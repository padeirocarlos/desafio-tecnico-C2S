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

MAX_TRY_ERROR = 5
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
    interaction_number: int
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
    """
    # This NODE serves as the primary interface between the user and the system,
    # handling initial contact, conversation management, and content moderation.
    #
    # NODE Agent Responsibilities:
    # - Greet users and establish conversational context
    # - Interpret user queries and requests in natural language
    # - Guide users through the vehicle search process with clarifying questions
    # - Maintain conversation flow and handle edge cases (unclear input, errors)
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
    
    history = state.get("history", [])
    confidence = state.get("confidence", "LOW")
    conversation = "Conversation history:\n\n"
    original_query = state.get("original_query")
    massage_origin = state.get("massage_origin", "UHMassage")
    
    if not original_query:
        logger.error(f"❌ No user query provided '{original_query}' ")
    
    # Skyp user interaction and move to user validation flow in the 'judging_assist_node' the next one 
    elif str(massage_origin).lower() == str("judging_assist").lower():
        decision = state.get("decision", "REQ")
        summary = state.get("summary")
        validation_question = state.get("validation_question")
        
        logger.info(f""" 🔀 ✅  ======= General Assist NODE TO => Judging User validation response: \n 1. Summary: {summary} \n decision: {decision}
                    \n 2. Validation Question: {validation_question} \n 3. User response: {original_query} \n 4. massage_origin: {massage_origin} ======= """)
    
    # Proceed to normal workflow user intarection  
    elif original_query:
        start_time = time.perf_counter()
        
        if history:
            conversation = format_conversation(history)
        else:
            conversation = "NO conversation history"
        
        try:
            result = await vehicleAgentic.general_assist_agent(user_query=original_query, conversation_history=conversation, model_name="ollama3") 
                                                                                    #  qwen3 gemma3:1b ollama3 deepseek  deepseek-r1 gemini gpt-oss:20b
            answers = result.get("answers")
            confidence = result.get("confidence")
            
            refined_time = (time.perf_counter() - start_time) * 1000
            decision = state.get("decision", "REQ")
            logger.info(f""" ✅ General Assist node executed success full: \n HMessage: {original_query}  \n AIMessage: {answers}  \n decision: {decision}
                            \n Level of confidence: {str(confidence).upper()} \n massage_origin: {massage_origin} \n Completed in {float(refined_time):.2f} ms """)
            
            return {
                **state,
                "answers": answers,
                "history": history,
                "massage_origin": massage_origin,
                "confidence": confidence,
                "content": result["content"],
                "role": result["role"],
                }
        except Exception as e:
            logger.error(f"❌ General Assist node failed: {e}")
            return {**state, }

async def judging_assist_node(state: WorkflowState) -> WorkflowState:
    """
    # This NODE analyzes the dialogue between the user and AI Assistant to intelligently
    # extract and translate vehicle feature requests into SQL query parameters.
    #
    # NODE Agent Responsibilities:
    # - Parse natural language requests for vehicle features (e.g., "red SUV with sunroof")
    # - Map user intent to database schema columns and values
    # - Filter and validate vehicle attributes before query construction
    # - Handle ambiguous requests by inferring the most likely database fields
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
    
    cycle = state.get("cycle")
    decision = state.get("decision", "REQ")
    answers = state.get("answers", "")
    history = state.get("history", [])
    original_query = state.get("original_query")
    judging_assist = state.get("massage_origin")
    conversation = "Conversation history:\n\n"
    
    # Formating User and Assistant conversation keeping only 10 windows of conversations
    if history:
        length = int(cycle.get("length"))
        if length > 0:
            history_ = history[length:] if len(history) > length else []
            conversation = format_conversation(history_, answers)
            logger.info(f" 1. ✅ 📦 💾 Judge Assistant NODE Current History Memory \n 1. Conversation: {conversation} \n 2. history: - {history} \n 2. Length: Reg - {length} / His - {len(history)}   \n 3. cycle {cycle}  ")
        else:
            conversation = format_conversation(history, answers)
    else:
        conversation += f"user: {original_query}\n"
        conversation += f"assistant: {answers}\n"
    
    logger.info(f" 1.1 HISTORY: Judge Assistant NODE Current History Memory \n 1. Conversation: {conversation} \n 2. history: - {history} \n 2. Length: Reg - {length} / His - {len(history)}   \n 3. cycle {cycle}  ")
    
    try:
        start_time = time.perf_counter()
        
        # Change to user response validation prompt. It must be checked before Agent running
        validation = False
        if str(decision).lower() == str("PRO").lower():
            validation = True
            
        result = await vehicleAgentic.judging_assist_agent(conversation=conversation, validation=validation, model_name="ollama3") 
                                                                            # ollama3 gemma3:1b qwen3 olmo-3:7b deepseek-r1 deepseek gemini gpt-oss:20b
        summary = result.get("summary")
        decision = result.get("decision")
        confidence = result.get("confidence")
        issues_detected = result.get("issues_detected")
        validation_question = result.get("validation_question")
        
        # Proceed to SQL Query filter validation from user before generate CODE. Here 'PRO'=> PROCEED
        if str(decision).lower() == str("PRO").lower():
            judging_assist = "judging_assist"
            answers = f"{summary} \n {validation_question}"
        
        # Proceed to filter gathering from user vehicle filter not enough
        elif str(decision).lower() == str("REQ").lower():
            answers = f"{answers} \n {issues_detected} \n {validation_question}"
            judging_assist = "UHMassage"
        
        # Proceed to SQL Query generation 'POSITIVE' validation from user before generate. Here 'POS'=> POSITIVE
        if str(decision).lower() == str("POS").lower():
            summary = state.get("summary")
            judging_assist = "judging_assist"

        # Collect more information from user to create SQL Query. User final response was 'NEGATIVE'. Here 'NEG'=> NEGATIVE
        elif str(decision).lower() == str("NEG").lower():
            summary = ""
            validation_question = ""
            judging_assist = "UHMassage"
            
        refined_time = (time.perf_counter() - start_time) * 1000
        logger.info(f""" ✅ Judge Assist node executed:  \n 1. Decision: {decision}  \n 2. answers: {answers} \n 3. Summary: {summary} \n 4. validation_question: {validation_question}
                    \n 4. Issues detected: {issues_detected} \n 5. Level of confidence: {str(confidence).upper()}  \n Completed in {float(refined_time):.2f}ms """)
        
        return {
            **state,
            "cycle": cycle,
            "answers": answers,
            "summary": summary,
            "decision": decision,
            "massage_origin": judging_assist,
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
    """
    # This agent analyzes the generated SQL query and refines it based on user needs,
    # preferences, and query performance characteristics to deliver optimal results.
    #
    # Agent Responsibilities:
    # - Evaluate SQL query efficiency and suggest optimizations (indexes, joins)
    # - Adjust query scope based on implicit user preferences (e.g., prioritize recent models)
    # - Add intelligent sorting (ORDER BY) based on likely user intent
    # - Implement result limits and pagination for large datasets
    # - Enhance queries with additional relevant filters the user may have forgotten
    # - Apply business logic rules (e.g., exclude out-of-stock vehicles, prioritize featured listings)
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
    
    confidence = state.get("confidence", "Low")
    massage_origin = state.get("massage_origin", "UHMassage")
    
    if str(massage_origin).lower() == str("sql_generater_node").lower():
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
    """
    # This NODE analyzes the conversation between the user and AI Assistant to construct
    # optimized SQL queries for retrieving vehicle data from the database.
    #
    # NODE Agent Responsibilities:
    # - Transform filtered vehicle features into valid SQL query syntax
    # - Build dynamic WHERE clauses based on user-specified criteria
    # - Optimize query structure for performance (indexes, joins, query complexity)
    # - Sanitize inputs to prevent SQL injection attacks
    # - Handle complex queries with multiple filters (AND/OR conditions)
    # - Generate parameterized queries for database execution
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
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
                    result = await vehicleAgentic.sql_generater_agent(user_query=sql_query, error_message=sql_query_error,model_name="qwen2.5-coder", error_fixer=True) # qwen3-coder qwen2.5-coder olmo-3:7b
                else:
                    result = await vehicleAgentic.sql_generater_agent(user_query=summary, model_name="qwen2.5-coder")
                
                comment = result.get("comment", "")
                sql_query = result.get("sql_query", "")
                confidence = result.get("confidence", "Low")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f""" ✅ 🔍 SQL Query generator node executed success full. \n 1. Comment: {comment} \n 3. SQL_query: {sql_query} 
                            \n 4. Level of confidence: {str(confidence).upper()} \n 5. Completed in {float(refined_time):.2f}ms """)

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
    """
    # This NODE analyzes the generated SQL query and refines it based on user needs,
    # preferences, and query performance characteristics to deliver optimal results.
    #
    # NODE Agent Responsibilities:
    # - Evaluate SQL query efficiency and suggest optimizations (indexes, joins)
    # - Adjust query scope based on implicit user preferences (e.g., prioritize recent models)
    # - Add intelligent sorting (ORDER BY) based on likely user intent
    # - Implement result limits and pagination for large datasets
    # - Enhance queries with additional relevant filters the user may have forgotten
    # - Apply business logic rules (e.g., exclude out-of-stock vehicles, prioritize featured listings)
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
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
                    result = await vehicleAgentic.sql_purify_agent(user_query=sql_purify_error, sql_query=sql_query, model_name="qwen2.5-coder", error_fixer=True)
                else:
                    result = await vehicleAgentic.sql_purify_agent(user_query=filter_summary, sql_query=sql_query, model_name="qwen2.5-coder") 
                                                                            # gemini deepseek deepseek-r1 qwen3-coder qwen2.5-coder olmo-3:7b
            
                feedback = result.get("feedback", "")
                sql_purify = result.get("sql_purify", "")
                confidence = result.get("confidence", "Low")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f""" ✅ 🎯 SQL Query generator node executed success full. \n 1. Feedback: {feedback} \n 3. SQL_query: {sql_purify} 
                            \n 4. Level of confidence: {str(confidence).upper()} \n 5. Completed in {float(refined_time):.2f}ms """)
                
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
    """
    # This NODE executes the optimized SQL query against the database and handles
    # all aspects of query execution, error management, and result retrieval.
    #
    # NODE Agent Responsibilities:
    # - Establish secure database connection with proper credentials
    # - Execute parameterized SQL queries safely
    # - Handle database errors and connection failures gracefully
    # - Monitor query execution time and implement timeouts for long-running queries
    # - Retrieve and format raw result sets from the database
    # - Manage database transactions (commit/rollback) when necessary
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
    sql_query = state.get("sql_query", "")
    sql_purify = state.get("sql_purify", sql_query)

    if not sql_query:
        logger.error(f"❌ No SQL query provided")
    
    if not sql_purify:
        logger.error(f"❌ No SQL Purify Query provided")
        
    if sql_query or sql_purify:
        start_time = time.perf_counter()
        run_agent = True

        try:
            if not sql_purify and sql_query:
                sql_purify = sql_query
                
            try:
                if run_agent:
                    sql_result = sql_query_execute(sql_query=sql_query)
                    comment = "NO! Comment!"
                else:
                    result = await vehicleAgentic.sql_query_executer_agent(sql_query=sql_query, model_name="qwen3") 
                                                                            # functiongemma mistral gemma12B_v ollama3 gemini gpt-oss:20b deepseek deepseek-r1 qwen3-coder qwen2.5-coder olmo-3:7b
                    comment = result.get("summary")
                    sql_result = result.get("sql_result")
                
                refined_time = (time.perf_counter() - start_time) * 1000
                logger.info(f" ✅ 🎯 SQL Query executer node success full. \n SQL Result: {sql_result} \n comment: {comment} \n Completed in : {float(refined_time):.2f}ms")
                
                state["massage_origin"] = "AI_SQL_query_execute"
                return { **state, "sql_result": sql_result, "comment": comment,}
            
            except Exception as e:
                logger.error(f"❌ SQL Query executer Agent failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ SQL Query execution node failed: {e}")
            return { **state, }
        
        state["massage_origin"] = "sql_query_execute_node"

async def synthesize_response_node(state: WorkflowState) -> WorkflowState:
    """
    # This NODE transforms raw SQL query results into human-readable, contextual responses
    # tailored to the user's original question and conversation flow.
    #
    # NODE Agent Responsibilities:
    # - Parse raw database results (rows, columns, data types)
    # - Analyze conversation context to understand user's intent and preferences
    # - Synthesize natural language summaries of query results
    # - Highlight key vehicle features that match user criteria
    # - Format data for optimal readability (tables, lists, cards)
    # - Handle edge cases (no results, too many results, partial matches)
    # - Add helpful suggestions based on results (alternative options, price ranges)
    # - Generate follow-up questions to refine search if needed
    
    :param state: Description
    :type state: WorkflowState
    :return: Description
    :rtype: WorkflowState
    """
    start_time = time.perf_counter()
    
    cycle = state.get("cycle")
    answers = state.get("answers", "")
    history = state.get("history", [])
    
    sql_result = state.get("sql_result", answers)

    logger.info(f"🔗 Processing final response ...")
    
    try:
        result = await vehicleAgentic.synthesize_response_agent(responses=sql_result, model_name="deepseek-r1") 
                                    # ollama3 olmo-3:7b gemma3:1b qwen3-coder gemini deepseek qwen3 deepseek-r1 deepseek gemini gpt-oss:20b
        final_response = result["final_response"]
        
        if final_response:
            length = len(history) + 1
            cycle_count = int(cycle.get("cycle")) + 1
            cycle = {"cycle":cycle_count, "length":length}
            state["cycle"] = cycle
            
        response = f" \n {final_response} \n "
        refined_time = (time.perf_counter() - start_time) * 1000
        logger.info(f" ✅ 🔗 📝 Final response: \n 1. {response} \n 3. Completed in {float(refined_time):.2f}ms ")
        
        return {
            **state,
            "answers": response,
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