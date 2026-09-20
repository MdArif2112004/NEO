"""
neo/llm/model.py
================
Triple-Engine Cognitive Core: Gemini (New SDK) -> Groq -> Ollama
"""
import os
import requests
import json

class LLMEngine:
    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
        
        if self.gemini_key:
            print("[Neo LLM] ✅ Primary Engine: Gemini (genai SDK)")
        elif self.groq_key:
            print("[Neo LLM] ✅ Primary Engine: Groq (Llama 3.3)")
        else:
            print("[Neo LLM] ⚠️ No Cloud APIs detected. Relying on Local Ollama.")

    def chat(self, system_prompt: str, messages: list) -> str:
        if self.gemini_key:
            try:
                return self._chat_gemini(system_prompt, messages)
            except Exception as e:
                print(f"[Neo LLM] ❌ Gemini Failed: {e}. Falling back to Groq...")

        if self.groq_key:
            try:
                return self._chat_groq(system_prompt, messages)
            except Exception as e:
                print(f"[Neo LLM] ❌ Groq Failed: {e}. Falling back to Ollama...")

        return self._chat_ollama(system_prompt, messages)

    def _chat_gemini(self, system_prompt: str, messages: list) -> str:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=self.gemini_key)
        
        # Convert our message format to the new Google GenAI format
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
            )
            
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0
            )
        )
        return response.text

    def _chat_groq(self, system_prompt: str, messages: list) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}", 
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _chat_ollama(self, system_prompt: str, messages: list) -> str:
        print("[Neo LLM] 🧠 Processing via local Ollama...")
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": "llama3.2",
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False
        }
        res = requests.post(url, json=payload, timeout=300) # Increased to 5 minutes to protect 8GB RAM
        res.raise_for_status()
        return res.json()["message"]["content"]

def get_model():
    return LLMEngine()
