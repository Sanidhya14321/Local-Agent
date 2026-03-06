from __future__ import annotations

from pathlib import Path

from core.json_utils import parse_json_from_text
from core.schemas import CodeProposal
from models.qwen_client import QwenClient


class CoderAgent:
    def __init__(self, client: QwenClient | None = None) -> None:
        self.client = client or QwenClient()
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "coder_prompt.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def run(
        self,
        task: str,
        plan: str,
        architecture: str,
        repo_context: str,
        previous_error: str = "",
    ) -> CodeProposal:
        prompt = (
            f"Task:\n{task}\n\nPlan:\n{plan}\n\nArchitecture:\n{architecture}\n"
            f"\nPrevious Error:\n{previous_error or 'none'}\n\nRepository Context:\n{repo_context[:9000]}"
        )

        fallback = {
            "summary": "No code proposed",
            "changes": [],
            "tests": ["python3 -m py_compile $(find . -name '*.py')"],
        }
        raw = await self.client.run(system_prompt=self.system_prompt, user_prompt=prompt)
        data = parse_json_from_text(raw, fallback)
        normalized = {
            "summary": data.get("summary", ""),
            "changes": [
                {"path": change.get("path", ""), "content": change.get("content", "")}
                for change in data.get("changes", [])
                if change.get("path")
            ],
            "tests": data.get("tests", []) or ["python3 -m py_compile $(find . -name '*.py')"],
        }
        return CodeProposal(**normalized)
