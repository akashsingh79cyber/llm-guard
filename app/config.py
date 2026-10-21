import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:9000/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))