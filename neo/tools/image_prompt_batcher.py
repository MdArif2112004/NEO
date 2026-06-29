"""
image_prompt_batcher.py — NEO Media Pipeline (priority #1)
Script .txt -> numbered Ideogram image prompts, each prefixed with the locked
art-style prefix. Output: media/assets/<video_id>/prompts.txt (paste-ready).

Dependencies: groq, python-dotenv
Install: pip install groq python-dotenv
Run: python neo/tools/image_prompt_batcher.py <script.txt> <video_id> [num_scenes]

RAM: negligible (Groq is HTTP, no local model). 8GB-safe.
Locked style prefix: reads media/character_ref/style_prefix.txt if present.
Paste that file once with your Ideogram art-style prefix; every prompt inherits it.
"""

import os
import re
import sys
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from groq import Groq
except ImportError:
    Groq = None

GROQ_MODEL        = "openai/gpt-oss-120b"
MEDIA_ROOT        = Path("media")
STYLE_PREFIX_FILE = MEDIA_ROOT / "character_ref" / "style_prefix.txt"

# ── Style prefix ────────────────────────────────────────────────────────────

def load_style_prefix() -> str:
    if STYLE_PREFIX_FILE.exists():
        p = STYLE_PREFIX_FILE.read_text(encoding="utf-8").strip()
        if p:
            return p
    print(f"⚠️  No style prefix found at {STYLE_PREFIX_FILE}")
    print("    Prompts will have NO locked art style. Create that file with your "
          "Ideogram prefix and re-run for consistent characters.\n")
    return ""

# ── Generate ──────────────────────────────────────────────────────────────────

def generate_prompts(script: str, num_scenes: int | None = None) -> list[str]:
    if Groq is None or not os.getenv("GROQ_API_KEY"):
        raise EnvironmentError("Needs `pip install groq` + GROQ_API_KEY in .env")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    target = f"exactly {num_scenes}" if num_scenes else "an appropriate number of (roughly one per beat)"
    sys_prompt = (
        "You are a storyboard director for short-form video. Break the script into "
        f"{target} visual scenes. For EACH scene write ONE vivid image-generation prompt: "
        "subject, setting, action, mood, lighting, color, composition. Concrete and visual. "
        "Do NOT include camera/lens jargon, scene numbers, or narration text. "
        "Return ONLY a JSON array of prompt strings. No markdown, no prose."
    )
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": sys_prompt},
                  {"role": "user", "content": script}],
        temperature=0.7, max_tokens=2500,
        reasoning_effort="low",
    )
    raw = resp.choices[0].message.content.strip()
    # Extract the JSON array even if the model adds preamble or markdown fences
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array in model output: {raw[:200]}")
    prompts = json.loads(raw[start:end + 1])
    if not isinstance(prompts, list):
        raise ValueError("Model did not return a JSON array")
    return [str(p).strip() for p in prompts if str(p).strip()]

# ── Save ────────────────────────────────────────────────────────────────────

def save(video_id: str, prompts: list[str], prefix: str) -> Path:
    out_dir = MEDIA_ROOT / "assets" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # paste-ready: one full prompt per block, no numbering inside the prompt
    blocks = []
    for p in prompts:
        full = f"{prefix}, {p}" if prefix else p
        blocks.append(full)
    out_file = out_dir / "prompts.txt"
    out_file.write_text("\n\n".join(blocks), encoding="utf-8")

    # numbered reference for tracking which scene is which
    ref = [f"{i}. {b}" for i, b in enumerate(blocks, 1)]
    (out_dir / "prompts_numbered.txt").write_text("\n\n".join(ref), encoding="utf-8")
    return out_file

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python image_prompt_batcher.py <script.txt> <video_id> [num_scenes]")
        sys.exit(1)

    script_path = Path(sys.argv[1])
    video_id    = sys.argv[2]
    num_scenes  = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not script_path.exists():
        print(f"Script not found: {script_path}")
        sys.exit(1)

    script = script_path.read_text(encoding="utf-8").strip()
    if not script:
        print("Script file is empty.")
        sys.exit(1)

    prefix = load_style_prefix()
    print(f"Generating prompts for '{video_id}' from {script_path.name}...")
    try:
        prompts = generate_prompts(script, num_scenes)
    except Exception as e:
        print(f"Generation failed: {e}")
        sys.exit(1)

    out_file = save(video_id, prompts, prefix)

    print(f"\n✅ {len(prompts)} prompts -> {out_file}")
    print(f"   Numbered reference -> {out_file.parent / 'prompts_numbered.txt'}\n")
    for i, p in enumerate(prompts, 1):
        preview = (prefix + ", " if prefix else "") + p
        print(f"{i}. {preview[:110]}{'...' if len(preview) > 110 else ''}")


if __name__ == "__main__":
    main()
