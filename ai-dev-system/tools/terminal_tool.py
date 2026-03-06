from __future__ import annotations

import asyncio


class TerminalTool:
    async def run(self, command: str, cwd: str, timeout: int = 300) -> dict[str, str | int]:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "exit_code": process.returncode or 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except TimeoutError:
            process.kill()
            return {"exit_code": 124, "stdout": "", "stderr": "Command timed out"}
