#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x ".venv/bin/python" ]]; then
	echo "Missing virtualenv at .venv"
	echo "Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
	exit 1
fi

export ANONYMIZED_TELEMETRY=False
export CHROMA_TELEMETRY_ENABLED=False
export CHROMA_PRODUCT_TELEMETRY_IMPL=chromadb.telemetry.product.null.NullProductTelemetry

if ! .venv/bin/python - <<'PY'
import socket

s = socket.socket()
try:
	s.bind(("127.0.0.1", 8765))
except OSError:
	raise SystemExit(1)
finally:
	s.close()
PY
then
  echo "Port 8765 is already in use. Stop the existing MCP server process first."
  echo "Tip: run 'lsof -i :8765' to find it, then 'kill <pid>'."
  exit 1
fi

if [[ "${MCP_RELOAD:-false}" == "true" ]]; then
	.venv/bin/python -m uvicorn mcp_server.server:app --reload --host 127.0.0.1 --port 8765
else
	.venv/bin/python -m uvicorn mcp_server.server:app --host 127.0.0.1 --port 8765
fi
