#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

missing=()
[[ -n "${BAND_CHAT_ID:-}" ]] || missing+=("BAND_CHAT_ID")

if [[ -z "${BAND_AGENT_API_KEY:-}" ]]; then
  for key in \
    BAND_PERIOP_INTAKE_AGENT_API_KEY \
    BAND_ECG_LAB_RISK_AGENT_API_KEY \
    BAND_PERIOP_SAFETY_REVIEWER_API_KEY \
    BAND_POSTOP_SURVEILLANCE_AGENT_API_KEY
  do
    [[ -n "${!key:-}" ]] || missing+=("$key")
  done
fi

agent_config="$ROOT_DIR/agent_config.yaml"
if [[ ! -f "$agent_config" ]]; then
  missing+=("agent_config.yaml")
fi

if (( ${#missing[@]} > 0 )); then
  printf 'Missing required Band environment variables: %s\n' "${missing[*]}" >&2
  printf 'Create the four external agents and a chat room in Band, copy band-agent-config.example.yaml to agent_config.yaml, then export either BAND_AGENT_API_KEY or the four per-agent API keys before running this script.\n' >&2
  exit 2
fi

for agent_key in periop_intake_agent ecg_lab_risk_agent periop_safety_reviewer postop_surveillance_agent; do
  if ! grep -q "$agent_key:" "$agent_config"; then
    printf 'agent_config.yaml is missing required agent entry: %s\n' "$agent_key" >&2
    exit 2
  fi
done

"$ROOT_DIR/backend/.venv/bin/python" - <<'PY'
import asyncio
import json
from fastapi.testclient import TestClient

from app.core.store import init_db
from app.main import app


async def main() -> None:
    init_db()
    client = TestClient(app)
    sample = client.post("/api/demo/sample-case").json()
    case_id = sample["case"]["id"]
    response = client.post(f"/api/cases/{case_id}/band-collaboration?send_to_band=true")
    response.raise_for_status()
    trace = response.json()
    print(json.dumps(
        {
            "case_id": case_id,
            "band_configured": trace["band_configured"],
            "room_id": trace["room_id"],
            "minimum_agent_requirement_met": trace["minimum_agent_requirement_met"],
            "agent_roles": len(trace["agent_roles"]),
            "steps": len(trace["collaboration_steps"]),
            "statuses": sorted({step["status"] for step in trace["collaboration_steps"]}),
        },
        ensure_ascii=False,
        indent=2,
    ))


asyncio.run(main())
PY
