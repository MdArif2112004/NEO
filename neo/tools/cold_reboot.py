"""
neo/tools/cold_reboot.py
========================
Cold Reboot Engine — Module Cache Phantom Fix.
Kills all pythonw background processes, flushes RAM cache,
and restarts the Neo boot sequence via start_neo.bat.

Usage:
    from neo.tools.cold_reboot import cold_reboot
    cold_reboot()  # Full reset
"""
import os
import sys
import time
import subprocess
import signal


def kill_pythonw_processes():
    """Force-kill all pythonw.exe processes to clear RAM cache."""
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "pythonw.exe"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        if "successfully" in output.lower():
            return True, "All pythonw processes terminated."
        elif "not found" in output.lower():
            return True, "No pythonw processes were running."
        else:
            return True, output.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout while killing pythonw processes."
    except Exception as e:
        return False, str(e)


def kill_all_neo_python_processes():
    """Also kill any python.exe processes that might be holding Neo modules."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe", "/T"],
            capture_output=True, text=True, timeout=10
        )
        return True, "Done."
    except Exception:
        return False, "Failed to kill python processes."


def wait_for_cleanup(seconds=3):
    """Wait for OS-level process cleanup and socket releases."""
    time.sleep(seconds)


def restart_neo():
    """Launch start_neo.bat to restart the full boot sequence."""
    bat_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "start_neo.bat")
    if not os.path.exists(bat_path):
        bat_path = os.path.join(os.getcwd(), "start_neo.bat")
    if not os.path.exists(bat_path):
        return False, f"start_neo.bat not found at {bat_path}"

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", bat_path],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return True, "Neo rebooting..."
    except Exception as e:
        return False, str(e)


def cold_reboot(hard=False):
    """
    Full cold reboot sequence:
    1. Kill all pythonw processes (clears module cache)
    2. Optionally kill all python processes (hard=True)
    3. Wait for OS cleanup
    4. Restart Neo via start_neo.bat

    Returns: (success: bool, message: str)
    """
    print("[Cold Reboot] 🔄 Initiating cold reboot sequence...", flush=True)

    # Step 1: Kill pythonw
    ok, msg = kill_pythonw_processes()
    print(f"[Cold Reboot] {msg}", flush=True)

    # Step 2: Optional hard kill of all python
    if hard:
        kill_all_neo_python_processes()

    # Step 3: Wait for cleanup
    print("[Cold Reboot] ⏳ Waiting for OS cleanup...", flush=True)
    wait_for_cleanup()

    # Step 4: Restart
    ok, msg = restart_neo()
    print(f"[Cold Reboot] {msg}", flush=True)
    return ok, "Cold reboot complete." if ok else f"Cold reboot partial: {msg}"


if __name__ == "__main__":
    import sys
    hard = "--hard" in sys.argv
    cold_reboot(hard=hard)