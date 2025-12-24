"""
Workflow nodes for the deep research vehicles agent.

This module contains all the node functions that implement the core
logic of the agentic vehicles workflow.
"""
import os
import time
import logging
import sqlite3
import pandas as pd
from .agent import VehicleAgentic
from data.dammy_db import initialize_cars_db
from langgraph.graph.message import add_messages
from typing import Annotated, List, Dict, Any, Optional, TypedDict

MAX_TRY_ERROR = 10
# Configure logger
logger = logging.getLogger("Vehicle-Agentic-Workflow (VAW)")

global vehicleAgentic
vehicleAgentic = VehicleAgentic()

class WorkflowMetrics(TypedDict):
    """
    Consolidated metrics for car workflow performance tracking.
    Groups related metrics for cleaner organization and easier analysis.
    """
    # Performance timing (all in milliseconds)
    total_latency: float
    user_feedback_latency: float
    car_search_latency: float
    synthesis_latency: float
    sql_purify_error: int
    sql_query_error: int
    
    # LLM car usage for cost tracking
    llm_calls: Dict[str, int]


class WorkflowState(TypedDict):
    """
    State for car agentic workflow and quality evaluation.
    Tracks query processing, research iterations, and performance metrics.
    """
    cycle: dict
    comment: str
    decision: str
    summary: str
    history: list
    answers: str
    feedback: str
    sql_query: str
    sql_result: str
    confidence: str
    sql_purify: str
    massage_origin: str
    original_query: str
    issues_detected: str
    sql_query_error: int
    sql_purify_error: int
    validation_question:str
    sql_query_try_quality: int
    sql_purify_try_quality: int
    final_response: Optional[str]
    
# Initialize functions for easy setup
def initialize_agent():
    """
    Initialize all agent components with required dependencies.
    """
    # initialize_db()
    initialize_metrics()
    
def initialize_metrics() -> WorkflowMetrics:
    """
    Initialize a clean metrics structure with default values.
    """
    return {
        "cycle": {"cycle":0, "length":0},
        "total_latency": 0.0,
        "user_feedback_latency": 0.0,
        "search_latency": 0.0,
        "synthesis_latency": 0.0,
        "sql_purify_error": 0,
        "sql_query_error": 0,
    }

def initialize_db():
    """ Initialize the car database."""
    initialize_cars_db()

def format_conversation( messages: List[Any], current_answer:str = "") -> str: 
    conversation = "Conversation history:\n\n"
    for message in messages:
        if isinstance(message, dict):
            conversation += f"{message.get("role")}: {message.get("content")}\n"
    
    if current_answer:
        conversation += f"assistant: {current_answer}\n"
    return conversation
    
async def general_assist_node(state: WorkflowState) -> WorkflowState:
    
    cycle = state.get("cycle")
    history = state.get("history", [])
    confidence = state.get("confidence", "LOW")
    conversation = "Conversation history:\n\n"
    original_query = state.get("original_query")
    issues_detected = state.get("issues_detected", "")
    massage_origin = state.get("massage_origin", "UHMassage")
    
    if not original_query:
        logger.error(f"❌ No user query provided '{original_query}' ")
    
    elif str(massage_origin).lower() == str("search_judge_assist").lower():
        summary = state.get("summary")
        validation_question = state.get("validation_question")
        logger.info(f" 🔀 ✅  ======= General Assist Node ======= ")
        logger.info(f" 🔀 ✅  ======= User validation response: \n 1. Summary: {summary} \n 2. Validation Question: {validation_question} \n 3. User response: {original_query} ======= ")
        
    elif original_query:
        start_time = time.perf_counter()
        
        if history:
            length = int(cycle.get("length"))
            if length > 0:
                history_ = history[length:]
                conversation = format_conversation(history_)
            else:
                conversation = format_conversation(history)
        else:
            conversation = "NO conversation history"
        
        if str(massage_origin).lower() == str("AI_Judge_assist").lower() and False:
            original_query = issues_detected
        
        try:
            result = await vehicleAgentic.general_assist_agent(user_query=original_query, conversation_history=conversation, model_name="ollama3") #  qwen3 ollama3 deepseek gemini gpt-oss:20b
            
            answers = result.get("answers")
            confidence = result.get("confidence")
            
            refined_time = (time.perf_counter() - start_time) * 1000
            logger.info(f" ✅ General Assist node executed success full: \n HMessage: {original_query}  \n AIMessage: {answers}  \n Level of confidence: {str(confidence).upper()}  \n Completed in {float(refined_time):.2f}ms")
            
            return {
                **state,
                "answers": answers,
                "history": history,
                "confidence": confidence,
                "content": result["content"],
                "role": result["role"],
                }
        except Exception as e:
            logger.error(f"❌ General Assist node failed: {e}")
            return {**state, }

async def search_judge_assist_node(state: WorkflowState) -> WorkflowState:
    
    cycle = state.get("cycle")
    answers = state.get("answers", "")
    history = state.get("history", [])
    original_query = state.get("original_query")
    search_judge_assist = state.get("massage_origin")
    conversation = "Conversation history:\n\n"
    
    if history:
        length = int(cycle.get("length"))
        if length > 0:
            history_ = history[length:] if len(history) > length else []
            conversation = format_conversation(history_, answers)
            logger.info(f" 1. ✅ ====== Judge Assistant NODE  \n 1. Conversation: {conversation} \n 2. history: - {history} \n 2. Length: Reg - {length} / His - {len(history)}   \n 3. cycle {cycle} ====== ")
        else:
            conversation = format_conversation(history, answers)
    else:
        conversation += f"user: {original_query}\n"
        conversation += f"assistant: {answers}\n"
    logger.info(f" 1.1 ✅ ======  \n 1. history: - {history} \n 2. Length: - {len(history)}   \n 3.  cycle_length: {int(cycle.get("length"))} ====== ")
    
    try:
        start_time = time.perf_counter()
        
        validation = False
        if str(search_judge_assist).lower() == str("search_judge_assist").lower():
            validation = True
            
        result = await vehicleAgentic.search_judge_assist_agent(conversation=conversation, validation=validation, model_name="ollama3") # ollama3 qwen3 olmo-3:7b deepseek gemini gpt-oss:20b
        
        summary = result.get("summary")
        decision = result.get("decision")
        issues_detected = result.get("issues_detected")
        validation_question = result.get("validation_question")
        confidence = result.get("confidence", "Low")
        
        if str(decision).lower() == str("PRO").lower():
            state["cycle"] = cycle
            length = len(history) + 1
            cycle_count = int(cycle.get("cycle")) + 1
            answers = f"{summary} \n {validation_question}"
            cycle = {"cycle":cycle_count, "length":length}
            search_judge_assist = "search_judge_assist"
            
        elif str(decision).lower() == str("POS").lower():
            summary = state.get("summary")
        else:
            summary = None
            validation_question = None
            state["cycle"] = cycle
            length = len(history) + 1
            search_judge_assist = "UHMassage"
            cycle_count = int(cycle.get("cycle")) + 1
            cycle = {"cycle":cycle_count, "length":length}
            
        if not decision:
            decision = "REQ"
        
        refined_time = (time.perf_counter() - start_time) * 1000
        logger.info(f" ✅ Judge Assist node executed:  \n 1. Decision: {decision}  \n 2. answers: {answers} \n 3. Summary: {summary} \n 4. Issues detected: {issues_detected} \n 5. Level of confidence: {str(confidence).upper()}  \n Completed in {float(refined_time):.2f}ms")
        
        return {
            **state,
            "cycle": cycle,
            "answers": answers,
            "decision": decision,
            "summary": summary,
            "massage_origin": search_judge_assist,
            "issues_detected": issues_detected,
            "validation_question": validation_question,
            "confidence": confidence,
            "content": result["content"],
            "role": result["role"],
            }
    except Exception as e:
        logger.error(f"❌ Judge Assist node failed: {e}")
        return {**state, }

async def refletion_node(state: WorkflowState) -> WorkflowState:
    
    history = state.get("history", [])
    decision = state.get("decision", "")
    confidence = state.get("confidence", "Low")
    issues_detected = state.get("issues_detected", "")
    massage_origin = state.get("massage_origin", "UHMassage")
    
    logger.info(f" ✅ Submitting Judge Question node executed !")
    
    if str(decision).lower() == ("REQ").lower() and str(massage_origin).lower() == str("UHMassage").lower():
        logger.info(f"🔄 ⚠️ Routing to General Assist node : \n 1. Decision: {decision} \n 2. Issues Detected: {issues_detected} \n history : {len(history)}  \n origin : {massage_origin}")
        return {**state, "massage_origin": "AI_Judge_assist",}
    
    elif str(massage_origin).lower() == str("sql_generater_node").lower():
        sql_query = state.get("sql_query", "")
        sql_query_try_quality = state.get("sql_query_try_quality", 0)
        
        logger.info(f"🔀 ⚠️ Routing to SQL Generator node :  \n SQL Query: {sql_query}  \n Level of confidence: '{str(confidence).upper()}'")
        
        return {**state, "sql_query_try_quality": sql_query_try_quality + 1,}
    
    elif str(massage_origin).lower() == str("sql_purify_node").lower():
        sql_purify = state.get("sql_purify", "")
        sql_purify_try_quality = state.get("sql_purify_try_quality", 0)
    
        logger.info(f"🔀 ⚠️ Routing to SQL Purify node :  \n SQL Query: {sql_purify}  \n Level of confidence: '{str(confidence).upper()}'")
        
        return {**state, "sql_purify_try_quality": sql_purify_try_quality + 1,}
    
    
async def sql_generater_node(state: WorkflowState) -> WorkflowState:
    
    answers = state.get("answers", "")
    summary = state.get("summary", answers)
    sql_query_error = None
    sql_error_count = 0
    recheck_code = True
    
    if not summary:
        logger.error(f"❌ No informaion to query provided")
    else:
        start_time = time.perf_counter()
        
        try:
            while recheck_code and sql_error_count < MAX_TRY_ERROR:
                
                if sql_query_error:
                    result = await vehicleAgentic.sql_generater_agent(user_query=sql_query, error_message=sql_query_error,model_name="olmo-3:7b", error_fixer=True) # qwen3-coder qwen2.5-coder olmo-3:7b
                else:
                    result = await vehicleAgentic.sql_generater_agent(user_query=summary, model_name="qwen2.5-coder")
                
                comment = result.get("comment", "")
                sql_query = result.get("sql_query", "")
                confidence = result.get("confidence", "Low")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f" ✅ 🔍 SQL Query generator node executed success full. \n 1. Comment: {comment} \n 3. SQL_query: {sql_query} \n 4. Level of confidence: {str(confidence).upper()} \n 5. Completed in {float(refined_time):.2f}ms ")

                try:
                    sql_query_execute(sql_query=sql_query)
                    refined_time = (time.perf_counter() - start_time) * 1000
                    logger.info(f" ✅ 🔍 Generator SQL Testing query passed!. Completed in : {float(refined_time):.2f}ms")
                    recheck_code = False
                    sql_query_error = None
                except Exception as e:
                    sql_query_error = e
                    sql_error_count = sql_error_count + 1
        
            return {
                **state,
                "comment": comment,
                "sql_query": sql_query,
                "confidence": confidence,
                "massage_origin": "sql_generater_node",
                "sql_error_count":sql_error_count,
                "content": result["content"],
                "role": result["role"],
                }
        
        except Exception as e:
            logger.error(f"❌ SQL Query Generator node failed: {e}")
            return {**state, }
        
    state["massage_origin"] = "sql_generater_node"
    
async def sql_purify_node(state: WorkflowState) -> WorkflowState:
    
    sql_query = state.get("sql_query", "")
    filter_summary = state.get("summary", "")
    comment = state.get("comment", "")
    sql_purify_error = None
    sql_error_count = 0
    recheck_code = True

    if not sql_query:
        logger.error(f"❌ SQL refining skyped no SQL provided")
    
    if not filter_summary:
        logger.error(f"❌ SQL Query refining skyped no user information to query provided")
        
    if sql_query and filter_summary:
        start_time = time.perf_counter()

        try:
            while recheck_code and sql_error_count < MAX_TRY_ERROR:
                
                if sql_purify_error:
                    result = await vehicleAgentic.sql_purify_agent(user_query=sql_purify_error, sql_query=sql_query, model_name="qwen3-coder", error_fixer=True)
                else:
                    result = await vehicleAgentic.sql_purify_agent(user_query=filter_summary, sql_query=sql_query, model_name="qwen3-coder") # gemini deepseek qwen3-coder qwen2.5-coder olmo-3:7b
            
                feedback = result.get("feedback", "")
                sql_purify = result.get("sql_purify", "")
                confidence = result.get("confidence", "Low")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f" ✅ 🎯 SQL Query generator node executed success full. \n 1. Feedback: {feedback} \n 3. SQL_query: {sql_purify} \n 4. Level of confidence: {str(confidence).upper()} \n 5. Completed in {float(refined_time):.2f}ms ")
                
                try:
                    sql_query_execute(sql_query=sql_query)
                    refined_time = (time.perf_counter() - start_time) * 1000
                    logger.info(f" ✅ 🔍 Purify SQL Testing query passed!. Completed in : {float(refined_time):.2f}ms")
                    recheck_code = False
                    sql_purify_error = None
                except Exception as e:
                    sql_purify_error = e
                    sql_error_count = sql_error_count + 1
                    
            return {
                **state,
                "feedback": feedback,
                "sql_purify": sql_purify,
                "confidence": confidence,
                "massage_origin": "sql_purify_node",
                "sql_error_count":sql_error_count,
                "content": result["content"],
                "role": result["role"],
                }
        
        except Exception as e:
            logger.error(f"❌ SQL Query refine node failed: {e}")
            return {**state, }
    
    state["massage_origin"] = "sql_purify_node"

async def sql_query_execute_node(state: WorkflowState) -> WorkflowState:
    
    sql_query = state.get("sql_query", "")
    sql_purify = state.get("sql_purify", sql_query)

    if not sql_query:
        logger.error(f"❌ No SQL query provided")
    
    if not sql_purify:
        logger.error(f"❌ No SQL Purify Query provided")
        
    if sql_query or sql_purify:
        start_time = time.perf_counter()

        try:
            if not sql_purify and sql_query:
                sql_purify = sql_query
            
            try:
                # result = await vehicleAgentic.sql_query_executer_agent(sql_query=sql_query, model_name="ollama3") # qwen3-coder gemini deepseek
                # comment = result.get("comment", "")
                # sql_result = result.get("sql_result", "")
                
                sql_result = sql_query_execute(sql_query=sql_query)
                comment = state.get("summary", "")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f" ✅ 🎯 SQL Query executer node success full. \n SQL Result: {sql_result} \n comment: {comment} \n Completed in : {float(refined_time):.2f}ms")
                
                state["massage_origin"] = "AI_SQL_query_execute"
                return { **state, "sql_result": sql_result, "comment": comment,}
            
            except Exception as e:
                logger.error(f"❌ SQL Query executer Agent failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ SQL Query execution node failed: {e}")
            return { **state, }

async def synthesize_response_node(state: WorkflowState) -> WorkflowState:
    """
    Synthesize cars answers into a coherent, comprehensive response.
    """
    start_time = time.perf_counter()
    
    answers = state.get("answers", "")
    sql_result = state.get("sql_result", answers)

    logger.info(f"🔗 Processing final response ...")
    
    try:
        result = await vehicleAgentic.synthesize_response_agent(responses=sql_result, model_name="ollama3") 
                                    # ollama3 olmo-3:7b qwen3-coder gemini deepseek qwen3 deepseek gemini gpt-oss:20b
        confidence = result["confidence"]
        description = result["description"]
        
        final_response = result["final_response"]
        response = f"{description} \n {final_response}"
        refined_time = (time.perf_counter() - start_time) * 1000
        logger.info(f" ✅ 🔗 📝 Final response: \n 1. {response} \n 2. Level of confidence: {str(confidence).upper()} \n 3. Completed in {float(refined_time):.2f}ms ")
        
        return {
            **state,
            "answers": response,
            "confidence": confidence,
            "content": result["content"],
            "role": result["role"],
            }
    except Exception as e:
        logger.error(f"❌ ⚠️ Final response node failed: {e}")
        return {**state, 
                "final_response": "I apologize, but I encountered an error while preparing your response. Please try again or contact support.",}

def sql_query_execute(sql_query: str) -> List[Dict]:
    if sql_query:
        sql_purify = sql_query
    try:
        conn = sqlite3.connect("mcp_server/cars.db")
        q = sql_purify.strip().removeprefix("```sql").removesuffix("```").strip()
        result = pd.read_sql_query(q, conn)
        result = result.to_dict(orient="records")
        return result
    except Exception as e:
        raise e
    finally:
        conn.close()