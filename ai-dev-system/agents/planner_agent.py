from __future__ import annotations

from pathlib import Path

from core.json_utils import parse_json_from_text
from core.schemas import AgentPlan
from models.deepseek_client import DeepSeekClient


class PlannerAgent:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "planner_prompt.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def run(
        self,
        task: str,
        repo_context: str,
        skills_context: str = "",
        memory_context: str = "",
        workflow_context: str = "",
    ) -> AgentPlan:
        fallback = AgentPlan(goal=task, steps=["Analyze requirements", "Implement initial version", "Validate with tests"])
        prompt = (
            f"Task:\n{task}\n\n"
            f"Skills Context:\n{skills_context[:3000] or 'No matching skills found.'}\n\n"
            f"Memory Context:\n{memory_context[:3000] or 'No relevant memory found.'}\n\n"
            f"Task Workflow Memory:\n{workflow_context[:2500] or 'No previous workflow found.'}\n\n"
            f"Repository Context:\n{repo_context[:6000]}"
        )
        response = await self.client.run(system_prompt=self.system_prompt, user_prompt=prompt)
        data = parse_json_from_text(response, fallback.model_dump())
        return AgentPlan(**data)
