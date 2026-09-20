"""
neo/tools/cold_reboot.py
========================
Cold Reboot Engine — Module Cache Phantom Fix (Linux).
Kills the Neo background processes, then relaunches the boot sequence with
`python3 run_neo.py`.

Usage:
    from neo.tools.cold_reboot import cold_reboot
    cold_reboot()  # Full reset
"""
import os
import signal
import subprocess
import time
from pathlib import Path

# Repository root: <repo>/neo/tools/cold_reboot.py -> parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]

# Background scripts spawned by start_neo.sh. Killed by name so unrelated
# python3 processes (and Neo itself) are never touched.
BACKGROUND_SCRIPTS = (
    "reddit_bounty_tracker.py",
    "telegram_router.py",
    "voice.py",
    "notification_server.py",
    "neo/tools/discord_spider.py",
)


def _protected_pids():
    """PIDs that must survive the purge: this process and its parent."""
    protected = {os.getpid(), os.getppid()}
    try:
        with open(f"/proc/{os.getpid()}/stat", "r", encoding="utf-8") as fh:
            protected.add(int(fh.read().split(") ", 1)[1].split()[1]))
    except Exception:
        pass
    return protected


def _kill_matching(pattern: str):
    """SIGKILL every process whose command line matches `pattern`.

    Returns (killed_pids, errors).
    """
    killed, errors = [], []
    protected = _protected_pids()
    try:
        found = subprocess.run(
            ["pgrep", "-f", pattern], capture_output=True, text=True, timeout=10
        )
    except FileNotFoundError:
        return [], ["pgrep not available on this system"]
    except subprocess.TimeoutExpired:
        return [], [f"timeout scanning for {pattern}"]

    for pid_str in found.stdout.split():
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        if pid in protected:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed.append(pid)
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            errors.append(str(exc))
    return killed, errors


def kill_background_processes():
    """Force-kill the Neo background scripts to clear the module cache.

    Linux port of the old Windows task-kill sweep: match by script name so
    unrelated python3 processes (and Neo itself) are never taken down.
    """
    killed, errors = [], []
    for script in BACKGROUND_SCRIPTS:
        got, errs = _kill_matching(script)
        killed.extend(got)
        errors.extend(errs)

    if errors:
        return False, f"Kill errors: {'; '.join(errors)}"
    if killed:
        return True, f"Terminated {len(killed)} background process(es): {sorted(set(killed))}"
    return True, "No Neo background processes were running."


def kill_all_neo_python_processes():
    """Hard mode: also purge any leftover `run_neo.py` session."""
    killed, errors = _kill_matching("run_neo.py")
    if errors:
        return False, f"Failed hard purge: {'; '.join(errors)}"
    return True, f"Hard purge complete ({len(killed)} run_neo process(es) killed)."


def wait_for_cleanup(seconds=3):
    """Wait for OS-level process cleanup and socket releases."""
    time.sleep(seconds)


def restart_neo():
    """Relaunch the boot sequence: detached `python3 run_neo.py`."""
    entry = REPO_ROOT / "run_neo.py"
    if not entry.exists():
        return False, f"run_neo.py not found at {entry}"

    try:
        subprocess.Popen(
            ["python3", "run_neo.py"],
            cwd=str(REPO_ROOT),
            # New session + detached stdio: the respawned Neo must not share (and
            # steal input from) the TTY of the instance that triggered the reboot.
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True, "Neo rebooting..."
    except Exception as e:
        return False, str(e)


def cold_reboot(hard=False):
    """
    Full cold reboot sequence:
    1. Kill the Neo background scripts (clears the module cache)
    2. Optionally kill leftover run_neo sessions (hard=True)
    3. Wait for OS cleanup
    4. Relaunch Neo via `python3 run_neo.py`

    Returns: (success: bool, message: str)
    """
    print("[Cold Reboot] 🔄 Initiating cold reboot sequence...", flush=True)

    # Step 1: Kill the background scripts
    ok, msg = kill_background_processes()
    print(f"[Cold Reboot] {msg}", flush=True)

    # Step 2: Optional hard purge of leftover Neo sessions
    if hard:
        ok, msg = kill_all_neo_python_processes()
        print(f"[Cold Reboot] {msg}", flush=True)

    # Step 3: Wait for cleanup
    print("[Cold Reboot] ⏳ Waiting for OS cleanup...", flush=True)
    wait_for_cleanup()

    # Step 4: Restart
    ok, msg = restart_neo()
    print(f"[Cold Reboot] {msg}", flush=True)
    return ok, "Cold reboot complete." if ok else f"Cold reboot partial: {msg}"


if __name__ == "__main__":
    import sys
    cold_reboot(hard="--hard" in sys.argv)
