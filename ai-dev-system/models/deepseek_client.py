from config.model_config import MODEL_ROUTE
from models.ollama_client import OllamaClient


class DeepSeekClient:
    def __init__(self, ollama_client: OllamaClient | None = None) -> None:
        self.ollama_client = ollama_client or OllamaClient()
        self.model = MODEL_ROUTE.planner

    async def run(self, system_prompt: str, user_prompt: str) -> str:
        return await self.ollama_client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
