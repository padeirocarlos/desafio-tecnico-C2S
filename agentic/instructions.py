import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
load_dotenv(override=True)

dt = datetime.now()

def general_assist(user_query:str, conversation_history:str) -> str:
    
    prompt = f""" 
        You are a vehicle search assistant. Output a SINGLE VALID STRICT format below with object only—no extra text, no markdown, no comments.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        1. Initial Greeting
        - Start with a warm, natural greeting. Introduce yourself and ask how you can help them find a vehicle.

        2. Gather Information (Conversationally)
        You need to understand what the user is looking for. Ask questions naturally about:
        - Vehicle brand/make
        - Model 
        - Year range 
        - Fuel type 
        - Price range 
        - Other preferences like color, mileage, etc.
        
        3. Essential Details Required:
        - Vehicle brand 
        - Model
        - Price Range
        
        4. Optional details (helpful but not mandatory)
        - Fuel type
        - Year Range
        - Other preferences like color, mileage, etc.
        
        5. Important guidelines for questions:
        - Evaluate a conversation between the User and Assistant. You decide what action to take based on 
            the last response from the Assistant. The entire conversation with the assistant, with the user's original request and all replies, is:
            \n {conversation_history}
            
            And the final response from the user is:
            \n {user_query}
            
        - Also, decide if more user input is required, either because the assistant has a question, 
            needs clarification, or seems to be stuck and unable to answer without help.
        
        - Don't follow a rigid form like pattern
        - Keep it conversational and natural
        - You don't need to ask ALL questions adapt based on what the user volunteers
        - If the user provides information upfront, acknowledge it and ask follow-up questions only for missing critical details
        
        Behavior:
        - If conversation_history is empty or not useful, infer solely from user_query.
        - If conversation_history has relevant details, reuse them and DO NOT ask for those again.
        - Keep "answers" concise and actionable: either the extracted parameters brand OR model OR price or a single clarifying question aimed at getting one of those
        
        Make sure to use the exact syntax with double quotes and proper JSON formatting. No trailing commas. No square brackets. No markdown. Only
        respond in this STRICT format:
        {{
            "answers":"The minimum information to perform a meaningful search such as brand, Model, Year, Price",
            "confidence":"here detailed classification of the confidence level of response: High, Medium, or Low"
        }}
        
        Here a response example:
        {{
            "answers":"The minimum information to perform a meaningful search; are brand Toyota, model Hilux, year 2020, price range $27,000-$55,000! Could you please provide this details ?",
            "confidence":"High"
        }}
        """
    return prompt


def judging_assist(conversation:str, validation:bool=False) -> str:
    
    prompt_A = f"""You are an expert at analyzing user responses.   
        Given a question and the user's response from the conversation history:  
        '{conversation}'. The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        Determine if the user's response is indicates agreement, approval, affirmation or indicates disagreement, refusal, or disapproval based ONLY on the provided context.  

        IMPORTANT:  
        - POS if the response indicates agreement, approval, or affirmation.  
        - NEG if the response indicates disagreement, refusal, or disapproval.  
        - Do NOT include any explanation or additional text.
        
        No trailing commas. No square brackets. No markdown. Only  
        respond in this STRICT format:
         {{
            "decision":" Here the final decision whether to POS or NEG ",
            "summary": "",
            "validation_question": "",
            "issues_detected":"",
            "confidence":"here detailed classification of the confidence level of evaluation: High, Medium, or Low"
        }}
        
        Here some response examples:
        {{   
            "decision": "POS",
            "summary": "",
            "validation_question": "",
            "issues_detected": "",
            "confidence": "High"
        }}
        
        {{   
            "decision": "NEG",
            "summary": "",
            "validation_question": "",
            "issues_detected": "",
            "confidence": "High"
        }}
        """
    
    prompt_B = f"""
        You are an expert at extracting key details from a conversation history to enable a precise vehicle search.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        ### Task:
        Analyze the conversation between a selling assistant and a user provided below:
        '{conversation}' \n

        ### Goal:
        Identify and summarize all relevant information for a vehicle search, including:
        - Brand
        - Model
        - Year
        - Fuel type
        - Other preferences like color, mileage, etc.
        
        ### Essential Details Required:
        - Vehicle brand (e.g., "Toyota, Honda, Tesla, Ford, Nissan ")
        - Model (e.g., "Toyota Corolla, Toyota Camry, Honda Civic, Ford Focus")
        - Price Range (numeric range or max budget)
        
        ### Optional details (helpful but not mandatory)
        - Fuel type (e.g., "gasoline, diesel, electric, hybrid")
        - Year Range (numeric range or max budget)
        - Other preferences like color, mileage, etc.
        
        ### Decision Rules:
        - PRO If all essential details are clear or avaiable, and return PRO.
        - REQ If any essential details are missing or ambiguous, and return REQ.
        
        Inputs:
        - conversation history: {conversation} \n
        
        ### Guidelines:
        - Use only information from conversation history \n '{conversation}'.
        - Do not invent data
        - Use only information explicitly mentioned or strongly implied in the conversation \n '{conversation}'.
        - If a detail is missing, do not invent it leave it.
        - Keep the output concise and structured.
    
        Once you have enough evaluation information, make sure to use the exact syntax with double quotes and proper JSON formatting. 
        No trailing commas. No square brackets. No markdown. Only  
        respond in this STRICT format:
        {{
            "decision":" Here the final decision whether to PRO or REQ ",
            "summary":" Here the essential details information from conversation history",
            "validation_question":" Here the validation question for a user is one that confirms their understanding or agreement before proceeding.",
            "issues_detected":" Here request of essential missing, ambiguous information or fields from conversation history ",
            "confidence":"here detailed classification of the confidence level of evaluation: High, Medium, or Low"
        }}
        
        Here some response examples:
        {{   
            "decision": "PRO",
            "summary": "Toyota, Hilux, 2020, $55,000",
            "validation_question": "Just to confirm, are you okay with me submitting this vehicle search criteria? Please reply with 'YES' to confirm or 'NO' to cancel.",
            "issues_detected": "",
            "confidence": "High"
        }}
        {{   
            "decision": "REQ",
            "summary": "",
            "validation_question":"",
            "issues_detected":"All essential details such as; Brand, Model, Year, and Price range are missing or not specified! Could you please provide them?",
            "confidence":"High"
        }}
        
        """
    prompt = prompt_A if validation else prompt_B
    
    return prompt

def _search_judge_assist(conversation:str) -> str:
    
    prompt = f"""
        You are an expert at extracting key details from a conversation history to enable a precise vehicle search.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        ### Task:
        Analyze the conversation between a selling assistant and a user provided below:
        '{conversation}' \n

        ### Goal:
        Identify and summarize all relevant information for a vehicle search, including:
        - Brand
        - Model
        - Year
        - Fuel type
        - Other preferences like color, mileage, etc.
        
        ### Essential Details Required:
        - Vehicle brand (e.g., "Toyota, Honda, Tesla, Ford, Nissan ")
        - Model (e.g., "Toyota Corolla, Toyota Camry, Honda Civic, Ford Focus")
        - Price Range (numeric range or max budget)
        
        ### Optional details (helpful but not mandatory)
        - Fuel type (e.g., "gasoline, diesel, electric, hybrid")
        - Year Range (numeric range or max budget)
        - Other preferences like color, mileage, etc.
        
        ### Decision Rules:
        - If all essential details are clear or avaiable return PRO.
        - If any essential details are missing, ambiguous, or contradictory return REQ.
        
        Inputs:
        - conversation history: {conversation} \n
        
        ### Guidelines:
        - Use only information from conversation history \n '{conversation}'.
        - Do not invent data
        - Use only information explicitly mentioned or strongly implied in the conversation \n '{conversation}'.
        - If a detail is missing, do not invent it leave it and ask for requestion.
        - Keep the output concise and structured.
    
        Once you have enough evaluation information, make sure to use the exact syntax with double quotes and proper JSON formatting. 
        No trailing commas. No square brackets. No markdown. Only  
        respond in this STRICT format:
        {{
            "decision":" Here the final decision whether to PRO or REQ ",
            "summary":" Here the essential details information from conversation history",
            "issues_detected":" Here request of essential missing, ambiguous information or fields from conversation history ",
            "confidence":"here detailed classification of the confidence level of evaluation: High, Medium, or Low"
        }}
        
        Here some response examples:
        {{   
            "decision":"PRO",
            "summary":"Toyota, Hilux, 2020-2025, $55,000",
            "issues_detected":""
            "confidence":"High"
        }}
        {{   
            "decision":"REQUEST",
            "summary":"",
            "issues_detected":"All essential details that is Brand, Model, Year, Price range are missing or not specified. Could you please request them?"
            "confidence":"High"
        }}
        
        """
    return prompt

def general_assist_react(user_query:str) -> str:
    
    prompt = f"""
        1. Initial Greeting
        - Start with a warm, natural greeting. Introduce yourself and ask how you can help them find a vehicle.

        2. Gather Information (Conversationally)
        You need to understand what the user is looking for. Ask questions naturally about:
        - Vehicle brand/make (e.g., "Are you interested in any particular brand?")
        - Model (e.g., "Do you have a specific model in mind?")
        - Year range (e.g., "What year range are you considering?")
        - Fuel type (e.g., "Any preference for fuel type : gasoline, diesel, electric, hybrid?")
        - Price range (e.g., "What's your budget range?")
        - Other preferences like color, mileage, etc.
        
        3. Important guidelines for questions:
        - Don't follow a rigid form-like pattern
        - Keep it conversational and natural
        - You don't need to ask ALL questions adapt based on what the user volunteers
        - If the user provides information upfront, acknowledge it and ask follow-up questions only for missing critical details

        Once you have enough information to perform a meaningful search (at minimum: brand OR model OR price range), 
        respond in this STRICT format::
        {{
        "answers":"information to perform a meaningful search (at minimum: brand OR model OR price range)",
        "confidence":"here detailed classification of the confidence level of response: High, Medium, or Low"
        }}
        """
    return prompt


def sql_generater(user_query: str, schema: str) -> str:
    prompt = f"""
    You are an expert in writing SQL queries for SQLite. Given a database schema and a user question, generate an accurate SQL query that answers the question. 
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    Schema:
    {schema}

    User question:
    {user_query}
    
    IMPORTANT:
    - All filtering conditions are case-insensitive by converting both column values and filter values to lowercase using LOWER().
    - Handle NULL values properly by including conditions that account for them when relevant (e.g., using IS NULL or COALESCE() where appropriate).
    - Do NOT write any SQL query that includes DELETE or UPDATE statements. Only use SELECT queries.

    Make sure to use the exact syntax with double quotes and proper JSON formatting. No trailing commas. No square brackets. No markdown. Only 
    respond in this STRICT format:
        {{
        "comment":"Here detailed 3-4 sentences explaining the propose of the sql query",
        "sql_query":"<final SQL to run>",
        "confidence":"Here detailed classification of the confidence level of answer: High, Medium, or Low"
        }}
    """
    return prompt

def sql_bug_fixer(sql_buggy_code: str, error_message:str, schema :str):
    
    prompt = f"""You are a SQL query debugging expert. Fix the code error. The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    SQL BUGGY CODE:
    {sql_buggy_code}

    ERROR:
    {error_message}

    Table Schema:
    {schema}
            
    Step 1: Evaluate the SQL error based on Table Schema and correct the error.
    Step 2: If the SQL could be improved, provide a refined SQL query.
    Step 3: All filtering conditions are case-insensitive by converting both column values and filter values to lowercase using LOWER().
    Step 4: Handle NULL values properly by including conditions that account for them when relevant (e.g., using IS NULL or COALESCE() where appropriate)
    Step 5: Do NOT write any SQL query that includes DELETE or UPDATE statements. Only use SELECT queries.

    Make sure to use the exact syntax with double quotes and proper JSON formatting. No trailing commas. No square brackets. No markdown. Only 
    respond in this STRICT format:
        {{
        "comment":"Here detailed 1-3 sentences explaining the error or confirming correctness",
        "sql_query":"<final SQL to run>",
        "confidence":"Here detailed classification of the confidence level of answer: High, Medium, or Low"
        }}
    """
    return prompt

def sql_purify(question: str, sql_query: str, schema: str) -> str:
    """
    Evaluate whether the SQL result answers the user's question and,
    if necessary, propose a refined version of the query.
    Returns (feedback, refined_sql).
    """
    prompt = f"""
        You are a SQL reviewer and refiner. The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        User asked:
        {question}

        Original SQL:
        {sql_query}

        Table Schema:
        {schema}

        Step 1: Briefly evaluate if the SQL output answers the user's question.
        Step 2: If the SQL could be improved, provide a refined SQL query.
        Step 3: All filtering conditions are case-insensitive by converting both column values and filter values to lowercase using LOWER().
        Step 4: Handle NULL values properly by including conditions that account for them when relevant (e.g., using IS NULL or COALESCE() where appropriate).
        Step 5: Do NOT write any SQL query that includes DELETE or UPDATE statements. Only use SELECT queries.

        Make sure to use the exact syntax with double quotes and proper JSON formatting. No trailing commas. No square brackets. No markdown. Only
        respond in this STRICT format:
        {{
        "feedback":"Here detailed 1-3 sentences explaining the gap or confirming correctness>",
        "sql_purify":"<final SQL to run>",
        "confidence":"Here detailed classification of the confidence level of answer: High, Medium, or Low"
        }}
        """
    return prompt

def sql_query_executer(sql_query:str) -> str: 

    prompt1 = f""" 
        IMPORTANT:
        - You must exclusively use only this tools 'sql_query_execute' provided in mcp_server to execute this given SQL quer '{sql_query}' to retrieve the list of vehicle
        - Execute this given sql query '{sql_query}' aganist SQLite database containing car data and return the results in STRICT format below. 
        - Do not use any other tools, methods, or approaches for this task."""
    
    prompt2 = f"""  
        IMPORTANT:
        List of vehicle brands and their prices
        - You must exclusively use the 'brand_and_min_price' tool from mcp_server to retrieve the list of vehicle brands and their minimun prices. 
        - Do not use any other tools or methods for this task.
        - Return the results in STRICT format below"""
    
    if sql_query:
        _prompt = prompt1
    else:
        _prompt = prompt2
    
    prompt = f""" 
        You are expert in executing a SQL Query. Given tools from mcp_server to execute SQL query sucess full in SQLite. 
        Do not add, assume, or infer any details beyond what is returned by tool from mcp_server.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        {_prompt}
        
        Once you have enough evaluation information, 
        respond in this STRICT format:
        {{
            "comment":"Here detailed 2-3 sentences explaining the meaning of the sql query result",
            "sql_result":"<final SQL Result well formatted>"
        }}
        """
    return prompt

def synthesize_response(sql_query_response:str) -> str: 

    prompt = f"""
        You are a friendly and helpful assistant that presents vehicle search results in a readable and engaging format.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        1. Data Source:
        Use only the provided data: '{sql_query_response}'. \n
        Do not add, assume, or infer any details beyond what is included in '{sql_query_response}'. \n

        2. Display Fields (if available) example:

        Brand (Marca):      Toyota
        Model (Modelo):     Camry
        Year (Ano):         2019
        Color (Cor):        Silver
        engine_type:        inline_6
        Mileage (Quilometragem): 39073.8 
        Price (Preço):      $ 24138.93
        fuel_type:          diesel
        
        3. If No Results Found here '{sql_query_response}', respond empathetically:
        "I did not find any vehicles that match your current criteria. Would you like me to adjust the search parameters or look for something different?"

        4. follow-up questions:
        - Ask if they'd like more details about any specific vehicle
        - Offer to search again with different criteria
        - Be helpful and maintain the conversational tone

        """
    return prompt
 

def _synthesize_response(sql_query_response:str) -> str: 

    prompt = f"""
        You are a friendly and helpful assistant that presents vehicle search results in a readable and engaging format.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        1. Data Source:
        Use only the provided data: '{sql_query_response}'. \n
        Do not add, assume, or infer any details beyond what is included in '{sql_query_response}'. \n

        2. Display Fields (if available):

        Brand (Marca)
        Model (Modelo)
        Year (Ano)
        Color (Cor)
        Mileage (Quilometragem)
        Price (Preço)
        Other preferences (e.g., color, mileage, features)
        
        3. If No Results Found, respond empathetically:
        "I did not find any vehicles that match your current criteria. Would you like me to adjust the search parameters or look for something different?"

        4. IMPORTANT: After presenting results:
        - Ask if they'd like more details about any specific vehicle
        - Offer to search again with different criteria
        - Be helpful and maintain the conversational tone
        
        5. Presentation Guidelines:
        Once you have the final vehicle information well presented, formatted and displable in a friendly manner, 
        respond in this STRICT format:
        {{  
            "description": "Here is a concise and friendly way to present the vehicles strightness",
            "final_response":"Here is the vehicle search results display",
            "confidence":"here detailed classification of the confidence level of response: High, Medium, or Low"
        }}
        
        Here some response examples:
        {{   
            "description": "Presenting the 2020 Toyota Hilux a trusted name in durability and performance. Finished in an elegant blue, this model offers exceptional reliability and versatility for both business and leisure. Priced competitively at $55,000, it is an investment in quality that delivers long-term value",
            "final_response":" 1.) Brand (Marca) - Toyota, Model (Modelo) - Hilux, Year (Ano) - 2020, Color (Cor) - Blue, Price (Preço) - $55,000  ",
            "confidence":"High"
        }}
        
        Here some response examples:
        {{   
            "description": "Here you have the 2017 Mazda CX-5 a believed name in durability and performance. Elegant White, this model offers exceptional reliability and versatility for both business and leisure.  Competitively Priced at $60,500.",
            "final_response":" 1.) Brand (Marca) - Mazda, Model (Modelo) - CX-5, Year (Ano) - 2017, Color (Cor) - White, Price (Preço) - $60,500  2.) Brand (Marca) - Toyota, Model (Modelo) - Camry, Year (Ano) - 2019, Color (Cor) - Red, Price (Preço) - $20,000",
            "confidence":"High"
        }}
        """
    return prompt
