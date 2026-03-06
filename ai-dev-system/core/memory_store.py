from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, root: str) -> None:
        self.path = Path(root) / ".ai_dev_memory.json"
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def append_event(self, key: str, value: Any) -> None:
        payload = self.load()
        bucket = payload.get(key, [])
        if not isinstance(bucket, list):
            bucket = []
        bucket.append(value)
        payload[key] = bucket[-100:]
        self.save(payload)
