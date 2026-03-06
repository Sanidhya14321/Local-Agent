from __future__ import annotations

from pathlib import Path


class RepoIndexer:
    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = Path(workspace_root)

    def _iter_files(self) -> list[Path]:
        ignored = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".venv"}
        paths: list[Path] = []
        for path in self.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignored for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yml", ".yaml"}:
                continue
            paths.append(path)
        return paths

    def search(self, query: str, limit: int = 8) -> list[dict[str, str]]:
        terms = [t for t in query.lower().split() if len(t) > 2]
        scores: list[tuple[int, Path]] = []

        for path in self._iter_files():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            score = sum(text.count(term) for term in terms)
            if score > 0:
                scores.append((score, path))

        scores.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, str]] = []

        for score, path in scores[:limit]:
            relative = str(path.relative_to(self.workspace_root))
            preview = path.read_text(encoding="utf-8", errors="ignore")[:1800]
            results.append({"path": relative, "score": str(score), "preview": preview})

        return results
