from __future__ import annotations

from core.self_improvement import SelfImprovementEngine
from tools.repo_indexer import RepoIndexer


class ContextManager:
    def __init__(self, repo_indexer: RepoIndexer, self_improvement: SelfImprovementEngine | None = None) -> None:
        self.repo_indexer = repo_indexer
        self.self_improvement = self_improvement

    def build_context(self, task: str, limit: int = 8) -> str:
        hits = self.repo_indexer.search(task, limit=limit)
        if not hits:
            return "No matching repository context found."

        chunks: list[str] = []
        for hit in hits:
            chunks.append(f"FILE: {hit['path']}\nSCORE: {hit['score']}\n{hit['preview']}")

        if self.self_improvement is not None:
            learned_patterns = self.self_improvement.code_pattern_context(task=task, limit=4)
            if learned_patterns:
                chunks.append(f"LEARNED_CODE_PATTERNS:\n{learned_patterns}")

        return "\n\n".join(chunks)
