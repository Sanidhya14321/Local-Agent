import asyncio

from config.settings import settings
from config.model_config import MODEL_ROUTE
from models.ollama_client import OllamaClient


class DeepSeekClient:
    def __init__(self, ollama_client: OllamaClient | None = None) -> None:
        self.ollama_client = ollama_client or OllamaClient()
        self.model = MODEL_ROUTE.planner
        self.timeout_seconds = settings.llm_call_timeout_seconds

    async def run(self, system_prompt: str, user_prompt: str) -> str:
        try:
            return await asyncio.wait_for(
                self.ollama_client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                ),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise TimeoutError(
                f"DeepSeek model call timed out after {self.timeout_seconds}s"
            ) from exc
