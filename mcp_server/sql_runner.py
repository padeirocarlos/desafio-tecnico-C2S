import sqlite3
import logging
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
logger = logging.getLogger(" SQLite3 Database Tools that demonstrates FastAPI and MCP integration (SFM)")

DB = "cars.db"
#  mcp_server$ npx @modelcontextprotocol/inspector python sql_runner.py 
mcp = FastMCP(name="SQL_Runner_Server",
            description="A simple SQL database API that demonstrates FastAPI and MCP integration",
            version="1.0.0")

@mcp.resource("config://app-version")
async def get_app_version() -> dict:
    """Static resource providing application version information"""
    return {
        "name": "SQL Runner Server",
        "version": "1.0.0",
        "release_date": "2025-12-16",
        "environment": "PRODUCTION"
    }

@mcp.tool()
async def brand_and_min_price() -> List[Dict]:
    
    """ Retrieves all vehicle brands with their minimum (cheapest) price, sorted from lowest to highest price.
      
        return:
            List[Dict]: A list of dictionaries, each containing:
            brand (str): Vehicle brand name
            min_price (float/int): Lowest price for that bran
        
        Database:
            Automatically closes connection after execution
    """
    
    sql = """SELECT brand, MIN(price) as min_price 
            FROM vehicles 
            GROUP BY brand 
            ORDER BY min_price ASC"""

    with sqlite3.connect(DB) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            result = reversed(cursor.fetchall())
            return result
        except Exception as e:
            raise e

@mcp.tool()
async def sql_query_execute(sql_query: str) -> List[Dict]:
    
    """ Executes SQL queries against a SQLite database containing car data and returns results as a List[Dict].
        Args:
            sql_query (str): A SQL query string to execute. The function accepts 
                            queries with or without markdown SQL code block formatting
      
        return:
            result: Query results as a list of dictionaries with all details of vehicle, where each dictionary 
                        represents one row with column names as keys
        
        Database:
            Automatically closes connection after execution
        
        Example Usage:
            result = sql_query_execute("SELECT * FROM vehicles LIMIT 10")
    """
    with sqlite3.connect(DB) as conn:
        try:
            sql = sql_query.strip().removeprefix("```sql").removesuffix("```").strip()
            cursor = conn.cursor()
            cursor.execute(sql)
            result = reversed(cursor.fetchall())
            return result
        except Exception as e:
            raise e


@mcp.tool()
async def run_transactional_query(sql_query: str) -> None:
    
    """ Executes SQL queries against a SQLite database containing car data.
        Args:
            sql_query (str): A SQL query string to execute. The function accepts 
                            queries with or without markdown SQL code block formatting
        
        Database:
            Automatically commit transaction after execution
            Automatically closes connection after execution
        
        Example Usage:
            transactional_sql_query_execute("INSERT INTO vehicles (brand, model, fuel_type, price)
            VALUES (?, ?, ?, ?)")
    """

    with sqlite3.connect(DB) as conn:
        try:
            sql = sql_query.strip().removeprefix("```sql").removesuffix("```").strip()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            raise e
        
if __name__ == "__main__":
    logger.info(f" ✅ 🔄 🎯 Starting the SQL Query MCP Server Content Explorer with STDIO transport ...! 🚀 ")
    
    # logger.info(f" 🔄 The service will be accessible via HTTP endpoints ... 🎯")
    # logger.info(f" 🔄 1. Be accessed over HTTP ... 🎯")
    # logger.info(f" 🔄 2. Handle multiple concurrent requests ... 🎯")
    # logger.info(f" 🔄 3. Be integrated with web services ... 🎯")
    
    mcp.run(transport="stdio") # mcp.run(transport='http') stdio
    