#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DB_PATH="${PERIOP_DB_PATH:-$ROOT_DIR/data/periop_agent.sqlite}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

"$BACKEND_DIR/.venv/bin/python" -m pip install -e "$BACKEND_DIR[dev]"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "Starting FastAPI backend on http://127.0.0.1:8010"
PERIOP_DB_PATH="$DB_PATH" "$BACKEND_DIR/.venv/bin/python" -m uvicorn app.main:app --app-dir "$BACKEND_DIR" --port 8010 &
BACKEND_PID=$!

echo "Starting React workbench on http://127.0.0.1:5173"
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

echo
echo "Demo ready:"
echo "  1. Open http://127.0.0.1:5173"
echo "  2. Click \"Load sample case\""
echo "  3. Review and export the draft"
echo
echo "Press Ctrl+C to stop both services."

wait "$BACKEND_PID" "$FRONTEND_PID"
