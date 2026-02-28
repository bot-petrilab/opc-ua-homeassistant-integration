#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_SERVER = REPO_ROOT / "testbed" / "opcua-sim" / "server.py"
CLIENT_MODULE = REPO_ROOT / "custom_components" / "opcua_machine" / "opcua_client.py"


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def load_client_manager():
    spec = importlib.util.spec_from_file_location("opcua_client", CLIENT_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load opcua_client module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OpcUaClientManager


async def run_smoke() -> None:
    OpcUaClientManager = load_client_manager()

    rows = await OpcUaClientManager.discover_servers("opc.tcp://127.0.0.1:4840", include_network=False)
    if not rows:
        raise AssertionError("discover_servers returned no endpoints")

    # At least one endpoint should use None policy in simulator
    if not any(r.get("security_policy") == "None" for r in rows):
        raise AssertionError(f"No security_policy None endpoint in discovery: {rows}")

    manager = OpcUaClientManager(
        endpoint="opc.tcp://127.0.0.1:4840",
        security_policy="None",
        username=None,
        password=None,
    )

    browse = await manager.browse_nodes(root_node_id="ns=2;s=Machine", depth=3, max_nodes=300)
    if not browse:
        raise AssertionError("browse_nodes returned empty list")

    names = {str(item.get("name", "")) for item in browse}
    expected_groups = {"Operation", "Process", "Assets", "Control", "Diagnostics"}
    if not expected_groups.issubset(names):
        raise AssertionError(f"Missing expected group names: {expected_groups - names}")

    values = await manager.read_nodes([
        "ns=2;s=Machine.Process.Temperature",
        "ns=2;s=Machine.Operation.Running",
        "ns=2;s=Machine.Control.StackLight.Green",
    ])
    for nid in values:
        if values[nid] is None:
            raise AssertionError(f"Read returned None for {nid}")

    await manager.disconnect()


def main() -> None:
    if not SIM_SERVER.exists():
        raise SystemExit(f"Simulator script missing: {SIM_SERVER}")

    env = dict(os.environ)
    proc = subprocess.Popen(
        [sys.executable, str(SIM_SERVER)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )

    try:
        if not wait_for_port("127.0.0.1", 4840, timeout=40.0):
            logs = ""
            if proc.stdout:
                logs = proc.stdout.read()
            raise SystemExit(f"Simulator did not open port 4840 in time. Logs:\n{logs}")

        asyncio.run(run_smoke())
        print("CI smoke test: PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
