import os, json, time, re
from datetime import datetime
from typing import Optional
from neo.tools.web_researcher import generate_research_report
from neo.tools.content_writer import generate_article
from neo.tools.arbitrage import execute_arbitrage_pipeline
from neo.tools.universal_ingest import run_ingestion_pipeline
from neo.tools.notion_api import push_csv_to_notion
from neo.tools.trend_scraper import scrape_trending_topics
from neo.tools.script_matrix import generate_arbitrage_scripts
from neo.tools.tts_engine import generate_voiceovers
from neo.tools.video_forge import render_shorts
from neo.tools.meta_coder import write_custom_tool
from neo.tools.clip_ingest import execute_clip_ingest
from neo.tools.deep_memory import memorize, recall

from neo.tools.compress_video import compress_video
from neo.tools.discord_bridge import discord_bridge
from neo.tools.youtube_publisher import youtube_publisher
from neo.tools.cold_reboot import cold_reboot
from neo.tools.validate_edits import validate_edits
# Cleanly imported all filesystem tools
from neo.tools.filesystem import (
    read_file, write_file, delete_file, edit_file, 
    list_files, create_file, open_website, search_web,
    ask_gemini_web, open_local_file, read_pdf,
    analyze_image, headless_osint_scrape
)
from neo.tools.notion_api import (
    create_notion_page, write_notion_content, read_notion_page, 
    read_notion_registry, update_notion_registry, create_calendar_task,
    insert_notion_db_row
)
from neo.tools.testing import run_tests, run_file
from neo.tools.screen import read_screen, capture_chatgpt
from neo.tools.permission import ask_permission
from neo.tools.error_memory import memorize_error_fix
from neo.memory.store import MemoryStore
from neo.llm.model import get_model
from neo.config import NEO_CONFIG
from neo.tools.system_audio import play_audio_cue
from neo.tools.neo_voice import speak

def read_observer_memory() -> str:
    """Reads the last 20 entries of the user's screen activity log."""
    path = "neo_core/observer_memory.json" if os.path.exists("neo_core/observer_memory.json") else "observer_memory.json"
    if not os.path.exists(path):
        return "No memory log found yet. The observer hasn't run."
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Just return the last 20 logs so we don't blow up the context window
            recent = data[-20:] 
            return json.dumps(recent, indent=2)
    except Exception as e:
        return f"Error reading memory: {e}"

# TOOLS DICTIONARY
TOOLS = {
    "read_file": read_file, 
    "write_file": write_file,
    "edit_file": edit_file, 
    "delete_file": delete_file,
    "create_file": create_file, 
    "list_files": list_files,
    "run_tests": run_tests, 
    "run_file": run_file,
    "read_screen": read_screen, 
    "capture_chatgpt": capture_chatgpt,
    "memorize_error_fix": memorize_error_fix,
    "open_website": open_website,
    "search_web": search_web, 
    "ask_gemini_web": ask_gemini_web,
    "read_observer_memory": read_observer_memory,
    "create_notion_page": create_notion_page,
    "write_notion_content": write_notion_content,
    "read_notion_page": read_notion_page,
    "read_notion_registry": read_notion_registry,
    "update_notion_registry": update_notion_registry,
    "play_audio_cue": play_audio_cue,
    "speak": speak,
    "generate_research_report": generate_research_report,
    "create_calendar_task": create_calendar_task,
    "generate_article": generate_article,
    "open_local_file": open_local_file,
    "read_pdf": read_pdf,
    "analyze_image": analyze_image,
    "insert_notion_db_row": insert_notion_db_row,
    "headless_osint_scrape": headless_osint_scrape,
    "execute_arbitrage_pipeline": execute_arbitrage_pipeline,
    "run_ingestion_pipeline": run_ingestion_pipeline,
    "push_csv_to_notion": push_csv_to_notion,
    "scrape_trending_topics": scrape_trending_topics,
    "youtube_publisher": youtube_publisher,
    "discord_bridge": discord_bridge,
    "compress_video": compress_video,
    "generate_arbitrage_scripts": generate_arbitrage_scripts,
    "generate_voiceovers": generate_voiceovers,
    "render_shorts": render_shorts,
    "write_custom_tool": write_custom_tool,
    "execute_clip_ingest": execute_clip_ingest,
    "memorize": memorize,
    "recall": recall,
    "cold_reboot": cold_reboot,
    "validate_edits": validate_edits,
}

TOOL_ALIASES = {
    "python":"create_file","write":"write_file","create":"create_file",
    "read":"read_file","delete":"delete_file","edit":"edit_file",
    "list":"list_files","run":"run_file","execute":"run_file",
    "test":"run_tests","screen":"read_screen","save_file":"write_file",
    "reboot":"cold_reboot","restart":"cold_reboot","reset":"cold_reboot",
    "validate":"validate_edits","valid8":"validate_edits","3cmd":"validate_edits","validation":"validate_edits",
    "new_file":"create_file","make_file":"create_file","open_file":"read_file",
    "browser":"open_website", "open":"open_website"
}

VALID_TOOLS = ", ".join(sorted(TOOLS.keys()))

CORE_FILES = {
    "run_neo.py", "neo/brain.py", "neo\\brain.py",
    "neo/config.py", "neo\\config.py",
    "neo/llm/model.py", "neo\\llm\\model.py",
    "neo/memory/store.py", "neo\\memory\\store.py",
    "neo/tools/permission.py", "neo\\tools\\permission.py",
    "notch.py", "observer.py"
}

SYSTEM_PROMPT = """You are Neo, an autonomous AI desktop agent and a World-Class Mentor.

PROTECTED FILES — never read, edit, run or delete these:
  run_neo.py, neo/brain.py, neo/config.py, neo/llm/model.py,
  neo/memory/store.py, neo/tools/permission.py, notch.py, observer.py

TOOLS — use ONLY these exact names:
  create_file(path, content)
  write_file(path, content)
  read_file(path)
  edit_file(path, old_text, new_text)
  delete_file(path)
  list_files(directory, pattern)
  run_file(path)
  run_tests(path)
  read_screen()
  capture_chatgpt()
  memorize_error_fix(error_snippet, solution)
  open_website(url)
  search_web(query)
  ask_gemini_web(massive_prompt)
  read_observer_memory()
  create_notion_page(title, is_frontend, parent_id)
  write_notion_content(page_id, text, block_type)
  read_notion_page(page_id)
  read_notion_registry()
  update_notion_registry(page_name, page_id, summary_of_purpose)
  read_notion_registry(query)
  play_audio_cue(cue_type)
  speak(text)
  generate_research_report(topic)
  create_calendar_task(task_name, days_from_now, database_id)
  generate_article(topic, target_audience, tone)
  open_local_file(path)
  read_pdf(path)
  analyze_image(image_path, prompt)
  insert_notion_db_row(database_id, company_name, data_dict)
  headless_osint_scrape(url)
  execute_arbitrage_pipeline(project_name, script_json)
  run_ingestion_pipeline(filepath, extraction_goal, output_csv="output.csv")
  push_csv_to_notion(csv_filepath, target_page_id)
  scrape_trending_topics(output_file="trending_data.json")
  youtube_publisher(...) - Autonomously generated tool: Upload an mp4 video to YouTube as a Shor...
  discord_bridge(...) - Autonomously generated tool: The function must accept two arguments, ...
  compress_video(...) - Autonomously generated tool: Take an input mp4 file and output a comp...
  generate_arbitrage_scripts(input_json="trending.json", output_dir="scripts") - Reads trending data and generates 60-second video scripts.
  generate_voiceovers(script_dir="scripts", audio_dir="audio") - Converts text scripts into mp3 voiceovers.
  render_shorts(audio_dir="audio", bg_video="gameplay.mp4", output_dir="renders") - Renders final YouTube Shorts.
  write_custom_tool(tool_name, objective) - Writes a Python tool, saves it, and wires it into the brain automatically.
  execute_clip_ingest(instruction="...") - Grabs the user's current clipboard text, processes it according to the instruction, and replaces the clipboard.
  memorize(text="...") - Saves important context, client workflows, or routines into long-term deep memory.
  recall(query="...") - Searches your deep memory for past context. Use this if you need to remember how to do something or retrieve past data.
  cold_reboot(hard=False) - FULL cold reboot: kills all pythonw processes, flushes RAM cache, restarts Neo via start_neo.bat. Use after editing any background scripts (telegram_router, voice, notification_server).
  validate_edits(dry_run=True) - 3-Command Validation Pass: scans Python files for syntax errors, fixes project structure, runs sanity test. Run BEFORE completing any file edits.

RESPOND WITH ONLY JSON — nothing else:
  Call tool:  {"tool":"create_file","args":{"path":"hello.py","content":"print('hello')"}}
  Finished:   {"done":true,"summary":"what was done"}
  
RULES:
- CRITICAL AUTONOMY RULE: NEVER output multiple JSON objects in one response. If the user asks for a multi-step task, output ONE tool JSON, wait for my [Observe] result, and then output the next tool JSON. Chain them autonomously step-by-step.
- One JSON object per response, no extra text
- Only use tool names listed above
- Do NOT use: python, execute, make, save
- Do NOT touch protected files
- Do NOT run run_neo.py or any core files
- IF A FILE IS MISSING OR A TASK IS IMPOSSIBLE: Do not invent new tasks or guess. Immediately abort using {"done":true, "summary":"Task failed because [reason]"}
- If a request is vague, figure out the technical steps yourself. ONLY ask the user for clarification if you have 2-3 distinct options and genuinely cannot proceed without their choice.
- If the user asks a general question or just wants to chat (e.g., "say hi", "how am I doing"), DO NOT write files. Just respond directly using {"done":true, "summary":"your reply here"}
- If the user asks to "open Chrome", "open Safari", or "open Browser", YOU MUST IMMEDIATELY use the open_website("https://google.com") tool. Do NOT explain that you cannot open desktop applications.
- THE NOTION PROTOCOL: Always run read_notion_registry() first to find the correct Page ID before reading or modifying Notion. If you create a new Notion page, you MUST immediately run update_notion_registry() to log its ID and purpose so you don't forget it.
- FRONTEND PURITY: You must NEVER create temporary, unformatted, or research pages in ARIF OS (Frontend). ARIF OS is strictly for beautiful, final, human-readable dashboards. All messy data, logs, databases, and raw research MUST be built inside NEO CONTROL (Backend).
- AUDIO PROTOCOL: You must run play_audio_cue('success') as your very last action when you successfully complete a multi-step user request. Run play_audio_cue('alert') if you hit a roadblock and need the user to look at the screen.
- VOCAL PROTOCOL: If the user explicitly asks you to "say", "speak", or "talk", you MUST use the speak(text) tool to deliver your response out loud. Keep spoken responses concise and conversational.

HARDENED RULES — Never violate these:
- COLD REBOOT PROTOCOL: After editing ANY background script (telegram_router.py, voice.py, notification_server.py), you MUST run cold_reboot() to kill pythonw processes, flush the module cache, and restart the boot sequence.
- DIRECT ENDPOINT MANDATE: capture_chatgpt() is DEPRECATED. Never use UI scraping — always use direct API endpoints (ask_gemini_web, generate_research_report, or get_model().chat()).
- SUBPROCESS QA GATE: run_file() on any script containing "import os" OR "import sys" requires human authorization — always gate through permission.py.
- 3-COMMAND VALIDATION PASS: Before completing any file edits, run validate_edits() to check for syntax errors, stale .bak files, missing __init__.py markers, and versioned duplicates (v1_, v2_ patterns).
- INLINE VERSIONING: Never create v1_brain.py, v2_brain.py, or similar versioned duplicates. Apply all changes incrementally within the primary file.
"""

class NeoBrain:
    def __init__(self):
        print("🔥 NEO LOADED")
        self.llm    = get_model()
        self.memory = MemoryStore()
        self.config = NEO_CONFIG

    def run(self, task: str, max_steps: int = 1000) -> str:
        print(f"\n{'='*60}\n[Neo] Task: {task}\n[Neo] {datetime.now().strftime('%H:%M:%S')}\n{'='*60}\n")
        messages = [{"role":"user","content":f"Task: {task}"}]
        self.memory.add("task_start", {"task":task,"time":time.time()})

        for step in range(1, max_steps+1):
            time.sleep(4)
            print(f"── Step {step} {'─'*40}")
            response = self.llm.chat(SYSTEM_PROMPT, messages)
            print(f"[Think] {response[:300]}")
            action = self._parse(response)

            if action is None:
                messages.append({"role":"assistant","content":response})
                messages.append({"role":"user","content":
                    f'ERROR: not valid JSON. Respond ONLY with: {{"tool":"TOOLNAME","args":{{...}}}}\nValid tools: {VALID_TOOLS}'})
                continue

            if action.get("done"):
                summary = action.get("summary","Done.")
                print(f"\n[Neo] ✅ {summary}")
                self.memory.add("task_done",{"summary":summary})
                return summary

            tool_name = self._resolve(action.get("tool",""))
            args      = self._fix_args(tool_name, action.get("args",{}))
            if not isinstance(args, dict): args = {} # Prevent LLM list hallucination crashes

            # Block access to core files
            path = args.get("path","")
            if path in CORE_FILES or any(path.endswith(c.replace("neo\\","").replace("neo/","")) for c in CORE_FILES):
                messages.append({"role":"assistant","content":response})
                messages.append({"role":"user","content":
                    f"BLOCKED: '{path}' is a protected core file. Work on other files only."})
                continue

            if tool_name not in TOOLS:
                messages.append({"role":"assistant","content":response})
                messages.append({"role":"user","content":
                    f"ERROR: '{tool_name}' is not valid. Use one of: {VALID_TOOLS}\n"
                    f'Example: {{"tool":"create_file","args":{{"path":"hello.py","content":"print(\'hello\')"}}}}'})
                continue

            if not self._permitted(tool_name, args):
                messages.append({"role":"assistant","content":response})
                messages.append({"role":"user","content":f"Permission denied for {tool_name}."})
                continue

            print(f"[Act] {tool_name}({str(args)[:120]})")
            obs = self._call(tool_name, args)
            print(f"[Observe] {str(obs)[:300]}")
            self.memory.add(f"step_{step}",{"tool":tool_name,"result":str(obs)[:200]})
            messages.append({"role":"assistant","content":response})
            messages.append({"role":"user","content":f"Result: {obs}\n\nNext step?"})

        return "[Neo] Max steps reached."

    def _resolve(self, name):
        if name in TOOLS: return name
        resolved = TOOL_ALIASES.get(name.lower(), name)
        if resolved != name: print(f"[Neo] 🔀 {name} → {resolved}")
        return resolved

    def _fix_args(self, tool, args):
        if tool in ("create_file","write_file"):
            for a in ("code","text","body","data"):
                if a in args and "content" not in args:
                    args["content"] = args.pop(a)
            for a in ("filename","file","name"):
                if a in args and "path" not in args:
                    args["path"] = args.pop(a)
        return args

    def _parse(self, text):
        text = text.strip()
        
        # 1. Strip raw markdown code fences immediately
        text = text.replace("```json", "").replace("```", "").strip()
        
        # 2. Strict JSON parsing attempt
        try: 
            return json.loads(text)
        except: 
            pass
        
        # 3. Ruthless Fallback: Regex extraction strategy to slice away human conversational fluff
        # Captures everything between the outermost curly braces inclusive
        json_pattern = r'(\{.*?\})'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for potential_json in reversed(matches):  # Check from most specific backwards
            try: 
                return json.loads(potential_json)
            except: 
                continue
                
        return None
    
    def _permitted(self, tool, args):
        # Auto-mode bypasses all permission checks
        if self.config.get("permission_mode") == "auto":
            return True

        dangerous = self.config.get("require_permission_for",
                                    ["delete_file","write_file","run_file"])

        # SUBPROCESS QA GATE: If running a file, scan it for dangerous imports
        if tool == "run_file":
            path = args.get("path", "")
            if path and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    # Block scripts containing import os or import sys from auto-execution
                    dangerous_imports = []
                    if "import os" in content and "import sys" in content:
                        dangerous_imports = ["os", "sys"]
                    elif "import os" in content:
                        dangerous_imports = ["os"]
                    elif "import sys" in content:
                        dangerous_imports = ["sys"]

                    if dangerous_imports:
                        imports_str = " and ".join(dangerous_imports)
                        reason = f"Script '{path}' contains import {imports_str} — requires human authorization."
                        print(f"[QA Gate] 🔒 {reason}")
                        return ask_permission(tool, {**args, "_qa_reason": reason})
                except Exception:
                    pass  # If we can't read it, let the normal permission flow handle it

        if tool in dangerous:
            return ask_permission(tool, args)

        return True

    def _call(self, tool, args):
        """Executes a tool with a 3-strike retry engine and Error Memory lookup."""
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                r = TOOLS[tool](**args)
                
                if isinstance(r, str) and r.startswith("Error:"):
                    raise Exception(r)
                    
                return r if r is not None else "✅ Done."
                
            except TypeError as e:
                import inspect
                sig = inspect.signature(TOOLS[tool])
                last_error = f"Wrong args for {tool}. Expected: {sig}. Got: {list(args.keys())}. {e}"
                args = self._fix_args(tool, args) 
                
            except Exception as e:
                last_error = str(e)
                error_type = self._extract_import_error(last_error)
                
                if (error_type == "missing_file" or "File not found" in last_error) and "path" in args:
                    found_path = self._find_file(os.path.basename(args["path"]))
                    if found_path:
                        args["path"] = found_path
                        continue
                
            print(f"  [Retry Engine] Tool '{tool}' failed (Attempt {attempt+1}/{max_retries}). Retrying...")

        # --- ERROR MEMORY LOOKUP ---
        hint = ""
        try:
            if os.path.exists("neo/memory/error_fixes.json"):
                with open("neo/memory/error_fixes.json", "r") as f:
                    fixes = json.load(f)
                    for snippet, solution in fixes.items():
                        if snippet in last_error:
                            hint = f"\n\n💡 [SYSTEM HINT from Past Memory]: The last time this happened, the fix was: {solution}"
        except Exception:
            pass

        return f"❌ Action failed after {max_retries} attempts. Last error: {last_error}{hint}"

    def _find_file(self, filename: str) -> str:
        for root, _, files in os.walk("."):
            if ".neo_trash" in root or "__pycache__" in root:
                continue
            if filename in files:
                return os.path.relpath(os.path.join(root, filename), ".")
        return ""

    def _extract_import_error(self, error_text: str) -> str:
        if "ModuleNotFoundError" in error_text:
            return "missing_module"
        if "ImportError" in error_text:
            return "import_error"
        if "FileNotFoundError" in error_text:
            return "missing_file"
        return "general_error"

def run(task: str, max_steps: int = 1000) -> str:
    """Module-level entry for Discord C&C and external integrations."""
    return NeoBrain().run(task, max_steps=max_steps)

if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or input("Task: ")
    NeoBrain().run(task)
