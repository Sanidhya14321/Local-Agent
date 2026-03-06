from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.schemas import RunRecord
from memory.learning_memory import LearningMemory
from skills.skill_library import Skill, SkillLibrary


class SelfImprovementEngine:
    def __init__(
        self,
        workspace_root: str,
        persist_directory: str | None = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        root = Path(workspace_root)
        skills_file = root / "skills" / "default_skills.json"
        memory_dir = Path(persist_directory) if persist_directory else root / ".ai_learning_memory"
        if not memory_dir.is_absolute():
            memory_dir = root / memory_dir

        self.skill_library = SkillLibrary(str(skills_file))
        self.learning_memory = LearningMemory(str(memory_dir), embedding_model=embedding_model)
        self._seed_skills()

    def _seed_skills(self) -> None:
        for skill in self.skill_library.as_dicts():
            self.learning_memory.add_skill(skill_name=skill["name"], description=skill["description"], payload=skill)

    def index_repository(self, workspace_root: str) -> int:
        return self.learning_memory.index_repository(workspace_root)

    def relevant_skills(self, task: str, limit: int = 4) -> list[Skill]:
        return self.skill_library.find_relevant(task=task, limit=limit)

    def skills_context(self, task: str, limit: int = 4) -> str:
        skills = self.relevant_skills(task=task, limit=limit)
        chunks: list[str] = []
        for skill in skills:
            chunks.append(
                json.dumps(
                    {
                        "name": skill.name,
                        "description": skill.description,
                        "steps": skill.steps,
                        "dependencies": skill.dependencies,
                        "files_generated": skill.files_generated,
                    },
                    ensure_ascii=True,
                )
            )
        return "\n".join(chunks)

    def memory_context(self, task: str, limit: int = 3) -> str:
        buckets = ["bug_memory", "architecture_memory", "solution_memory"]
        chunks: list[str] = []
        for bucket in buckets:
            hits = self.learning_memory.query_memory(bucket, query=task, limit=limit)
            if hits:
                joined = "\n".join(item.get("text", "")[:600] for item in hits)
                chunks.append(f"{bucket}:\n{joined}")
        return "\n\n".join(chunks)

    def workflow_context(self, task: str, limit: int = 3) -> str:
        hits = self.learning_memory.retrieve_task_workflows(query=task, limit=limit)
        return "\n".join(item.get("text", "") for item in hits)

    def code_pattern_context(self, task: str, limit: int = 4) -> str:
        hits = self.learning_memory.query_codebase(query=task, limit=limit)
        return "\n\n".join(item.get("text", "")[:1200] for item in hits)

    def store_reflection(self, record: RunRecord, reflection: dict[str, Any]) -> None:
        for error in reflection.get("errors_encountered", []):
            if error:
                self.learning_memory.add_memory(
                    "bug_memory",
                    text=str(error),
                    metadata={"task": record.task, "status": record.status.value},
                )

        for strategy in reflection.get("successful_strategies", []):
            if strategy:
                self.learning_memory.add_memory(
                    "solution_memory",
                    text=str(strategy),
                    metadata={"task": record.task, "status": record.status.value},
                )

        if record.architecture:
            self.learning_memory.add_memory(
                "architecture_memory",
                text=json.dumps(record.architecture, ensure_ascii=True),
                metadata={"task": record.task, "status": record.status.value},
            )

        for solution in reflection.get("reusable_solutions", []):
            if solution:
                self.learning_memory.add_memory(
                    "code_patterns",
                    text=str(solution),
                    metadata={"task": record.task, "status": record.status.value, "kind": "reusable_solution"},
                )

        self.learning_memory.store_task_workflow(
            task=record.task,
            steps=reflection.get("workflow_steps", []),
            outcome=record.status.value,
            notes="; ".join(reflection.get("successful_strategies", [])[:3]),
        )
