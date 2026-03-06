from dataclasses import dataclass


@dataclass
class ProjectBlueprint:
    name: str
    backend_stack: str
    frontend_stack: str


class ProjectService:
    def build_blueprint(self, name: str) -> ProjectBlueprint:
        return ProjectBlueprint(
            name=name,
            backend_stack="FastAPI + Pydantic + service layer",
            frontend_stack="Next.js + TypeScript + Tailwind",
        )
