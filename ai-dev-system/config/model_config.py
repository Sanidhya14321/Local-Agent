from dataclasses import dataclass

from config.settings import settings


@dataclass(frozen=True)
class ModelRoute:
    planner: str
    architect: str
    coder: str
    debugger: str
    fixer: str


MODEL_ROUTE = ModelRoute(
    planner=settings.deepseek_model,
    architect=settings.deepseek_model,
    coder=settings.qwen_model,
    debugger=settings.deepseek_model,
    fixer=settings.qwen_model,
)
