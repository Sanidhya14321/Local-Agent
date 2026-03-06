from __future__ import annotations

from core.schemas import CodeProposal
from tools.filesystem_tool import FilesystemTool
from tools.test_runner import TestRunner


class ExecutionEngine:
    def __init__(self, filesystem_tool: FilesystemTool, test_runner: TestRunner, workspace_root: str) -> None:
        self.filesystem_tool = filesystem_tool
        self.test_runner = test_runner
        self.workspace_root = workspace_root

    def apply_changes(self, proposal: CodeProposal) -> list[str]:
        changed_files: list[str] = []
        for change in proposal.changes:
            self.filesystem_tool.write_file(change.path, change.content)
            changed_files.append(change.path)
        return changed_files

    async def run_checks(self, commands: list[str] | None = None) -> dict[str, str | int]:
        checks = commands or ["python3 -m py_compile $(find . -name '*.py')"]
        return await self.test_runner.run(checks, cwd=self.workspace_root)
