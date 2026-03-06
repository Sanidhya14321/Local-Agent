from __future__ import annotations

from tools.terminal_tool import TerminalTool


class TestRunner:
    __test__ = False

    def __init__(self, terminal_tool: TerminalTool) -> None:
        self.terminal_tool = terminal_tool

    async def run(self, commands: list[str], cwd: str) -> dict[str, str | int]:
        combined_stdout: list[str] = []
        combined_stderr: list[str] = []
        last_code = 0

        for command in commands:
            result = await self.terminal_tool.run(command=command, cwd=cwd)
            last_code = int(result["exit_code"])
            combined_stdout.append(f"$ {command}\n{result['stdout']}")
            combined_stderr.append(result["stderr"])
            if last_code != 0:
                break

        return {
            "exit_code": last_code,
            "stdout": "\n".join(combined_stdout),
            "stderr": "\n".join(filter(None, combined_stderr)),
        }
