from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from core.agent_router import AgentRouter
from core.execution_engine import ExecutionEngine


class GraphState(TypedDict, total=False):
    task: str
    plan_json: str
    architecture: str
    repo_context: str
    previous_error: str
    changed_files: list[str]
    logs: list[str]
    check_exit_code: int
    check_stdout: str
    check_stderr: str
    error_blob: str
    debug_report_json: str
    test_commands: list[str]
    memory_context: str


class LangGraphOrchestrator:
    def __init__(self, router: AgentRouter, execution_engine: ExecutionEngine) -> None:
        self.router = router
        self.execution_engine = execution_engine
        self._progress_callback: Callable[[str], Awaitable[None]] | None = None
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(GraphState)

        async def notify(message: str) -> None:
            if self._progress_callback is not None:
                await self._progress_callback(message)

        async def code_node(state: GraphState) -> GraphState:
            await notify("Coder agent: generating implementation")
            proposal = await self.router.coder.run(
                task=state["task"],
                plan=state["plan_json"],
                architecture=state["architecture"],
                repo_context=state["repo_context"],
                previous_error=state.get("previous_error", ""),
            )
            changed_files = self.execution_engine.apply_changes(proposal)
            logs = state.get("logs", []) + [f"Coder applied {len(changed_files)} file(s)"]
            await notify(f"Coder agent: applied {len(changed_files)} file(s)")
            return {
                "changed_files": changed_files,
                "logs": logs,
                "test_commands": proposal.tests or ["python3 -m py_compile $(find . -name '*.py')"],
            }

        async def test_node(state: GraphState) -> GraphState:
            await notify("Execution engine: running validation checks")
            result = await self.execution_engine.run_checks(state.get("test_commands"))
            stdout = str(result.get("stdout", ""))
            stderr = str(result.get("stderr", ""))
            exit_code = int(result.get("exit_code", 1))
            logs = state.get("logs", []) + [f"Execution checks exit_code={exit_code}"]
            await notify(f"Execution engine: checks finished with exit_code={exit_code}")
            return {
                "check_exit_code": exit_code,
                "check_stdout": stdout,
                "check_stderr": stderr,
                "error_blob": f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}",
                "logs": logs,
            }

        async def debug_node(state: GraphState) -> GraphState:
            await notify("Debugger agent: analyzing failure")
            debug = await self.router.debugger.run(
                task=state["task"],
                logs=state.get("error_blob", ""),
                plan=state["plan_json"],
                memory_context=state.get("memory_context", ""),
            )
            logs = state.get("logs", []) + ["Debugger produced root-cause analysis"]
            await notify("Debugger agent: root cause analysis ready")
            return {"debug_report_json": debug.model_dump_json(indent=2), "logs": logs}

        async def fix_node(state: GraphState) -> GraphState:
            await notify("Fix agent: generating patch")
            fix_proposal = await self.router.fixer.run(
                task=state["task"],
                debug_report=state.get("debug_report_json", "{}"),
                repo_context=state["repo_context"],
            )
            fixed_files = self.execution_engine.apply_changes(fix_proposal)
            logs = state.get("logs", []) + [f"Fix agent applied {len(fixed_files)} file(s)"]
            await notify(f"Fix agent: applied {len(fixed_files)} file(s)")
            return {
                "changed_files": state.get("changed_files", []) + fixed_files,
                "logs": logs,
                "previous_error": state.get("error_blob", ""),
                "test_commands": fix_proposal.tests or state.get("test_commands", []),
            }

        def should_debug(state: GraphState) -> str:
            return "debug" if state.get("check_exit_code", 1) != 0 else "done"

        graph.add_node("code", code_node)
        graph.add_node("test", test_node)
        graph.add_node("debug", debug_node)
        graph.add_node("fix", fix_node)

        graph.add_edge(START, "code")
        graph.add_edge("code", "test")
        graph.add_conditional_edges("test", should_debug, {"debug": "debug", "done": END})
        graph.add_edge("debug", "fix")
        graph.add_edge("fix", END)

        return graph.compile()

    async def run_attempt(
        self,
        task: str,
        plan_json: str,
        architecture: str,
        repo_context: str,
        previous_error: str,
        memory_context: str,
        progress_callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> GraphState:
        self._progress_callback = progress_callback
        initial_state: GraphState = {
            "task": task,
            "plan_json": plan_json,
            "architecture": architecture,
            "repo_context": repo_context,
            "previous_error": previous_error,
            "memory_context": memory_context,
            "changed_files": [],
            "logs": [],
        }
        try:
            result = await self.graph.ainvoke(initial_state)
            return result
        finally:
            self._progress_callback = None
