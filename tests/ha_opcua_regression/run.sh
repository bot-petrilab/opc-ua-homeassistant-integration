#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/user/.openclaw/workspace"
TEST_DIR="$ROOT/tests/ha_opcua_regression"
VENV="$ROOT/.pw-venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Playwright venv missing at $VENV. Please create it first."
  exit 1
fi

export HA_URL="${HA_URL:-http://localhost:8123}"
export HA_USER="${HA_USER:-admin}"
export HA_PASS="${HA_PASS:-Admin123}"
export OPC_ENDPOINT="${OPC_ENDPOINT:-opc.tcp://127.0.0.1:4840}"
export OUT_DIR="${OUT_DIR:-$TEST_DIR/out}"

"$VENV/bin/python" "$TEST_DIR/test_runner.py"

# Optional extended checks for PR readiness
if [ "${FULL_MATRIX:-0}" = "1" ]; then
  "$VENV/bin/python" "$TEST_DIR/platform_coverage_check.py"
fi

if [ "${SECURITY_CHECK:-0}" = "1" ]; then
  "$VENV/bin/python" "$TEST_DIR/security_configflow_check.py"
fi
