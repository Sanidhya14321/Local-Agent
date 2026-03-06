# AI Dev System (Local Autonomous Coding)

A fully local autonomous AI coding system that runs on Ollama and coordinates multiple agents through a local MCP server, with a VS Code extension as the primary interface.

## Architecture

User -> VS Code Extension -> MCP Server -> LangGraph-style Orchestrator -> Planner/Architecture/Code/Test/Debug/Fix Agents -> Ollama Models

## Models

- `deepseek-r1:7b`: planning, architecture, debugging, root-cause analysis
- `qwen2.5-coder:7b`: coding, refactoring, tests, implementation fixes

## Quick Start

1. Start Ollama and ensure the models exist:
   - `ollama pull deepseek-r1:7b`
   - `ollama pull qwen2.5-coder:7b`
2. Create a Python virtual environment:
   - `python3 -m venv .venv`
3. Install dependencies:
   - `.venv/bin/python -m pip install -r requirements.txt`
4. Start MCP server:
   - `./scripts/start_mcp.sh`
5. Open `vscode_extension/` in VS Code and run extension host (`F5`).

## Notes

- No cloud calls are required.
- Tool execution happens through the MCP server.
- Configurable via environment variables in `.env`.
- Includes self-improving memory backed by ChromaDB (`.ai_learning_memory/`).
- Planner reuses skills + task workflows before generating plans.
- Reflection agent stores reusable solutions and bug/fix memory after each run.
