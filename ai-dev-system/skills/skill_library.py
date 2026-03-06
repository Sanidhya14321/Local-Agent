from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    name: str
    description: str
    steps: list[str]
    dependencies: list[str]
    files_generated: list[str]
    code_templates: list[str]


class SkillLibrary:
    def __init__(self, skills_file: str) -> None:
        self.skills_file = Path(skills_file)
        self.skills: list[Skill] = self._load()

    def _load(self) -> list[Skill]:
        raw = json.loads(self.skills_file.read_text(encoding="utf-8"))
        return [Skill(**item) for item in raw]

    def as_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "steps": s.steps,
                "dependencies": s.dependencies,
                "files_generated": s.files_generated,
                "code_templates": s.code_templates,
            }
            for s in self.skills
        ]

    def find_relevant(self, task: str, limit: int = 4) -> list[Skill]:
        terms = {t for t in task.lower().split() if len(t) > 2}
        scored: list[tuple[int, Skill]] = []

        for skill in self.skills:
            haystack = (
                f"{skill.name} {skill.description} "
                + " ".join(skill.steps)
                + " "
                + " ".join(skill.dependencies)
            ).lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda item: item[0], reverse=True)
        if scored:
            return [skill for _, skill in scored[:limit]]
        return self.skills[: min(limit, len(self.skills))]
