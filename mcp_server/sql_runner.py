import sqlite3
import pandas as pd
from typing import List, Dict
from mcp.server.fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP(name="SQL_Runner_Server",
            description="A simple SQL database API that demonstrates FastAPI and MCP integration",
            version="1.0.0")

@mcp.resource("config://app-version")
def get_app_version() -> dict:
    """Static resource providing application version information"""
    return {
        "name": "SQL Runner Server",
        "version": "1.0.0",
        "release_date": "2025-12-16",
        "environment": "PRODUCTION"
    }

@mcp.tool()
def brand_and_min_price() -> List[Dict]:
    
    """ Retrieves all vehicle brands with their minimum (cheapest) price, sorted from lowest to highest price.
      
        return:
            List[Dict]: A list of dictionaries, each containing:
            brand (str): Vehicle brand name
            min_price (float/int): Lowest price for that bran
        
        Database:
            Connects to data/cars.db (SQLite database)
            Automatically closes connection after execution
    """
    
    sql ="""SELECT brand, MIN(price) as min_price 
            FROM vehicles 
            GROUP BY brand 
            ORDER BY min_price ASC"""

    try:
        conn = sqlite3.connect("data/cars.db")
        
        result = pd.read_sql_query(sql, conn)
        result = result.to_dict(orient="records")
        return result
    except Exception as e:
        raise e
    finally:
        conn.close()
        
@mcp.tool()
def sql_query_execute(sql_query: str) -> List[Dict]:
    
    """ Executes SQL queries against a SQLite database containing car data and returns results as a List[Dict].
        Args:
            sql_query (str): A SQL query string to execute. The function accepts 
                            queries with or without markdown SQL code block formatting
      
        return:
            List[Dict]: Query results as a list of dictionaries with all details of vehicle, where each dictionary 
                        represents one row with column names as keys
        
        Database:
            Connects to 'data/cars.db' (SQLite database)
            Automatically closes connection after execution
        
        Example Usage:
            df = sql_query_execute("SELECT * FROM cars LIMIT 10")
    """
    
    if sql_query:
        sql_purify = sql_query
    try:
        conn = sqlite3.connect("data/cars.db")
        q = sql_purify.strip().removeprefix("```sql").removesuffix("```").strip()
        result = pd.read_sql_query(q, conn)
        result = result.to_dict(orient="records")
        return result
    except Exception as e:
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    # login(hf_token, add_to_git_credential=True)
    mcp.run(transport='stdio')