
import os
import time
import uuid
import logging
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain.tools import tool
from agents import Agent, Runner
from data.dammy_db import DB_SCHEMA
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from .agents_client import model_client_name_dict
from mcp_server.mcp_server import Agentic_MCP_Server
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from .entity import GeneralResult, SqlQueryPurifyResult, SqlQueryResult, SqlResult, SearchJudgeResult, FinalResult
from .instructions import synthesize_response, general_assist, sql_purify, judging_assist, sql_bug_fixer, sql_query_executer, sql_generater, general_assist_react

# Configure logger
logger = logging.getLogger("Vehicles-Agentic-Workflow")

load_dotenv(override=True)

class VehicleAgentic:
    
    def __init__(self, model_name: str="ollama3"):
        self.model_name = model_name
        self.agentic_mcp_server = None
        
    async def connect_to_mcp_servers(self):
        self.agentic_mcp_server = Agentic_MCP_Server()
        await self.agentic_mcp_server.connect_to_servers()
        return self.agentic_mcp_server
    
    async def general_assist_react_agent(self, user_query:str, model_name:str) -> dict:
        
        content = """You are a friendly and helpful vehicle search assistant. Your role is to help users find vehicles in a database by 
                    having a natural, conversational interaction."""
                    
        instruction = general_assist_react(user_query = user_query)

        agent = create_react_agent(
            prompt=instruction,
            checkpointer=InMemorySaver(),
            model=ChatOllama(model=model_name),
            tools=[]
            )
        
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        result = agent.invoke({"messages": [HumanMessage(content=user_query)]}, config)
        final_output = result["messages"]
        
        final_result = { "answers": final_output.answers,
                        "original_query": user_query,
                        "confidence": final_output.confidence,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
    
    async def judging_assist_agent(self, conversation:str, validation:bool, model_name:str) -> dict: 
        
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
    
    async def general_assist_agent(self, user_query:str, conversation_history:str, model_name:str) -> dict: 
        
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
    
    async def synthesize_response_agent(self, responses:str, model_name:str) -> dict:
        
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
    
    async def sql_purify_agent(self, user_query:str, sql_query:str, model_name:str, error_fixer=False) -> dict:
        
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
    
    async def sql_generater_agent(self, user_query:str, model_name:str, error_message=None, error_fixer=False) -> dict:
        
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
    
    async def sql_query_executer_agent(self, sql_query:str, model_name:str) -> dict:
        
        instruction = sql_query_executer(sql_query = sql_query)
        content=" You are expert in executing a SQL Query. Given tools from mcp_server to execute SQL query sucess full in SQLite."
        messages = [{"role": "assistant", "content": f"{content}"}]
        
        if self.agentic_mcp_server == None:
            await self.connect_to_mcp_servers()
        mcp_servers = self.agentic_mcp_server.mcp_servers["sql_server"]
        
        agent =  Agent(
                    name = "Sqlquery-Executer-Agent",
                    instructions = instruction,
                    model = self.get_model(model_name) if model_name else self.get_model(self.model_name),
                    mcp_servers = mcp_servers,
                    output_type = SqlResult,)
        
        result = await Runner.run(agent, messages)
        
        final_result = { "comment": result.final_output.comment,
                        "sql_result": result.final_output.sql_result,
                        "content": f"{content}",
                        "role": "assistant",
                        }
        return final_result
    
    def get_model(self, model_name: str) -> Agent:
        return model_client_name_dict.get(model_name, model_client_name_dict[self.model_name])





