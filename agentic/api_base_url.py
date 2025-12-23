from enum import StrEnum

class ApiConfig(StrEnum):
    # URL Base
    ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1/"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GROK_BASE_URL = "https://api.x.ai/v1"
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
    
    # Model name
    DEEP_SEEK_MODEL = "deepseek-chat"
    DEEP_SEEK_R1_MODEL = "deepseek-r1"
    GEMINI_MODEL = "gemini-2.0-flash"
    OPENAI_MODEL = "gpt-4o-mini"
    ANTHROPIC_MODEL = "claude-sonnet-4-5"
    LLMA_GPT_20_MODEL="gpt-oss:20b"
    OLMO_3_7B_MODEL="olmo-3:7b-instruct"
    LLMA_GPT_120_MODEL="gpt-oss:120b"
    
    LLMA_DEEPSEEK_MODEL = "deepseek-r1:1.5b"
    LLMA_GEMMA_270M_MODEL = "gemma3:270m"
    LLMA_QWEN_CODER_25_MODEL = "qwen2.5-coder"
    LLMA_QWEN_3_MODEL = "qwen3:latest"
    LLMA_32_MODEL = "llama3.2:latest"
    LLMA_3_MODEL =  "llama3:latest"
    
    # VISION and Multi Model name
    LLMA_GEMMA_4B_MODEL = "gemma3:4b"
    LLMA_GEMMA_1B_MODEL = "gemma3:1b"
    LLMA_GEMMA_12B_MODEL = "gemma3:12b"
    LLMA_QWEN3_CODER_MODEL = "qwen3-coder:30b"
    
    
    LLMA_QWEN2_MODEL = "siasi/qwen2-vl-7b-instruct"
    LLMA_QWEN3_MODEL = "qwen3-vl:8b"
    LLMA_LLAVA_MODEL = "llava:7b-v1.6"

    # Personal accounting API
    OPENAI_API_KEY_NAME = "OPENAI_API_KEY"

    # OpenRouter API
    OPENROUTER_API_KEY_NAME = "OPENROUTER_API_KEY"

    # Personal accounting API
    DEEPSEEKAI_API_KEY_NAME = "DEEPSEEKAI_API_KEY"

    # ANTHROPIC_API_KEY
    ANTHROPIC_API_KEY_NAME = "ANTHROPIC_API_KEY"

    # OLLAMA_PUBLIC_KEY =
    OLLAMA_PUBLIC_KEY_NAME = "OLLAMA_PUBLIC_KEY"

    # GOOGLE_API_KEY
    GOOGLE_API_KEY_NAME = "GOOGLE_API_KEY"
    
    GEMINI_API_KEY_NAME = "GEMINI_API_KEY"

    # GROQ_API_KEY
    GROQ_API_KEY_NAME = "GROQ_API_KEY"

    GMAIL_APP_PASSWORD_NAME ="GMAIL_APP_PASSWORD" 
    
    HUGGING_FACE_API_TOKEN="HUGGING_FACE_API_TOKEN"
    
   