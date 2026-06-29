"""
neo/tools/testing.py
====================
Run Python files and pytest tests.
Neo uses this to verify code it writes.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(path: str = ".", timeout: int = 60) -> str:
    """
    Run pytest on a file or directory.
    Returns full output including pass/fail summary.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: Path not found: {path}"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(p), "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(p.parent if p.is_file() else p)
        )
        output = result.stdout + result.stderr
        status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
        return f"{status}\n\n{output[-3000:]}"  # last 3000 chars
    except subprocess.TimeoutExpired:
        return f"Error: Tests timed out after {timeout}s"
    except Exception as e:
        return f"Error running tests: {e}"


def run_file(path: str, timeout: int = 30) -> str:
    """
    Execute a Python file and return stdout + stderr.
    Neo uses this to test scripts it writes.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found: {path}"
    if p.suffix != ".py":
        return f"Error: Not a Python file: {path}"

    try:
        result = subprocess.run(
            [sys.executable, str(p)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(p.parent)
        )
        stdout = result.stdout
        stderr = result.stderr
        status = "✅ Success" if result.returncode == 0 else f"❌ Exit code {result.returncode}"
        output_parts = [status]
        if stdout:
            output_parts.append(f"STDOUT:\n{stdout[-2000:]}")
        if stderr:
            output_parts.append(f"STDERR:\n{stderr[-1000:]}")
        return "\n\n".join(output_parts)
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout}s"
    except Exception as e:
        return f"Error running file: {e}"
