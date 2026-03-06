from __future__ import annotations

import json
from typing import Any


def parse_json_from_text(raw_text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    text = raw_text.strip()
    if not text:
        return fallback

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return fallback

    return fallback
