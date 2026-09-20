"""
neo/tools/error_memory.py
=========================
Layer 1 Error Memory. Allows Neo to log solutions to persistent errors.
"""
import json
import os

MEMORY_FILE = "neo/memory/error_fixes.json"

def memorize_error_fix(error_snippet: str, solution: str) -> str:
    """Saves a proven solution for a specific error snippet."""
    fixes = {}
    
    # Ensure memory folder exists
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                fixes = json.load(f)
        except:
            pass
            
    fixes[error_snippet] = solution
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(fixes, f, indent=2)
        
    return f"✅ Memorized! If I see '{error_snippet}' again, I will know to: {solution}"
