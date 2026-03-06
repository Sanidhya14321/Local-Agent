from __future__ import annotations

from pathlib import Path

from core.json_utils import parse_json_from_text
from core.schemas import DebugReport
from models.deepseek_client import DeepSeekClient


class DebuggerAgent:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "debug_prompt.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def run(self, task: str, logs: str, plan: str, memory_context: str = "") -> DebugReport:
        prompt = (
            f"Task:\n{task}\n\nPlan:\n{plan}\n\n"
            f"Relevant Memory:\n{memory_context[:2500] or 'No relevant memory found.'}\n\n"
            f"Execution Logs:\n{logs[:10000]}"
        )
        fallback = {
            "root_cause": "Unable to infer root cause",
            "evidence": ["Model fallback used"],
            "fix_plan": ["Inspect failing module", "Patch syntax/runtime issue", "Re-run tests"],
            "regression_risk": "medium",
        }
        raw = await self.client.run(system_prompt=self.system_prompt, user_prompt=prompt)
        data = parse_json_from_text(raw, fallback)
        return DebugReport(**data)
