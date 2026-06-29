"""
neo/tools/meta_coder.py
=======================
The Meta-Coder (Self-Writing Tool Protocol).
Allows N.E.O. to autonomously write, save, and install new Python tools 
into its own nervous system without operator intervention.
"""
import os
import json
from groq import Groq

def write_custom_tool(tool_name: str, objective: str) -> str:
    """Autonomously writes a new Python tool and wires it into brain.py."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ META-CODER FAULT: Missing GROQ_API_KEY."

    print(f"\n[META-CODER] Initiating Neural Synthesis for tool: '{tool_name}'...")
    print(f"  -> Objective: {objective[:50]}...")

    client = Groq(api_key=api_key)

    # 1. Synthesize the Python Code
    system_prompt = """You are an elite Python Architect building tools for an autonomous agent.
    Write a single Python file containing a function named EXACTLY the requested tool_name.
    Rules:
    1. Only return the raw Python code. NO markdown formatting. NO triple backticks (```).
    2. The function MUST return a String indicating success or failure (e.g., '✅ Success: ...' or '❌ Error: ...').
    3. Include all necessary standard library imports at the top. Do not use obscure third-party libraries unless strictly necessary.
    4. Keep it robust, safe, and optimized for an 8GB RAM Windows machine.
    """
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Write a tool named '{tool_name}' that does the following: {objective}"}
            ],
            temperature=0.2, # Low temp for code accuracy
            max_tokens=1500
        )
        
        raw_code = response.choices[0].message.content.strip()
        
        # Clean up any markdown the LLM might have hallucinated despite the rules
        if raw_code.startswith("```python"):
            raw_code = raw_code[9:]
        if raw_code.startswith("```"):
            raw_code = raw_code[3:]
        if raw_code.endswith("```"):
            raw_code = raw_code[:-3]
            
        raw_code = raw_code.strip()

        # 2. Save the Physical File
        tool_path = f"neo/tools/{tool_name}.py"
        with open(tool_path, 'w', encoding='utf-8') as f:
            f.write(raw_code)
            
        print(f"  ✅ Tool '{tool_name}.py' physically forged.")

        # 3. Wire into brain.py (The dangerous part)
        brain_path = "neo/brain.py"
        if not os.path.exists(brain_path):
             return f"❌ META-CODER FAULT: '{brain_path}' not found. Cannot wire the brain."
             
        with open(brain_path, 'r', encoding='utf-8') as f:
            brain_content = f.read()

        # Check if it's already wired
        if f"import {tool_name}" in brain_content or f"{tool_name}(" in brain_content:
            return f"✅ META-CODER COMPLETE: '{tool_name}' forged, but appears already wired in brain.py."

        # Find the insertion points
        # Insert Import
        import_marker = "# Cleanly imported all filesystem tools"
        import_statement = f"from neo.tools.{tool_name} import {tool_name}\n"
        brain_content = brain_content.replace(import_marker, import_statement + import_marker)

        # Insert into TOOLS dict
        dict_marker = '"scrape_trending_topics": scrape_trending_topics,'
        dict_statement = f'{dict_marker}\n    "{tool_name}": {tool_name},'
        brain_content = brain_content.replace(dict_marker, dict_statement)

        # Insert into SYSTEM_PROMPT
        prompt_marker = 'scrape_trending_topics(output_file="trending_data.json")'
        prompt_statement = f'{prompt_marker}\n  {tool_name}(...) - Autonomously generated tool: {objective[:40]}...'
        brain_content = brain_content.replace(prompt_marker, prompt_statement)

        # Save the re-wired brain
        with open(brain_path, 'w', encoding='utf-8') as f:
            f.write(brain_content)

        return f"✅ META-CODER COMPLETE: '{tool_name}' successfully forged and wired into the central nervous system. I require a restart to load the new neural pathways."

    except Exception as e:
        return f"❌ META-CODER FAULT: Neural synthesis crashed: {str(e)}"
