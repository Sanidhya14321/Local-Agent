# MCP Server API

This server exposes local tool and orchestration endpoints over HTTP.

## Endpoints

- `GET /health`
- `POST /workflow/run` with `{ "task": "..." }`
- `POST /workflow/preview` with `{ "task": "..." }`
- `POST /workflow/preview/apply` with `{ "changes": [...], "tests": [...] }`
- `GET /workflow/{run_id}`

Learning endpoints:
- `GET /learning/skills`
- `POST /learning/memory/query`
- `POST /learning/reindex`

Tool endpoints:
- `POST /tools/filesystem/read`
- `POST /tools/filesystem/write`
- `POST /tools/filesystem/mkdir`
- `POST /tools/terminal/run`
- `POST /tools/repo_search`
- `POST /tools/test_execution`

## Run

```bash
uvicorn mcp_server.server:app --reload --port 8765
```
