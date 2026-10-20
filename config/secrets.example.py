'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    24.12.3.10.30
'''


###################################################### CONFIGURE YOUR TOOLS HERE ######################################################


# Login Credentials for LinkedIn (Optional)
username = "your_email@gmail.com"       # Enter your username in the quotes
password = "your_password_here"           # Enter your password in the quotes


## Artificial Intelligence (Beta Not-Recommended)
# Use AI
use_AI = True                          # True or False, Note: True or False are case-sensitive
'''
Note: Set it as True only if you want to use AI, and If you either have a
1. Local LLM model running on your local machine, with it's APIs exposed. Example softwares to achieve it are:
    a. Ollama - https://ollama.com/
    b. llama.cpp - https://github.com/ggerganov/llama.cpp
    c. LM Studio - https://lmstudio.ai/ (Recommended)
    d. Jan - https://jan.ai/
2. OR you have a valid OpenAI API Key, and money to spare, and you don't mind spending it.
CHECK THE OPENAI API PIRCES AT THEIR WEBSITE (https://openai.com/api/pricing/). 
'''

# Select AI Provider 
ai_provider = "openai"                # "openai", "gemini" (Use "openai" for local Ollama via OpenAI-compatible API)
'''
Note: Select your AI provider. 
* "openai" - OpenAI-compatible local APIs (like Ollama at localhost:11434) or OpenAI API
* "gemini" - Google Gemini API (Gemini models) 
'''

# Your LLM url or other AI api url and port (Ollama local endpoint)
llm_api_url = "http://localhost:11434/v1/"

# Your LLM API key or other AI API key 
llm_api_key = "not-needed"              # Enter "not-needed" for local Ollama

# Main LLM model name for LinkedIn Easy Apply question answering (Fast local Ollama model)
llm_model = "qwen2.5:7b"                # Options in your Ollama: "qwen2.5:7b", "qwen3:1.7b", "llama3.1:8b"

# Fast LLM model specifically for Gmail status tracking & email categorization (local Ollama)
gmail_ai_model = "qwen3:1.7b"

# Vision LLM model specifically for External Applications (reads screenshots to make decisions & verify submissions)
browser_vision_model = "qwen3.5:2b"    # Options in your Ollama: "qwen3.5:2b" (recommended fast), "qwen3.5:9b"

llm_spec = "openai"                # OpenAI-compatible format for Ollama

# # Yor local embedding model name or other AI Embedding model name 
# llm_embedding_model = "nomic-embed-text-v1.5" 

# Do you want to stream AI output? 
stream_output = False                    # Examples: True or False. (False is recommended for performance, True is recommended for user experience!)
'''
Set `stream_output = True` if you want to stream AI output or `stream_output = False` if not. 
'''
##




############################################################################################################ 
'''
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻! 

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive. 

Support my work on <PATREON_LINK>. Together, we can help more job seekers. 

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact. 

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving. 

Gratefully yours 🙏🏻, 
Sai Vignesh Golla 
''' 
############################################################################################################ 