import os
import json
import logging
from dotenv import load_dotenv
from agents import FunctionTool
from agents.mcp import MCPServerStdio
from contextlib import AsyncExitStack
from typing import List, Dict, TypedDict
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

load_dotenv(override=True)

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

logger = logging.getLogger("MCP-Server (MCP)")
class MCPServer:
    """
    # 1. Load MCP server configuration (host, port, credentials)
    # 2. Instantiate MCP server with security settings
    # 3. Create client connection pool for agent communication
    # 4. Register all agents as MCP endpoints
    """
    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = [] # new
        self.exit_stack = AsyncExitStack() # new
        
        self.list_tools: List[ToolDefinition] = [] # new
        self.tools_session: Dict[str, ClientSession] = {} # new
        
        # for mcp_server for OpenAI support
        self.mcp_servers: Dict[str, list[MCPServerStdio]] = {} # new
        
        self.list_resource: List[ToolDefinition] = [] # new
        self.resources_session: Dict[str, ClientSession] = {} # new
        
    async def _connect(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            
            read, write = stdio_transport
            client_session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            # Instead of using MCP tools directly we should give mcp_server function definitions for OpenAI support
            self.mcp_servers[server_name] = [await self.exit_stack.enter_async_context(MCPServerStdio(server_config, client_session_timeout_seconds=360))]
            
            await client_session.initialize()
            self.sessions.append(client_session)
            
            response = await client_session.list_tools()
            tools = response.tools
            logger.info(f" ✅ 🎯 \nConnected to {server_name} with tools:, {[t.name for t in tools]}! 🚀 ")
            
            for tool in tools:
                self.tools_session[tool.name]=client_session
                self.list_tools.append(tool)
            
        except Exception as e:
            print(f"Failed to connect to server {server_name}: {e}")
    
    async def connect(self): # new
        """Connect to all configured MCP servers."""
        try:
            with open(os.path.join(os.getcwd(), "mcp_server", "server_config.json"), "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self._connect(server_name, server_config)
                
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    async def cleanup(self): 
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()
    
    async def call_tool(self, tool_name:str, tool_args:dict):
        # Call a tool
        session = self.tools_session[tool_name] 
        tool_result = await session.call_tool(tool_name, arguments=tool_args)
        return tool_result
    
    async def call_tool_openai(self, tool_name:str, tool_args:dict):
        # Call a tool
        session = self.tools_session[tool_name] 
        tool_result = await session.call_tool(tool_name, arguments=tool_args)
        
        schema = {**tool_result.inputSchema, "additionalProperties": False}
        
        openai_tool = FunctionTool(
                name=tool_result.name,
                description=tool_result.description,
                params_json_schema=schema,
                on_invoke_tool=lambda ctx, args, toolname=tool_result.name: session.call_tool(tool_name, arguments=tool_args))
        
        return openai_tool
    
    async def list_tools_openai(self):
        openai_tools=[]
        for session in  self.sessions:
            # Call a tool
            tool_result = await session.list_tools()
            for tool in  tool_result.tools:
                schema = {**tool.inputSchema, "additionalProperties": False}
                openai_tools.append(FunctionTool(
                        name=tool.name,
                        description=tool.description,
                        params_json_schema=schema,
                        on_invoke_tool=lambda ctx, args, toolname=tool.name: session.call_tool(toolname, json.loads(tool.inputSchema))))
        logger.info(f" 🔄 🎯 \n List tools map to OpenAI tools:, {[t.name for t in openai_tools]}! ")
        
        return openai_tools

    async def read_resource(self,resource_name):
        session = self.resources_session[resource_name]
        resource_result = await session.read_resource(resource_name)
        return resource_result