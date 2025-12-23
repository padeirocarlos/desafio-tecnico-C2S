import os
import time
import uuid
import logging
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

from agentic.nodes import (
    initialize_agent,
)

from agentic.edges import (
    route_after_sql_purify,
    route_after_sql_generater,
    route_after_judge_assist,
    route_after_refletion,
)

from agentic.nodes import (
    WorkflowState,
    general_assist_node,
    search_judge_assist_node,
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
    workflow.add_node("search_judge_assist", search_judge_assist_node)
    workflow.add_node("refletion", refletion_node)
    workflow.add_node("sql_generater", sql_generater_node)
    workflow.add_node("sql_purify", sql_purify_node)
    workflow.add_node("sql_query_execute", sql_query_execute_node)
    workflow.add_node("synthesize_response", synthesize_response_node)

    # set entry point to decomposition node
    workflow.set_entry_point("general_assist")
    workflow.add_edge("general_assist", "search_judge_assist")
    
    # Add edges
    workflow.add_conditional_edges(
        "search_judge_assist",
        route_after_judge_assist,
        {
            "sql_generater": "sql_generater", 
            "general_assist": "general_assist",
            "END": END,
        },
    )
    
    # Add edges
    workflow.add_conditional_edges(
        "refletion",
        route_after_refletion,
        {
            "general_assist": "general_assist", 
            "sql_purify": "sql_purify",
            "sql_generater": "sql_generater",
        },
    )

    workflow.add_conditional_edges(
        "sql_purify",
        route_after_sql_purify,
        {
            "refletion": "refletion",
            "sql_query_execute": "sql_query_execute",
        },
    )
      
    workflow.add_edge("sql_query_execute", "synthesize_response")
    
    workflow.add_conditional_edges(
        "sql_generater",
        route_after_sql_generater,
        {
            "sql_query_execute": "sql_query_execute",
            "refletion": "refletion",
        },
    )
    
    workflow.add_edge("synthesize_response", END)
    
    graph = workflow.compile(checkpointer=sql_memory)
    
    return graph

class VehicleChat:
    def __init__(self):
        self.graph = None
        self.cycle = {"cycle":0, "length":0}
        self.search_summary = None
        self.vehiclechat_id = str(uuid.uuid4())
        self.memory = InMemorySaver()

    async def setup(self):
        await self.build_graph()
    
    async def build_graph(self):
        # Set up Graph Builder with State
        self.graph = await workflow_app(self.memory)
    
    async def run_superstep(self, message, history):
        config = {"configurable": {"thread_id": self.vehiclechat_id}}
        
        state = WorkflowState()
        state["massage_origin"] = "UHMassage"
        
        history_ = history
        if isinstance(history,list) and len(history) > 0:
            if len(history) > 12:
                history_ = history[-12:]
 
        state["cycle"] = self.cycle
        state["original_query"] = message
        user = {"role": "user", "content": message}
        
        if self.search_summary:
            state["summary"] = self.search_summary["summary"]
            state["validation_question"] = self.search_summary["sumary_question"]
            state["massage_origin"] = "search_judge_assist"
            self.search_summary = None
        
        if not history_:
            state["history"] = [user]
        else:
            state["history"] = history_ + [user]
        
        result = await self.graph.ainvoke(state, config=config)
        
        self.cycle = result["cycle"]
        
        massage_origin = result.get("massage_origin")
        if str(massage_origin).lower() == str("search_judge_assist").lower():
            self.search_summary = {"summary":result["summary"], "sumary_question": result["answers"]}
        else:
            self.search_summary = None
            
        reply = {"role": "assistant", "content": str(result["answers"])}
        
        if not history_:
            return [user, reply]
        
        return history_ + [user, reply]
    
async def cleanup():
    new_vehicleChat = VehicleChat()
    await new_vehicleChat.setup()
    return None, new_vehicleChat

async def process_message(vehicleChat, message, history):
    results = await vehicleChat.run_superstep(message, history)
    return results, vehicleChat