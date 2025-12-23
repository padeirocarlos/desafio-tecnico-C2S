import os
import time
import uuid
import logging
from agentic.edges import INTERACTION_NUMBER
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

from agentic.edges import (
    route_after_sql_purify,
    route_after_sql_generater,
    route_after_judging_assist,
    route_after_general_assist,
    route_after_refletion,
)

from agentic.nodes import (
    WorkflowState,
    initialize_agent,
    general_assist_node,
    judging_assist_node,
    refletion_node,
    sql_generater_node,
    sql_purify_node,
    sql_query_execute_node,
    synthesize_response_node,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo")

async def workflow_app(sql_memory = InMemorySaver()) -> StateGraph:
    
    sql_memory = sql_memory
    
    initialize_agent()

    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("general_assist", general_assist_node)
    workflow.add_node("judging_assist", judging_assist_node)
    workflow.add_node("sql_generater", sql_generater_node)
    workflow.add_node("refletion", refletion_node)
    workflow.add_node("sql_purify", sql_purify_node)
    workflow.add_node("sql_query_execute", sql_query_execute_node)
    workflow.add_node("synthesize_response", synthesize_response_node)

    # set entry point to decomposition node
    workflow.set_entry_point("general_assist")
    
    # Add edges general_assist
    workflow.add_conditional_edges(
        "general_assist",
        route_after_general_assist,
        {
            "judging_assist": "judging_assist",
            "END": END,
        },
    )
    
    # Add edges judging_assist
    workflow.add_conditional_edges(
        "judging_assist",
        route_after_judging_assist,
        {
            "sql_generater": "sql_generater", 
            "general_assist": "general_assist",
            "END": END,
        },
    )

    # Add edges sql_generater
    workflow.add_conditional_edges(
        "sql_generater",
        route_after_sql_generater,
        {
            "sql_query_execute": "sql_query_execute",
            "refletion": "refletion",
        },
    )
    
    # Add edges refletion
    workflow.add_conditional_edges(
        "refletion",
        route_after_refletion,
        {
            "sql_purify": "sql_purify",
            "general_assist": "general_assist", 
            "sql_generater": "sql_generater",
        },
    )
    
    # Add edges sql_purify
    workflow.add_conditional_edges(
        "sql_purify",
        route_after_sql_purify,
        {
            "refletion": "refletion",
            "sql_query_execute": "sql_query_execute",
        },
    )
    
    workflow.add_edge("sql_query_execute", "synthesize_response")
    
    workflow.add_edge("synthesize_response", END)
    
    graph = workflow.compile(checkpointer=sql_memory)
    
    return graph

class VehicleChat:
    def __init__(self):
        self.graph = None
        self.search_summary = None
        self.interaction_number = 0
        self.memory = InMemorySaver()
        self.cycle = {"cycle":0, "length":0}
        self.vehiclechat_id = str(uuid.uuid4())

    async def setup(self):
        await self.build_graph()
    
    async def build_graph(self):
        # Set up Graph Builder with State
        self.graph = await workflow_app(self.memory)
    
    async def run_superstep(self, message, history):
        config = {"configurable": {"thread_id": self.vehiclechat_id}}
        
        state = WorkflowState()
        state["massage_origin"] = "UHMassage"
        
        # This for TOKEN control avoiding COST for LLM Agent bill 
        history_ = history
        if isinstance(history,list) and len(history) > 0:
            if len(history) > 10:
                history_ = history[-10:]
 
        state["cycle"] = self.cycle
        state["original_query"] = message
        user = {"role": "user", "content": message}
        state["interaction_number"] = self.interaction_number
        
        # This workflow for user intarection and validation. Coming from Judging NODE, Keep it for next interaction
        if self.search_summary:
            state["summary"] = self.search_summary["summary"]
            state["decision"] = self.search_summary["decision"]
            state["massage_origin"] = self.search_summary["massage_origin"]
            state["validation_question"] = self.search_summary["sumary_question"]
            self.search_summary = None
        
        # This for ChatBox visualization control messaging flow with Assistant and USER for LLM Agent use 
        if not history_:
            state["history"] = [user]
        else:
            state["history"] = history_ + [user]
        
        result = await self.graph.ainvoke(state, config=config)
        
        self.cycle = result["cycle"]
        
        # Save in flight (Memory) critical information for next submitions 
        massage_origin = result.get("massage_origin")
        if str(massage_origin).lower() == str("judging_assist").lower():
            self.search_summary = {"summary":result["summary"], "sumary_question": result["answers"], "massage_origin": result.get("massage_origin"), "decision": result.get("decision")}
        else:
            self.search_summary = None
        
        # Save in flight (Memory) critical information for next submittions analysis
        if self.interaction_number == INTERACTION_NUMBER:
            self.interaction_number = 0
            
        self.interaction_number += 1
        
        reply = {"role": "assistant", "content": str(result["answers"])}
        
        if not history_:
            return [user, reply]
        
        return history_ + [user, reply]

async def process_message(vehicleChat, message, history):
    
    if not message or message.strip() == "":
        return "#### ⚠️ Please enter some Query to Vehicle Seller Assistant (VSA) AI first!", history, vehicleChat, None
    results = await vehicleChat.run_superstep(message, history)
    return "#### ℹ️ Your query and click Go!", results, vehicleChat, None