from __future__ import annotations

from pathlib import Path

from core.json_utils import parse_json_from_text
from core.schemas import CodeProposal
from models.qwen_client import QwenClient


class FixAgent:
    def __init__(self, client: QwenClient | None = None) -> None:
        self.client = client or QwenClient()
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "fix_prompt.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def run(self, task: str, debug_report: str, repo_context: str) -> CodeProposal:
        prompt = f"Task:\n{task}\n\nDebug Report:\n{debug_report}\n\nRepository Context:\n{repo_context[:9000]}"
        fallback = {"summary": "No fix generated", "patches": [], "post_fix_checks": ["pytest -q"]}
        raw = await self.client.run(system_prompt=self.system_prompt, user_prompt=prompt)
        data = parse_json_from_text(raw, fallback)

        patches = data.get("patches", [])
        normalized = {
            "summary": data.get("summary", ""),
            "changes": [
                {"path": patch.get("path", ""), "content": patch.get("content", "")}
                for patch in patches
                if patch.get("path")
            ],
            "tests": data.get("post_fix_checks", []) or ["pytest -q"],
        }
        return CodeProposal(**normalized)
