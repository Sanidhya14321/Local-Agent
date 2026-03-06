from __future__ import annotations

from pathlib import Path


class FilesystemTool:
    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def _resolve(self, relative_path: str) -> Path:
        target = (self.workspace_root / relative_path).resolve()
        if self.workspace_root not in target.parents and target != self.workspace_root:
            raise ValueError("Path escapes workspace root")
        return target

    def read_file(self, relative_path: str) -> str:
        target = self._resolve(relative_path)
        return target.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> str:
        target = self._resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return str(target)

    def make_dir(self, relative_path: str) -> str:
        target = self._resolve(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        return str(target)
