import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .api_base_url import ApiConfig
from agents import OpenAIChatCompletionsModel, set_tracing_disabled, set_default_openai_client, set_default_openai_api

set_default_openai_api("chat_completions")
set_tracing_disabled(True)
load_dotenv(override=True)

anthropic_openai = AsyncOpenAI(api_key=os.getenv(ApiConfig.ANTHROPIC_API_KEY_NAME), base_url=ApiConfig.ANTHROPIC_BASE_URL)
set_default_openai_client(anthropic_openai, use_for_tracing=False)
anthropic_client = OpenAIChatCompletionsModel(model=ApiConfig.ANTHROPIC_MODEL, openai_client=anthropic_openai)

gemini_openai = AsyncOpenAI(api_key=os.getenv(ApiConfig.GEMINI_API_KEY_NAME), base_url=ApiConfig.GEMINI_BASE_URL)
set_default_openai_client(gemini_openai, use_for_tracing=False)
gemini_client = OpenAIChatCompletionsModel(model=ApiConfig.GEMINI_MODEL, openai_client=gemini_openai)

deepseek_openai = AsyncOpenAI(api_key=os.getenv(ApiConfig.DEEPSEEKAI_API_KEY_NAME), base_url=ApiConfig.DEEPSEEK_BASE_URL)
set_default_openai_client(deepseek_openai, use_for_tracing=False)
deepseek_client = OpenAIChatCompletionsModel(model=ApiConfig.DEEP_SEEK_MODEL, openai_client=deepseek_openai) 

# Base configuration for ollama openai local use
ollama_openai = AsyncOpenAI(api_key=os.getenv(ApiConfig.OLLAMA_PUBLIC_KEY_NAME), base_url=ApiConfig.OLLAMA_BASE_URL)
set_default_openai_client(ollama_openai, use_for_tracing=False)

# client configuration for which ollama openai local use
deepseek_r1_client = OpenAIChatCompletionsModel(model=ApiConfig.DEEP_SEEK_R1_MODEL, openai_client=ollama_openai) 
ollama_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_32_MODEL, openai_client=ollama_openai)
ollama3_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_3_MODEL, openai_client=ollama_openai)
qwen3_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_QWEN_3_MODEL, openai_client=ollama_openai)
olmo_3_7b_client = OpenAIChatCompletionsModel(model=ApiConfig.OLMO_3_7B_MODEL, openai_client=ollama_openai)
gemma12B_vclient = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_GEMMA_12B_MODEL, openai_client=ollama_openai) 
gemma1B_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_GEMMA_1B_MODEL, openai_client=ollama_openai)
qwen3_coder_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_QWEN3_CODER_MODEL, openai_client=ollama_openai)
qwen2_5_coder_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_QWEN_CODER_25_MODEL, openai_client=ollama_openai)
gpt_oss_20b_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_GPT_20_MODEL, openai_client=ollama_openai)
gpt_oss_120b_client = OpenAIChatCompletionsModel(model=ApiConfig.LLMA_GPT_120_MODEL, openai_client=ollama_openai)

model_client_name_dict = {"ollama": ollama_client,
              "ollama3": ollama3_client,
              "olmo-3:7b": olmo_3_7b_client,
              "qwen3": qwen3_client, 
              "gemma3:1b": gemma1B_client,
              "gemma12B_v": gemma12B_vclient,
              "anthropic": anthropic_client,
              "deepseek":deepseek_client,
              "deepseek":deepseek_client,
              "deepseek-r1":deepseek_r1_client,
              "gemini": gemini_client,
              "qwen3-coder": qwen3_coder_client,
              "qwen2.5-coder": qwen2_5_coder_client,
              "gpt-oss:20b": gpt_oss_20b_client,
              "gpt-oss:120b": gpt_oss_120b_client,
              }