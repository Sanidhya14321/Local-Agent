from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from config.settings import settings
from mcp_server.agent_runtime import AgentRuntime


app = FastAPI(title="Local AI Dev MCP Server", version="0.1.0")
workspace_root = str(Path(settings.workspace_root).resolve())
runtime = AgentRuntime(workspace_root=workspace_root)


class RunWorkflowRequest(BaseModel):
    task: str


class FileRequest(BaseModel):
    path: str
    content: str | None = None


class CommandRequest(BaseModel):
    command: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 8


class MemoryQueryRequest(BaseModel):
    memory_type: str
    query: str
    limit: int = 5


class ApplyPreviewRequest(BaseModel):
    changes: list[dict]
    tests: list[str] = []


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "workspace_root": workspace_root}


@app.post("/workflow/run")
async def run_workflow(body: RunWorkflowRequest) -> dict[str, str]:
    record = runtime.run_async(task=body.task)
    return {"run_id": record.run_id, "status": record.status.value}


@app.post("/workflow/preview")
async def preview_workflow(body: RunWorkflowRequest) -> dict:
    return await runtime.preview(task=body.task)


@app.post("/workflow/preview/apply")
async def apply_preview_workflow(body: ApplyPreviewRequest) -> dict:
    if not body.changes:
        raise HTTPException(status_code=400, detail="changes are required")
    return await runtime.apply_preview_changes(changes=body.changes, tests=body.tests)


@app.get("/learning/skills")
async def learning_skills() -> dict:
    return {"skills": runtime.self_improvement.skill_library.as_dicts()}


@app.post("/learning/memory/query")
async def learning_memory_query(body: MemoryQueryRequest) -> dict:
    results = runtime.self_improvement.learning_memory.query_memory(
        memory_type=body.memory_type,
        query=body.query,
        limit=body.limit,
    )
    return {"results": results}


@app.post("/learning/reindex")
async def learning_reindex() -> dict:
    count = runtime.self_improvement.index_repository(workspace_root)
    return {"indexed_files": count}


@app.get("/workflow/{run_id}")
async def get_workflow(run_id: str) -> dict:
    record = runtime.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run_id not found")
    return runtime.serialize_record(record)


@app.websocket("/workflow/{run_id}/stream")
async def stream_workflow(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()

    record = runtime.get_run(run_id)
    if not record:
        await websocket.send_json({"type": "error", "message": "run_id not found"})
        await websocket.close(code=1008)
        return

    queue = runtime.subscribe(run_id)
    await websocket.send_json(runtime.serialize_record(record))

    try:
        while True:
            update = await queue.get()
            await websocket.send_json(update)
            if update.get("status") in {"success", "failed"}:
                await websocket.close(code=1000)
                break
    except WebSocketDisconnect:
        pass
    finally:
        runtime.unsubscribe(run_id, queue)


@app.post("/tools/filesystem/read")
async def fs_read(body: FileRequest) -> dict[str, str]:
    return {"content": runtime.registry.filesystem.read_file(body.path)}


@app.post("/tools/filesystem/write")
async def fs_write(body: FileRequest) -> dict[str, str]:
    if body.content is None:
        raise HTTPException(status_code=400, detail="content is required")
    out = runtime.registry.filesystem.write_file(body.path, body.content)
    return {"written": out}


@app.post("/tools/filesystem/mkdir")
async def fs_mkdir(body: FileRequest) -> dict[str, str]:
    out = runtime.registry.filesystem.make_dir(body.path)
    return {"created": out}


@app.post("/tools/terminal/run")
async def terminal_run(body: CommandRequest) -> dict:
    return await runtime.registry.terminal.run(command=body.command, cwd=workspace_root)


@app.post("/tools/repo_search")
async def repo_search(body: SearchRequest) -> dict:
    results = runtime.registry.repo_search.search(query=body.query, limit=body.limit)
    return {"results": results}


@app.post("/tools/test_execution")
async def test_execution(body: SearchRequest) -> dict:
    commands = [line.strip() for line in body.query.split("\n") if line.strip()]
    result = await runtime.registry.test_execution.run(commands=commands, cwd=workspace_root)
    return result
