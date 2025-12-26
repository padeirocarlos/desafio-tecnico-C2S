
import os
import time
import uuid
import logging
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from langchain.tools import tool
from data.dammy_db import DB_SCHEMA
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from .agents_client import model_client_name_dict
from mcp_server.mcp_server import MCPServer
from langgraph.checkpoint.memory import InMemorySaver
from agents.agent import ToolsToFinalOutputResult
from agents import Agent, Runner, ModelSettings, RunContextWrapper, FunctionToolResult
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from .entity import GeneralResult, SqlQueryPurifyResult, SqlQueryResult, SqlResult, SearchJudgeResult, FinalResult
from .instructions import synthesize_response, general_assist, sql_purify, judging_assist, sql_bug_fixer, sql_query_executer, sql_generater, general_assist_react

# Configure logger
logger = logging.getLogger("Vehicles-Agentic-Workflow")

load_dotenv(override=True)

class VehicleAgentic:
    
    def __init__(self, model_name: str="ollama3"):
        self.model_name = model_name
        self.mcp_server = None
    
    async def connect_to_mcp_servers(self):
        self.mcp_server = MCPServer()
        await self.mcp_server.connect()
        return self.mcp_server
 
    async def general_assist_agent(self, user_query:str, conversation_history:str, model_name:str) -> dict: 
        # STEP 1: User Interaction & Moderation Agent
        # 
        # This agent serves as the primary interface between the user and the system,
        # handling initial contact, conversation management, and content moderation.
        #
        # Agent Responsibilities:
        # - Greet users and establish conversational context
        # - Interpret user queries and requests in natural language
        # - Guide users through the vehicle search process with clarifying questions
        # - Maintain conversation flow and handle edge cases (unclear input, errors)
    
        content = """ You are a friendly vehicle search assistant. Your job is to produce a single, valid JSON object with the user's search parameters and your confidence. 
            Do not include ANY text before or after the JSON. No comments. No markdown. Only JSON.Use previous conversation history if available; if not, start fresh."""
                    
        messages = [{"role": "assistant", "content": f"{content}"}]
        instruction = general_assist(user_query = user_query, conversation_history=conversation_history)
        
        agent =  Agent(
                    name = "General-Car-Assistant-Agent",
                    instructions = instruction,
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    output_type=GeneralResult,)
        
        result = await Runner.run(agent, messages)
        
        final_result = { "answers": result.final_output.answers,
                        "original_query": user_query,
                        "confidence": result.final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
    
    async def judging_assist_agent(self, conversation:str, validation:bool, model_name:str) -> dict: 
            
        # STEP 2: Conversation Analysis Agent
        # 
        # This agent analyzes the dialogue between the user and AI Assistant to intelligently
        # extract and translate vehicle feature requests into SQL query parameters.
        #
        # Agent Responsibilities:
        # - Parse natural language requests for vehicle features (e.g., "red SUV with sunroof")
        # - Map user intent to database schema columns and values
        # - Filter and validate vehicle attributes before query construction
        # - Handle ambiguous requests by inferring the most likely database fields
        # 
        # Input: Conversation history (user messages + assistant responses)
        # Output: Structured filter parameters for SQL WHERE clauses
        #
        # Example transformation:
        #   User: "Show me affordable family cars with good safety ratings"
        #   Agent extracts: vehicle_type='sedan', price_range='<30000', safety_rating='>=4' 
    
        if validation:
            content = """ You are an expert at analyzing user responses """
        else:
            content = """You are act as expert to evaluate the provided conversation between a Vehicle search and seller assistant and an User."""
                    
        messages = [{"role": "assistant", "content": f"{content}"}]
        instruction = judging_assist(conversation = conversation, validation=validation)
        
        agent =  Agent(
                    name = "Judge-Assistant-Agent",
                    instructions = instruction,
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    output_type=SearchJudgeResult,)
        
        result = await Runner.run(agent, messages)
        
        final_result = { "decision": result.final_output.decision,
                        "summary": result.final_output.summary,
                        "validation_question": result.final_output.validation_question,
                        "issues_detected": result.final_output.issues_detected,
                        "confidence": result.final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        
        return final_result
    
    async def sql_generater_agent(self, user_query:str, model_name:str, error_message=None, error_fixer=False) -> dict:
        
        # STEP 3: SQL Query Generation Agent
        # 
        # This agent analyzes the conversation between the user and AI Assistant to construct
        # optimized SQL queries for retrieving vehicle data from the database.
        #
        # Agent Responsibilities:
        # - Transform filtered vehicle features into valid SQL query syntax
        # - Build dynamic WHERE clauses based on user-specified criteria
        # - Optimize query structure for performance (indexes, joins, query complexity)
        # - Sanitize inputs to prevent SQL injection attacks
        # - Handle complex queries with multiple filters (AND/OR conditions)
        # - Generate parameterized queries for database execution
        # 
        # Input: Structured filter parameters from STEP 2 (vehicle attributes, constraints)
        # Output: Executable SQL query string with safe parameter binding
        
        if error_fixer:
            instruction = sql_bug_fixer(sql_buggy_code = user_query, error_message=error_message,schema=DB_SCHEMA)
            content=" You are expert in fix errors in SQL Query. Given the schema, sql error and sql query, Fix the sql code error for SQLite."
        else:
            instruction = sql_generater(user_query = user_query, schema=DB_SCHEMA)
            content=" You are expert in generate SQL Query. Given the schema and the user's question, write a SQL query for SQLite."
        
        messages = [{"role": "assistant", "content": f"{content}"}]
        
        agent =  Agent(
                    name = "Sqlquery-Generater-Agent",
                    instructions = instruction,
                    # model = self.get_model(self.model_name) if model_name is None else self.get_model(model_name),
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    output_type=SqlQueryResult,)
        
        result = await Runner.run(agent, messages)
        
        final_result = { "comment": result.final_output.comment,
                        "sql_query": result.final_output.sql_query,
                        "confidence": result.final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
    
    async def sql_purify_agent(self, user_query:str, sql_query:str, model_name:str, error_fixer=False) -> dict:
        # STEP 4: SQL Query Optimization Agent
        # 
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
        # 
        # Input: Base SQL query from STEP 3 + conversation context + user preferences
        # Output: Optimized, user-focused SQL query ready for execution
        
        if not error_fixer:
            instruction = sql_purify(question = user_query, sql_query=sql_query, schema=DB_SCHEMA)
            content= """ You are expert in evaluate SQL Query. Evaluate whether the SQL result 
                        answers the user's question and, if necessary, propose a refined version of the query."""
        else:
            instruction = sql_bug_fixer(sql_buggy_code = sql_query, error_message=user_query, schema=DB_SCHEMA)
            content=" You are expert in fix errors in SQL Query. Given the schema, sql error and sql query, Fix the sql code error for SQLite."
        
        messages = [{"role": "assistant", "content": f"{content}"}]
        
        agent =  Agent(
                    name = "SqlQuery-Purify-Agent",
                    instructions = instruction,
                    # model = self.get_model(self.model_name) if model_name is None else self.get_model(model_name),
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    output_type=SqlQueryPurifyResult,)
        
        result = await Runner.run(agent, messages)
        
        final_result = { "feedback": result.final_output.feedback,
                        "sql_purify": result.final_output.sql_purify,
                        "confidence": result.final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
        
    
    async def sql_query_executer_agent(self, sql_query:str, model_name:str) -> dict:
        # STEP 5: SQL Query Execution Agent
        # 
        # This agent executes the optimized SQL query against the database and handles
        # all aspects of query execution, error management, and result retrieval.
        #
        # Agent Responsibilities:
        # - Establish secure database connection with proper credentials
        # - Execute parameterized SQL queries safely
        # - Handle database errors and connection failures gracefully
        # - Monitor query execution time and implement timeouts for long-running queries
        # - Retrieve and format raw result sets from the database
        # - Manage database transactions (commit/rollback) when necessary
        # 
        # Input: Optimized SQL query string + parameters from STEP 4
        # Output: Raw database results (list of vehicle records) or error information
    
        instruction = sql_query_executer(sql_query = sql_query)
        content=" You are expert in executing a SQL Query. Given tools from mcp_server to execute SQL query sucess full in SQLite."
        messages = [{"role": "assistant", "content": f"{content}"}]
        
        if self.mcp_server == None:
            await self.connect_to_mcp_servers()
        mcp_servers = self.mcp_server.mcp_servers["sql_server"]
        list_tools = await self.mcp_server.list_tools_openai()
        
        
        agent =  Agent(
                    name = "Sqlquery-Executer-Agent",
                    instructions = instruction,
                    mcp_servers = mcp_servers,
                    output_type = SqlResult,
                    # tools=list_tools,
                    # tool_use_behavior=self.tool_sql_result_handler,
                    # model_settings = ModelSettings(tool_choice="sql_query_execute"),
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    )
        
        result = await Runner.run(agent, messages)
        
        final_result = { 
                        "comment": result.final_output.comment,
                        # "comment": "",
                        "sql_result": result.final_output.sql_result,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
    
    
    async def synthesize_response_agent(self, responses:str, model_name:str) -> dict:
                
        # STEP 6: SQL Response Synthesis Agent
        # 
        # This agent transforms raw SQL query results into human-readable, contextual responses
        # tailored to the user's original question and conversation flow.
        #
        # Agent Responsibilities:
        # - Parse raw database results (rows, columns, data types)
        # - Analyze conversation context to understand user's intent and preferences
        # - Synthesize natural language summaries of query results
        # - Highlight key vehicle features that match user criteria
        # - Format data for optimal readability (tables, lists, cards)
        # - Handle edge cases (no results, too many results, partial matches)
        # - Add helpful suggestions based on results (alternative options, price ranges)
        # - Generate follow-up questions to refine search if needed
        
        content="You are a friendly and helpful vehicle search results Displayer assistant ."
        messages = [{"role": "assistant", "content": f"{content}"}]
        instruction = synthesize_response(sql_query_response=responses)
        
        agent =  Agent(
                    name = "Response-Synthesizer-Agent",
                    instructions = instruction,
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    # output_type = FinalResult,
                    )
        
        result = await Runner.run(agent, messages)
        
        final_result = { 
                        "final_response": result.final_output,
                        # "description": result.final_output.description,
                        # "confidence": result.final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        
        return final_result
    
    def tool_sql_result_handler(self,
        context: RunContextWrapper[Any],
        tool_results: List[FunctionToolResult]
        ) -> ToolsToFinalOutputResult:
        """Processes tool results to decide final output."""
        sql_result = []
        for result in tool_results:
            if result.output:
                sql_result.append(result.output)
            
        if sql_result:    
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=sql_result
            )
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output=f"""I did not find any vehicles that match your current criteria. 
                            Would you like me to adjust the search parameters 
                            or look for something different?"""
                            )
        
    def get_model(self, model_name: str) -> Agent:
        return model_client_name_dict.get(model_name, model_client_name_dict[self.model_name])





