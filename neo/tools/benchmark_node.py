"""
neo/tools/benchmark_node.py
===========================
Enterprise LLM Benchmarking & Evaluation Node.
Pings Groq to generate structured logic sheets for human auditing.
RAM Constraint: 8GB Optimized. Zero-capital runtime.
"""
import os
from groq import Groq

INPUT_FILE = "prompt.txt"
OUTPUT_FILE = "evaluation_output.md"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def execute_benchmark():
    print("\n🔬 [BENCHMARK] Initializing evaluation pipeline...")
    
    if not GROQ_API_KEY:
        print("❌ [SYSTEM FAULT] GROQ_API_KEY environment variable is missing.")
        return

    if not os.path.exists(INPUT_FILE):
        print(f"❌ [SYSTEM FAULT] Target file '{INPUT_FILE}' not found. Please create it in the root directory.")
        return

    # Read the prompt context from disk
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_prompt = f.read().strip()

    if not raw_prompt:
        print("⚠️ [BENCHMARK] Warning: 'prompt.txt' is empty. Terminating cycle.")
        return

    client = Groq(api_key=GROQ_API_KEY)

    # Inject strict template layout formatting constraints into the model system instructions
    system_instruction = (
        "You are an elite, enterprise-grade Code Auditor and Logic Engine. "
        "Analyze the user's input deeply and format your output strictly using these three Markdown headers:\n"
        "# Logic Breakdown\n"
        "[Provide your comprehensive structural evaluation here]\n\n"
        "# Code Output\n"
        "[Provide complete, clean, optimized code solutions here]\n\n"
        "# Edge Cases\n"
        "[Identify structural failure states, memory bounds, or validation vulnerabilities here]"
    )

    print("📡 [BENCHMARK] Routing payload to Groq (Llama-3.3-70B)...")

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": raw_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.1,  # Low temperature to force predictable, rigorous evaluation logic
            max_tokens=3000
        )
        
        evaluation_payload = response.choices[0].message.content.strip()
        
        # Write output payload directly to markdown ledger
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(evaluation_payload)
            
        print(f"✅ [CYCLE COMPLETE] Structured evaluation compiled successfully in: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ [SYSTEM FAULT] Pipeline collapse during model invocation: {str(e)}")

if __name__ == "__main__":
    execute_benchmark()
