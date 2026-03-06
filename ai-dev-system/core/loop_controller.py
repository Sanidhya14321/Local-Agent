from __future__ import annotations

from collections.abc import Awaitable, Callable

from core.agent_router import AgentRouter
from core.context_manager import ContextManager
from core.execution_engine import ExecutionEngine
from core.langgraph_orchestrator import LangGraphOrchestrator
from core.memory_store import MemoryStore
from core.self_improvement import SelfImprovementEngine
from core.schemas import RunRecord, RunStatus


class LoopController:
    def __init__(
        self,
        router: AgentRouter,
        context_manager: ContextManager,
        execution_engine: ExecutionEngine,
        memory_store: MemoryStore,
        self_improvement: SelfImprovementEngine,
        max_loops: int,
    ) -> None:
        self.router = router
        self.context_manager = context_manager
        self.execution_engine = execution_engine
        self.memory_store = memory_store
        self.self_improvement = self_improvement
        self.max_loops = max_loops
        self.langgraph = LangGraphOrchestrator(router=router, execution_engine=execution_engine)

    async def run(
        self,
        record: RunRecord,
        progress_callback: Callable[[RunRecord], Awaitable[None]] | None = None,
    ) -> RunRecord:
        async def emit() -> None:
            if progress_callback:
                await progress_callback(record)

        record.status = RunStatus.running
        await emit()
        repo_context = self.context_manager.build_context(record.task)
        skills_context = self.self_improvement.skills_context(record.task)
        memory_context = self.self_improvement.memory_context(record.task)
        workflow_context = self.self_improvement.workflow_context(record.task)

        record.logs.append("Planning task")
        await emit()
        plan = await self.router.planner.run(
            record.task,
            repo_context,
            skills_context=skills_context,
            memory_context=memory_context,
            workflow_context=workflow_context,
        )
        record.plan = plan
        await emit()

        record.logs.append("Designing architecture")
        await emit()
        architecture = await self.router.architect.run(record.task, plan.model_dump_json(indent=2))
        record.architecture = architecture
        await emit()

        for attempt in range(1, self.max_loops + 1):
            record.attempts = attempt
            record.logs.append(f"Attempt {attempt}: executing LangGraph workflow")
            await emit()

            async def on_attempt_progress(message: str) -> None:
                record.logs.append(message)
                await emit()

            result = await self.langgraph.run_attempt(
                task=record.task,
                plan_json=plan.model_dump_json(indent=2),
                architecture=str(architecture),
                repo_context=repo_context,
                previous_error=record.last_error,
                memory_context=memory_context,
                progress_callback=on_attempt_progress,
            )
            record.logs.extend(result.get("logs", []))
            changed = result.get("changed_files", [])
            record.changed_files.extend(changed)
            await emit()

            if int(result.get("check_exit_code", 1)) == 0:
                record.status = RunStatus.success
                record.logs.append("Checks passed. Workflow completed successfully.")
                await emit()
                self.memory_store.append_event(
                    "successful_runs",
                    {
                        "task": record.task,
                        "attempt": attempt,
                        "changed_files": changed,
                    },
                )
                await self._reflect_and_store(record)
                return record

            record.last_error = str(result.get("error_blob", "Unknown error"))
            record.logs.append("Checks failed after code/fix attempt. Retrying loop.")
            await emit()

        record.status = RunStatus.failed
        record.logs.append("Max loop count reached without success.")
        await emit()
        self.memory_store.append_event(
            "failed_runs",
            {"task": record.task, "attempts": record.attempts, "last_error": record.last_error[:1500]},
        )
        await self._reflect_and_store(record)
        return record

    async def _reflect_and_store(self, record: RunRecord) -> None:
        reflection = await self.router.reflection.run(
            task=record.task,
            logs=record.logs,
            status=record.status.value,
            changed_files=record.changed_files,
            last_error=record.last_error,
        )
        self.self_improvement.store_reflection(record, reflection)
