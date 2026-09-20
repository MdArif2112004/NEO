"""
neo/tools/permission.py
=======================
Permission gate for dangerous actions.
Set auto_approve=True in config.py to run fully autonomous.
"""

from neo.config import NEO_CONFIG


def ask_permission(tool_name: str, args: dict) -> bool:
    """
    Ask user permission for an action.
    Returns True = proceed, False = deny.

    To disable all permission checks:
        Set auto_approve: true in neo/config.py
    """
    # Format args for display
    args_display = "\n".join(
        f"  {k}: {str(v)[:120]}" for k, v in args.items()
    )

    print(f""")
╔══════════════════════════════════════════════════╗
║  Neo wants to: {tool_name:<34}║
╠══════════════════════════════════════════════════╣
{args_display}
╚══════════════════════════════════════════════════╝
""")

    mode = NEO_CONFIG.get("permission_mode", "ask")  # "ask" | "auto" | "deny"

    if mode == "auto":
        print("[Permission] Auto-approved ✅")
        return True

    if mode == "deny":
        print("[Permission] Auto-denied ❌")
        return False

    # mode == "ask"
    try:
        answer = input("Allow? [Y/n/a(lways)] → ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[Permission] Denied (interrupted)")
        return False

    if answer in ("a", "always"):
        # Switch to auto for rest of session
        NEO_CONFIG["permission_mode"] = "auto"
        print("[Permission] Auto-approve enabled for this session ✅")
        return True

    return answer in ("", "y", "yes")
