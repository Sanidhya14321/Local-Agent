from __future__ import annotations

from tools.filesystem_tool import FilesystemTool
from tools.repo_indexer import RepoIndexer
from tools.terminal_tool import TerminalTool
from tools.test_runner import TestRunner


class ToolRegistry:
    def __init__(self, workspace_root: str) -> None:
        self.filesystem = FilesystemTool(workspace_root)
        self.terminal = TerminalTool()
        self.repo_search = RepoIndexer(workspace_root)
        self.test_execution = TestRunner(self.terminal)
