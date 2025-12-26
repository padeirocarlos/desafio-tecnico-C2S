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

logger = logging.getLogger("Vehicle-Agentic-Workflow (VAW)")

def route_after_general_assist(state: Dict[str, Any]) -> Literal[ "judging_assist", "END"]:
    """
     AGENT: Post-General Assistance Router (edges after_general_assist)
        This routing agent determines the next workflow step after the general assistance
        agent handles user interaction, directing the flow based on user intent classification
        and conversation state.
    
    :param state: Description
    :type state: Dict[str, Any]
    :rtype: Literal['judging_assist', 'END']
    """
    
    massage_origin = state.get("massage_origin")
    interaction_number = state.get("interaction_number")
    
    if int(interaction_number) == INTERACTION_NUMBER or str(massage_origin).lower() == str("judging_assist").lower():
        return "judging_assist"
    
    return "END"
    
def route_after_judging_assist(state: Dict[str, Any]) -> Literal["sql_generater", "general_assist", "END"]:
    """
     AGENT: Post-Judgment Router (edges after_judging_assist)
        This routing agent evaluates the assistant's judgment/decision and determines
        the appropriate next step in the workflow based on the quality, completeness,
        and confidence of the judgment made.
    
    :param state: Description
    :type state: Dict[str, Any]
    :rtype: Literal['sql_generater', 'general_assist', 'END']
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
        This routing agent determines the next workflow step after SQL query generation,
        directing the process flow based on query characteristics, validation results,
        and system state.
    
    :param state: Description
    :type state: Dict[str, Any]
    :rtype: Literal['sql_query_execute', 'refletion']
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
        AGENT: Post-SQL Purification Router (edges after_sql_purify)
        This routing agent evaluates the purified/sanitized SQL query and determines
        the next workflow step based on security validation, query safety assessment,
        and purification results.
    
    :param state: Description
    :type state: Dict[str, Any]
    :rtype: Literal['sql_query_execute', 'refletion']
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
    """
    AGENT: Post-Reflection Router (edges after_reflection)
    This routing agent evaluates the reflection/self-assessment results and determines
    the next workflow step based on quality checks, performance evaluation, and
    identified improvement opportunities.
    
    :param state: Description
    :type state: Dict[str, Any]
    :rtype: Literal['general_assist', 'sql_purify', 'sql_generater']
    """
    
    massage_origin = state.get("massage_origin", "UHMassage")
    
    if str(massage_origin).lower() == str("sql_purify_node").lower():
        return "sql_purify"
    
    elif str(massage_origin).lower() == str("sql_generater_node").lower():
        return "sql_generater"
    
    return "general_assist"
        


