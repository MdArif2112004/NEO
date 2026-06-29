import os

NEO_CONFIG = {
    # "groq"   → your Groq key (Fast, versatile, bypassing Gemini limits)
    # "gemini" → your Gemini key 
    # "ollama" → free local, no key
    "llm_backend": "groq",

    # Pulls from environment variable first, otherwise paste it below
    "groq_api_key": os.getenv("GROQ_API_KEY") or "",
    
    "groq_model":   "openai/gpt-oss-120b",   
    "ollama_model": "llama3.2",
    "ollama_url":   "http://localhost:11434",

    "permission_mode": "ask",
    "require_permission_for": ["delete_file","write_file","run_file"],
    "max_steps":   20,
    "auto_backup": True,
    "allowed_directories": [],
}
