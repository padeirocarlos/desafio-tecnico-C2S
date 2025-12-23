"""
Routing and edge logic for the deep research agent workflow.

This module contains the conditional routing functions that determine
the flow of execution through the agentic workflow graph.
"""
import logging
from typing import Literal, Dict, Any
from langgraph.types import interrupt, Command

MAX_QUALITY_TRY = 5
INTERACTION_NUMBER = 2

# Configure logger
logger = logging.getLogger("Vehicle-Agentic-Workflow (VAW)")

def route_after_vehicle_info_assist(state: Dict[str, Any]) -> Command[Literal["sql_generater", "END"]]:
    """
    Intelligent routing based on general user assist gatharing information and tools use
    """
    confidence = state.get("confidence", "Low")
    
    # Pause execution; payload shows up under result["__interrupt__"]
    is_approved = interrupt({
        "question": "Do you want to proceed with this action?",
        "details": state["action_details"]})

    # Route based on the response
    if is_approved:
        logger.info(f"🔄 ⚠️ Routing to General Assist node : {str(confidence).upper()}")
        return Command(goto="sql_generater")  # Runs after the resume payload is provided
    else:
        logger.info(f"🔀 ✅ Routing to SQL Generater node : {str(confidence).upper()}!")
        return Command(goto="general_assist")

def route_after_general_assist(state: Dict[str, Any]) -> Literal[ "judging_assist", "END"]:
    
    massage_origin = state.get("massage_origin")
    interaction_number = state.get("interaction_number")
    
    if int(interaction_number) == INTERACTION_NUMBER or str(massage_origin).lower() == str("judging_assist").lower():
        return "judging_assist"
    
    return "END"
    
def route_after_judging_assist(state: Dict[str, Any]) -> Literal["sql_generater", "general_assist", "END"]:
    """
    Intelligent routing based on general user assist results level of confidence
    """
    decision = state.get("decision","")
    summary = state.get("summary","")
    answers = state.get("answers:","")
    
    if str(decision).lower() == str("POS").lower():
        logger.info(f"🔀 ✅ Routing to SQL Query Generater node : \n 1. Summary: {summary} \n 2. Answers: {answers}!")
        return "sql_generater"
    
    if str(decision).lower() == str("NEG").lower():
        logger.info(f"🔀 ✅ Routing to General Assist node : \n 1. Summary: {summary} \n 2. Answers: {answers}")
        return "general_assist"
    
    return "END"

def route_after_sql_generater(state: Dict[str, Any]) -> Literal["sql_query_execute", "refletion"]:
    """
    Intelligent routing based on general user assist results level of confidence
    """
    sql_query = state.get("sql_query", "")
    confidence = state.get("confidence", "Low")
    sql_query_try_quality = state.get("sql_query_try_quality", 0)
    
    if str(confidence).lower() in ("low","medium") and sql_query_try_quality < MAX_QUALITY_TRY:
        return "refletion"
    else:
        logger.info(f"🔀 ✅ Routing to SQL Query Execute node :  \n SQL Query: {sql_query}  \n Level of confidence: '{str(confidence).upper()}'!")
        return "sql_query_execute"

def route_after_sql_purify(state: Dict[str, Any]) -> Literal["sql_query_execute", "refletion"]:
    """
    Intelligent routing based on general user assist results level of confidence
    """
    sql_purify = state.get("sql_purify", "")
    confidence = state.get("confidence", "Low")
    sql_purify_try_quality = state.get("sql_purify_try_quality", 0)
    
    if str(confidence).lower() in ("low","medium") and sql_purify_try_quality < MAX_QUALITY_TRY:
        return "refletion"
    else:
        logger.info(f"🔀 ✅ Routing to SQL Query Execute node :  \n SQL_query: {sql_purify}  \n Level of confidence: '{str(confidence).upper()}'!")
        return "sql_query_execute"

def route_after_refletion(state: Dict[str, Any]) -> Literal["general_assist", "sql_purify", "sql_generater"]:
    
    massage_origin = state.get("massage_origin", "UHMassage")
    
    if str(massage_origin).lower() == str("sql_purify_node").lower():
        return "sql_purify"
    
    elif str(massage_origin).lower() == str("sql_generater_node").lower():
        return "sql_generater"
    
    return "general_assist"
        


