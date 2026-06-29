"""
neo/tools/deep_memory.py
========================
Zero-Cost Local Vectorized Deep Memory (RAG).
Uses Local Ollama for embeddings and pure Numpy for semantic search.
Optimized for 8GB constraints. Rate-limit immune.
"""
import os
import json
import requests
import numpy as np

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "deep_memory.json")
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

def _load_db():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"documents": [], "embeddings": []}

def _save_db(db):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f)

def _get_embedding(text: str) -> list:
    """Calls local Ollama for zero-cost vector embeddings."""
    response = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=10)
    response.raise_for_status()
    return response.json()["embedding"]

def memorize(text: str) -> str:
    """Stores vital text, context, or routines into N.E.O.'s long-term semantic memory."""
    try:
        db = _load_db()
        if text in db["documents"]:
            return "✅ MEMORY FAULT: Data already exists in the Vector Matrix."
            
        vector = _get_embedding(text)
        
        db["documents"].append(text)
        db["embeddings"].append(vector)
        _save_db(db)
        return f"✅ MEMORY STORED: '{text[:50]}...'"
    except requests.exceptions.ConnectionError:
        return "❌ MEMORY FAULT: Ollama is not running. Please start Ollama."
    except Exception as e:
        return f"❌ MEMORY FAULT: Pipeline collapse: {str(e)}"

def recall(query: str) -> str:
    """Searches N.E.O.'s long-term memory for highly relevant past context."""
    try:
        db = _load_db()
        if not db["documents"]:
            return "❌ DEEP MEMORY IS CURRENTLY EMPTY."
            
        query_vector = np.array(_get_embedding(query))
        
        # Calculate Cosine Similarity efficiently
        db_vectors = np.array(db["embeddings"])
        dot_products = np.dot(db_vectors, query_vector)
        norms = np.linalg.norm(db_vectors, axis=1) * np.linalg.norm(query_vector)
        
        # Prevent division by zero errors on empty vectors
        norms = np.where(norms == 0, 1e-10, norms)
        similarities = dot_products / norms
        
        # Extract Top 3 most relevant memories (Threshold > 0.55)
        top_indices = np.argsort(similarities)[-3:][::-1]
        results = [db["documents"][i] for i in top_indices if similarities[i] > 0.55]
        
        if not results:
            return "❌ NO RELEVANT MEMORIES FOUND FOR THIS QUERY."
            
        memories = "\n".join([f"- {doc}" for doc in results])
        return f"✅ RETRIEVED CONTEXT:\n{memories}"
    except requests.exceptions.ConnectionError:
        return "❌ RECALL FAULT: Ollama is not running. Please start Ollama."
    except Exception as e:
        return f"❌ RECALL FAULT: Pipeline collapse: {str(e)}"
