"""
neo/memory/store.py
===================
Lightweight session memory for Neo.
Stores step history as JSON. SQLite/vector coming later.
"""

import json
import time
from pathlib import Path
from datetime import datetime


class MemoryStore:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.memory_dir  = Path.home() / ".neo" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.memory_dir / f"session_{self.session_id}.json"
        self.steps = []
        print(f"[Memory] Session: {self.session_id}")

    def add(self, key: str, value: dict):
        """Store a memory step."""
        entry = {
            "key":       key,
            "value":     value,
            "timestamp": time.time()
        }
        self.steps.append(entry)
        self._save()

    def get_recent(self, n: int = 10) -> list:
        """Return last n memory entries."""
        return self.steps[-n:]

    def get_all(self) -> list:
        return self.steps

    def _save(self):
        """Persist session to disk."""
        try:
            self.session_file.write_text(
                json.dumps(self.steps, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass  # Memory write failure should never crash the agent

    def summary(self) -> str:
        """Return a readable summary of this session."""
        lines = []
        for s in self.steps:
            lines.append(f"[{s['key']}] {json.dumps(s['value'])[:100]}")
        return "\n".join(lines) if lines else "No memory yet."
