#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
TEST_DIR="$REPO_ROOT/tests/ha_opcua_regression"
VENV="$WORKSPACE_ROOT/.pw-venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Playwright venv missing at $VENV"
  exit 1
fi

HA_URL="${HA_URL:-http://localhost:8123}"
HA_USER="${HA_USER:-admin}"
HA_PASS="${HA_PASS:-Admin123}"
OUT_DIR="${OUT_DIR:-$TEST_DIR/out}"

ENDPOINTS=(
  "${OPC_ENDPOINT_1:-opc.tcp://127.0.0.1:4840}"
  "${OPC_ENDPOINT_2:-opc.tcp://127.0.0.1:4842}"
)

echo "HA_URL=$HA_URL"
echo "Endpoints: ${ENDPOINTS[*]}"

for ep in "${ENDPOINTS[@]}"; do
  echo
  echo "=== E2E matrix run for $ep ==="
  HA_URL="$HA_URL" HA_USER="$HA_USER" HA_PASS="$HA_PASS" OPC_ENDPOINT="$ep" OUT_DIR="$OUT_DIR" "$VENV/bin/python" "$TEST_DIR/test_runner.py"
  HA_URL="$HA_URL" HA_USER="$HA_USER" HA_PASS="$HA_PASS" OPC_ENDPOINT="$ep" OUT_DIR="$OUT_DIR" "$VENV/bin/python" "$TEST_DIR/config_entry_add_remove_check.py"
  HA_URL="$HA_URL" HA_USER="$HA_USER" HA_PASS="$HA_PASS" OPC_ENDPOINT="$ep" OUT_DIR="$OUT_DIR" "$VENV/bin/python" "$TEST_DIR/security_policy_matrix_check.py"
done

echo
echo "Matrix run completed successfully. Artifacts in: $OUT_DIR"
