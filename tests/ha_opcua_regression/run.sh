#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${VENV_PATH:-$REPO_ROOT/.venv-playwright}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Playwright venv not found at $VENV"
  echo "Create it with:"
  echo "  python3 -m venv $VENV"
  echo "  $VENV/bin/pip install playwright"
  echo "  $VENV/bin/playwright install chromium"
  exit 1
fi

export HA_URL="${HA_URL:-http://localhost:8123}"
export HA_USER="${HA_USER:-admin}"
export HA_PASS="${HA_PASS:-Admin123}"
export OPC_ENDPOINT="${OPC_ENDPOINT:-opc.tcp://127.0.0.1:4840}"
export OUT_DIR="${OUT_DIR:-$REPO_ROOT/tests/ha_opcua_regression/out}"

"$VENV/bin/python" "$REPO_ROOT/tests/ha_opcua_regression/test_runner.py"
