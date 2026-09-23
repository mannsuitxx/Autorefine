#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "Checking Ollama runtime..."
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama serve on 127.0.0.1:11434..."
  nohup ~/.local/bin/ollama serve > /tmp/sih_ollama.log 2>&1 &
  sleep 2
fi

echo "Building React frontend..."
if ! (cd frontend/react && npm install && npm run build); then
  echo "ERROR: Frontend build failed! Refusing to start uvicorn with missing dist/." >&2
  exit 1
fi

if [ ! -d "frontend/react/dist" ]; then
  echo "ERROR: frontend/react/dist directory is missing after build! Refusing to start uvicorn." >&2
  exit 1
fi

PORT="${PORT:-8001}"
fuser -k "$PORT/tcp" 2>/dev/null || true

HOST="${HOST:-127.0.0.1}"
echo "Starting AutoRefine Workbench Console on ${HOST}:${PORT}..."
nohup python3 -m uvicorn backend.main:app --host "$HOST" --port "$PORT" > /tmp/sih_backend.log 2>&1 &

sleep 2
echo "================================================================================"
echo "  ✅ AUTOREFINE WORKBENCH ONLINE (100% AIR-GAPPED ON-PREMISE):"
echo "  • AutoRefine Console   : http://localhost:${PORT}"
echo "  • API documentation    : http://localhost:${PORT}/docs"
echo "================================================================================"
