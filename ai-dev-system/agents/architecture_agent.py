from __future__ import annotations

from models.deepseek_client import DeepSeekClient


class ArchitectureAgent:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()

    async def run(self, task: str, plan_text: str) -> dict[str, list[str]]:
        system_prompt = (
            "You are an Architecture Agent. Return JSON only with keys: "
            "backend, frontend, infrastructure, data_flow."
        )
        user_prompt = f"Task:\n{task}\n\nPlan:\n{plan_text}"
        raw = await self.client.run(system_prompt=system_prompt, user_prompt=user_prompt)

        from core.json_utils import parse_json_from_text

        fallback = {
            "backend": ["FastAPI modular service"],
            "frontend": ["Next.js modular UI"],
            "infrastructure": ["MCP server + Ollama local runtime"],
            "data_flow": ["VSCode Extension -> MCP -> Agents -> Tools"],
        }
        return parse_json_from_text(raw, fallback)
