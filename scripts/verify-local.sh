#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

"$BACKEND_DIR/.venv/bin/python" -m pip install -e "$BACKEND_DIR[dev]"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "== Backend tests =="
(cd "$BACKEND_DIR" && ".venv/bin/python" -m pytest)

echo "== Local safety evals =="
(cd "$BACKEND_DIR" && ".venv/bin/python" -m app.evals.run_local)

echo "== Frontend production build =="
(cd "$FRONTEND_DIR" && npm run build)

echo "All local verification checks passed."
