from __future__ import annotations

import asyncio
import difflib
import uuid

from config.settings import settings
from core.agent_router import AgentRouter
from core.context_manager import ContextManager
from core.execution_engine import ExecutionEngine
from core.loop_controller import LoopController
from core.memory_store import MemoryStore
from core.self_improvement import SelfImprovementEngine
from core.schemas import RunRecord, RunStatus
from mcp_server.tool_registry import ToolRegistry


class AgentRuntime:
    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = workspace_root
        self.registry = ToolRegistry(workspace_root)
        self.router = AgentRouter()
        self.self_improvement = SelfImprovementEngine(
            workspace_root,
            persist_directory=settings.chroma_persist_dir,
            embedding_model=settings.embedding_model_name,
        )
        self.self_improvement.index_repository(workspace_root)
        self.context_manager = ContextManager(self.registry.repo_search, self_improvement=self.self_improvement)
        self.execution_engine = ExecutionEngine(
            filesystem_tool=self.registry.filesystem,
            test_runner=self.registry.test_execution,
            workspace_root=workspace_root,
        )
        self.memory_store = MemoryStore(workspace_root)
        self.loop_controller = LoopController(
            router=self.router,
            context_manager=self.context_manager,
            execution_engine=self.execution_engine,
            memory_store=self.memory_store,
            self_improvement=self.self_improvement,
            max_loops=settings.max_agent_loops,
        )
        self.records: dict[str, RunRecord] = {}
        self.subscribers: dict[str, list[asyncio.Queue[dict]]] = {}
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.max_log_payload_entries = 80

    def create_run(self, task: str) -> RunRecord:
        run_id = str(uuid.uuid4())
        record = RunRecord(run_id=run_id, status=RunStatus.queued, task=task)
        self.records[run_id] = record
        return record

    async def execute(self, run_id: str) -> None:
        record = self.records[run_id]
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(run_id))
        try:
            updated = await self.loop_controller.run(record, progress_callback=self._emit_update)
            self.records[run_id] = updated
            await self._emit_update(updated)
        except asyncio.CancelledError:
            if record.status not in {RunStatus.success, RunStatus.failed}:
                record.status = RunStatus.failed
                record.last_error = "Run cancelled by user"
                record.logs.append("Workflow cancelled by user.")
                self.records[run_id] = record
                await self._emit_update(record)
            raise
        except Exception as exc:
            record.status = RunStatus.failed
            detail = str(exc).strip() or repr(exc)
            record.last_error = f"Unhandled runtime error ({type(exc).__name__}): {detail}"
            record.logs.append("Workflow crashed before completion.")
            self.records[run_id] = record
            await self._emit_update(record)
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            self.tasks.pop(run_id, None)

    def run_async(self, task: str) -> RunRecord:
        record = self.create_run(task)
        self.subscribers.setdefault(record.run_id, [])
        self.tasks[record.run_id] = asyncio.create_task(self.execute(record.run_id))
        return record

    async def cancel_run(self, run_id: str) -> tuple[bool, str]:
        record = self.records.get(run_id)
        if not record:
            return False, "run_id not found"

        if record.status in {RunStatus.success, RunStatus.failed}:
            return False, f"run already terminal ({record.status.value})"

        task = self.tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            return True, "cancellation requested"

        record.status = RunStatus.failed
        record.last_error = "Run cancelled by user"
        record.logs.append("Workflow cancelled by user.")
        self.records[run_id] = record
        await self._emit_update(record)
        return True, "cancelled"

    def get_run(self, run_id: str) -> RunRecord | None:
        return self.records.get(run_id)

    async def preview(self, task: str) -> dict:
        repo_context = self.context_manager.build_context(task)
        plan = await self.router.planner.run(
            task,
            repo_context,
            skills_context=self.self_improvement.skills_context(task),
            memory_context=self.self_improvement.memory_context(task),
            workflow_context=self.self_improvement.workflow_context(task),
        )
        architecture = await self.router.architect.run(task, plan.model_dump_json(indent=2))
        proposal = await self.router.coder.run(
            task=task,
            plan=plan.model_dump_json(indent=2),
            architecture=str(architecture),
            repo_context=repo_context,
            previous_error="",
        )

        enriched_changes: list[dict] = []
        for change in proposal.changes:
            before_content = ""
            try:
                before_content = self.registry.filesystem.read_file(change.path)
            except Exception:
                before_content = ""

            unified_diff = "\n".join(
                difflib.unified_diff(
                    before_content.splitlines(),
                    change.content.splitlines(),
                    fromfile=f"a/{change.path}",
                    tofile=f"b/{change.path}",
                    lineterm="",
                )
            )
            enriched_changes.append(
                {
                    "path": change.path,
                    "content": change.content,
                    "before_content": before_content,
                    "diff": unified_diff,
                }
            )

        return {
            "task": task,
            "plan": plan.model_dump(),
            "architecture": architecture,
            "summary": proposal.summary,
            "changes": enriched_changes,
            "tests": proposal.tests,
        }

    async def apply_preview_changes(self, changes: list[dict], tests: list[str] | None = None) -> dict:
        changed_files: list[str] = []
        for change in changes:
            path = str(change.get("path", "")).strip()
            content = str(change.get("content", ""))
            if not path:
                continue
            self.registry.filesystem.write_file(path, content)
            changed_files.append(path)

        check_result = await self.execution_engine.run_checks(tests or None)
        return {
            "applied": len(changed_files),
            "changed_files": changed_files,
            "checks": check_result,
        }

    def subscribe(self, run_id: str) -> asyncio.Queue[dict]:
        if run_id not in self.records:
            raise KeyError(run_id)
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self.subscribers.setdefault(run_id, []).append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[dict]) -> None:
        listeners = self.subscribers.get(run_id, [])
        if queue in listeners:
            listeners.remove(queue)
        if not listeners and run_id in self.subscribers:
            del self.subscribers[run_id]

    async def _emit_update(self, record: RunRecord) -> None:
        payload = self.serialize_record(record)
        for queue in self.subscribers.get(record.run_id, []):
            await queue.put(payload)

    def serialize_record(self, record: RunRecord) -> dict:
        payload = record.model_dump()
        payload["logs"] = record.logs[-self.max_log_payload_entries :]
        return payload

    async def _heartbeat_loop(self, run_id: str) -> None:
        while True:
            await asyncio.sleep(2)
            record = self.records.get(run_id)
            if record is None:
                return
            if record.status in {RunStatus.success, RunStatus.failed}:
                return
            if record.status == RunStatus.running:
                await self._emit_update(record)
