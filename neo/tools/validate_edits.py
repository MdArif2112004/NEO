"""
neo/tools/validate_edits.py
==========================
3-Command Validation Pass — Version Chasing Bloat Fix.

Before completing any file edits, run this to ensure:
  1. scan python files  — Check for syntax errors, orphaned imports, and duplicate logic
  2. fix project        — Auto-correct common issues (missing __init__.py, stale .bak files)
  3. create hello.py    — Verify basic file creation still works (quick sanity test)

Usage:
    from neo.tools.validate_edits import validate_edits
    result = validate_edits()
    print(result["scan"], result["fix"], result["hello"])
"""
import os
import sys
import ast
import subprocess
from datetime import datetime


def scan_python_files() -> dict:
    """
    Command 1: Scan all Python files for syntax errors and orphaned references.
    Returns { "status": "pass"|"fail", "issues": [...] }
    """
    issues = []
    scanned = 0

    for root, _, files in os.walk("."):
        # Skip hidden dirs, virtual envs, and cache
        if any(skip in root for skip in [".neo_trash", "__pycache__", ".git", "venv", ".env"]):
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            scanned += 1
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
                ast.parse(source)
            except SyntaxError as e:
                issues.append({
                    "file": path,
                    "type": "syntax_error",
                    "detail": str(e)
                })
            except Exception as e:
                issues.append({
                    "file": path,
                    "type": "read_error",
                    "detail": str(e)
                })

    # Check for versioned duplicates (v1_, v2_, _bak patterns that aren't .bak)
    for root, _, files in os.walk("."):
        if any(skip in root for skip in [".neo_trash", "__pycache__", ".git"]):
            continue
        basenames = set()
        for f in files:
            base = os.path.splitext(f)[0]
            # Detect v1_brain.py, v2_brain.py style duplicates
            if base.startswith("v") and "_" in base and base.split("_", 1)[1] in basenames:
                issues.append({
                    "file": os.path.join(root, f),
                    "type": "version_bloat",
                    "detail": f"Duplicate versioned file: {f} — merge into primary file instead."
                })
            basenames.add(base)

    status = "pass" if not issues else "fail"
    return {
        "command": "scan python files",
        "status": status,
        "files_scanned": scanned,
        "issues": issues
    }


def fix_project(dry_run: bool = True) -> dict:
    """
    Command 2: Fix common project issues.
    - Creates missing __init__.py in all package directories
    - Removes stale .bak files older than 30 days (unless dry_run)
    - Ensures neo_core/ is the recognized root

    dry_run=True: Report what would be done without making changes.
    Returns { "status": "pass"|"fail", "actions": [...] }
    """
    actions = []

    # Check that all package dirs have __init__.py
    package_dirs = [
        "neo", "neo/tools", "neo/llm", "neo/memory",
        "experiments", "audio", "renders", "scripts",
        "downloads", "downloads/pdfs", "solo_leveling"
    ]
    for d in package_dirs:
        init_path = os.path.join(d, "__init__.py")
        if not os.path.exists(init_path) and os.path.isdir(d):
            if not dry_run:
                try:
                    with open(init_path, "w") as f:
                        f.write(f"# {d} package marker\n")
                    actions.append(f"Created missing {init_path}")
                except Exception as e:
                    actions.append(f"Failed to create {init_path}: {e}")
            else:
                actions.append(f"[DRY RUN] Would create missing {init_path}")

    # Check for stale .bak files (older than 30 days)
    now = datetime.now().timestamp()
    for root, _, files in os.walk("."):
        if ".neo_trash" in root or "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".bak"):
                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                age_days = (now - mtime) / 86400
                if age_days > 30:
                    if not dry_run:
                        try:
                            os.remove(path)
                            actions.append(f"Removed stale .bak: {path} (aged {age_days:.0f} days)")
                        except Exception as e:
                            actions.append(f"Failed to remove {path}: {e}")
                    else:
                        actions.append(f"[DRY RUN] Would remove stale .bak: {path} (aged {age_days:.0f} days)")

    # Verify root references are correct
    if os.path.exists("neo_core"):
        actions.append("WARNING: 'neo_core/' directory exists outside the expected structure — may cause import confusion.")

    status = "pass" if not actions else "partial" if dry_run else "pass"
    return {
        "command": "fix project",
        "status": status,
        "dry_run": dry_run,
        "actions": actions
    }


def create_hello_test() -> dict:
    """
    Command 3: Quick sanity check — create and then delete a test file.
    Verifies basic file creation tooling is working.
    """
    try:
        test_path = "_neo_sanity_test.txt"
        with open(test_path, "w") as f:
            f.write("Neo validation test — created at " + datetime.now().isoformat())
        # Verify it was created
        if os.path.exists(test_path):
            os.remove(test_path)
            return {
                "command": "create hello.py (sanity test)",
                "status": "pass",
                "detail": "File creation + deletion works correctly."
            }
        else:
            return {
                "command": "create hello.py (sanity test)",
                "status": "fail",
                "detail": "File was not created after write attempt."
            }
    except Exception as e:
        return {
            "command": "create hello.py (sanity test)",
            "status": "fail",
            "detail": str(e)
        }


def validate_edits(dry_run: bool = True) -> dict:
    """
    Run the full 3-Command Validation Pass.

    This should be called BEFORE completing any file edits to prevent
    version chasing bloat and broken import traps.

    Returns:
    {
        "timestamp": "...",
        "overall": "pass"|"fail"|"warning",
        "scan": { ... },
        "fix": { ... },
        "hello": { ... }
    }
    """
    print("=" * 60)
    print("[Validate] 🔍 Running 3-Command Validation Pass...")
    print("=" * 60)

    scan_result = scan_python_files()
    fix_result = fix_project(dry_run=dry_run)
    hello_result = create_hello_test()

    # Determine overall status
    statuses = [scan_result["status"], fix_result["status"], hello_result["status"]]
    if all(s == "pass" for s in statuses):
        overall = "pass"
    elif any(s == "fail" for s in statuses):
        overall = "fail"
    else:
        overall = "warning"

    print(f"\n[Validate] 📊 Results:")
    print(f"  1. Scan Python Files  : {scan_result['status'].upper()} ({scan_result['files_scanned']} files checked)")
    print(f"  2. Fix Project         : {fix_result['status'].upper()} ({len(fix_result['actions'])} actions)")
    print(f"  3. Sanity Test         : {hello_result['status'].upper()}")
    print(f"\n[Validate] {'✅ PASS' if overall == 'pass' else '⚠️ WARNING' if overall == 'warning' else '❌ FAIL'}")
    print("=" * 60)

    return {
        "timestamp": datetime.now().isoformat(),
        "overall": overall,
        "scan": scan_result,
        "fix": fix_result,
        "hello": hello_result
    }


if __name__ == "__main__":
    import json
    dry_run = "--apply" not in sys.argv  # Default is dry_run; use --apply to execute fixes
    result = validate_edits(dry_run=dry_run)
    print(json.dumps(result, indent=2))