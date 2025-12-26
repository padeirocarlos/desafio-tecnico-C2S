
An intelligent virtual assistant for browsing and searching vehicles in a dealership database, featuring natural language interaction and MCP (Model Context Protocol) architecture.
## 📋 Table of Contents

## 🎯 Overview:
This project implements a conversational virtual assistant that helps users find vehicles in a dealership database. Instead of traditional menu-based interfaces, the assistant engages in natural conversation to understand user preferences and requirements.
Key Highlights

Natural Language Interaction: Chat with the assistant naturally - no rigid forms or menus
MCP Architecture: Clean separation between client, server, and database layers
Intelligent Search: The assistant asks relevant follow-up questions based on context
Rich Database: 100+ vehicles with realistic attributes
Terminal-Based: Runs entirely in the command line

## 🏗️ Architecture

![Data → processed Flowchart](dev/output.png)

## Description of Flowchart:
- **Data**: → processed by Agent
- **Agent**: → invokes Reflection Invoker
- **Reflection**: Invoker → dynamically selects and calls Processing Logic
- **Processing Logic**: → returns results back to the agent for further steps.

## ✨ Features

- **🤖 Virtual Agent**: Conversational AI that understands user intent
- **💬 Natural Dialogue**: Ask questions in your own words
- **🔍 Smart Filtering**: Filter by brand, model, year, fuel type, price range, and more
- **📊 Detailed Results**: View brand, model, year, color, mileage, and price
- **🔄 MCP Protocol**: Proper client-server-database architecture
- **📝 100+ Vehicles**: Pre-populated database with realistic data
- **🎨 User-Friendly**: Clear, formatted output in the terminal

## Communication Flow

- **User**: → Types natural language query in terminal
- **Client**: → Extracts filters and sends to MCP Server
- **MCP Server**: → Validates, queries database, returns results
- **Client** → Formats and displays results to user

## 🔧 Prerequisites
Before you begin, ensure you have the following installed:
- **Python**: 3.8+
- **pip**: (Python package manager)
- **Virtual environment**: (recommended)

## 🚀 How to Run

1. Clone the repository:
   ```bash
   - **STEPS**
      1. git clone https://github.com/padeirocarlos/desafio-tecnico-C2S.git
         curl -fsSL https://ollama.com/install.sh | sh
         ollama server
         ollama pull ollama3  # pull one of this model: gemma4B_v gemma12B_v qwen3 gemini ollama3.2 deepseek
      2. cd desafio-tecnico-C2S
         2.1. touch .env ( create this file put your keys)
         2.2. change variable name in this files:
            - agentic/agents_client.py
            - agentic/api_base_url.py
      3. uv add -r requirements.txt
         uv run app.py

   - **Running on**:
      1. local URL:  
         http://127.0.0.1:7860
  
      2. Running on public URL: 
         output example: https://277d00fc4eb724a0ce.gradio.live
