from __future__ import annotations

from pathlib import Path

from core.json_utils import parse_json_from_text
from models.deepseek_client import DeepSeekClient


class ReflectionAgent:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "reflection_prompt.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def run(self, task: str, logs: list[str], status: str, changed_files: list[str], last_error: str) -> dict:
        payload = (
            f"Task:\n{task}\n\nStatus:\n{status}\n\nChanged Files:\n{changed_files}\n"
            f"\nLast Error:\n{last_error[:6000]}\n\nExecution Logs:\n" + "\n".join(logs[-120:])
        )
        fallback = {
            "errors_encountered": [last_error[:400]] if last_error else [],
            "successful_strategies": ["Iterative code/test/fix loop"],
            "reusable_solutions": ["Reuse modular route/service split for backend tasks"],
            "workflow_steps": [
                "Gather context",
                "Plan architecture",
                "Generate code",
                "Run checks",
                "Apply fix loop",
            ],
        }
        raw = await self.client.run(system_prompt=self.system_prompt, user_prompt=payload)
        return parse_json_from_text(raw, fallback)
