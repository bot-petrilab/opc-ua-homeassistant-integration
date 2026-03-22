#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

from asyncua import Server, ua

# Import integration client manager directly
import sys

sys.path.insert(
    0, "/home/user/.openclaw/workspace/ha-docs-test-env/config/custom_components"
)
from opcua.opcua_client import OpcUaClientManager  # type: ignore


async def run_secure_server(stop_evt: asyncio.Event, cert: str, key: str) -> None:
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4841")
    server.set_server_name("Secure OPC UA Test Server")

    await server.load_certificate(cert)
    await server.load_private_key(key)
    server.set_security_policy(
        [
            ua.SecurityPolicyType.Basic256Sha256_Sign,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ]
    )

    idx = await server.register_namespace("urn:opcua:secure-test")
    obj = await server.nodes.objects.add_object(
        f"ns={idx};s=SecureMachine", "SecureMachine"
    )
    await obj.add_variable(f"ns={idx};s=SecureMachine.TestValue", "TestValue", 123.45)

    async with server:
        while not stop_evt.is_set():
            await asyncio.sleep(0.2)


def make_cert_pair(base: Path, name: str) -> tuple[str, str]:
    cert = base / f"{name}.crt"
    key = base / f"{name}.key"
    cmd = [
        "openssl",
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-sha256",
        "-nodes",
        "-keyout",
        str(key),
        "-out",
        str(cert),
        "-days",
        "365",
        "-subj",
        f"/CN={name}",
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(cert), str(key)


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="opcua-sec-test-") as td:
        td_path = Path(td)
        server_cert, server_key = make_cert_pair(td_path, "opcua-server")
        client_cert, client_key = make_cert_pair(td_path, "opcua-client")

        stop_evt = asyncio.Event()
        server_task = asyncio.create_task(
            run_secure_server(stop_evt, server_cert, server_key)
        )
        await asyncio.sleep(1.8)

        try:
            m_sign = OpcUaClientManager(
                endpoint="opc.tcp://127.0.0.1:4841",
                security_policy="Basic256Sha256_Sign",
                username=None,
                password=None,
                client_cert_path=client_cert,
                client_key_path=client_key,
                server_cert_path=server_cert,
                client_key_password=None,
            )

            browse = await m_sign.browse_nodes(
                root_node_id="i=85", depth=5, max_nodes=500
            )
            test_nodes = [
                item.get("node_id")
                for item in browse
                if str(item.get("name", "")) == "TestValue"
            ]
            if not test_nodes:
                raise RuntimeError(
                    "Could not locate TestValue node in secure server browse"
                )
            test_node_id = str(test_nodes[0])

            vals_sign = await m_sign.read_nodes([test_node_id])
            await m_sign.disconnect()

            m_se = OpcUaClientManager(
                endpoint="opc.tcp://127.0.0.1:4841",
                security_policy="Basic256Sha256_SignAndEncrypt",
                username=None,
                password=None,
                client_cert_path=client_cert,
                client_key_path=client_key,
                server_cert_path=server_cert,
                client_key_password=None,
            )
            vals_se = await m_se.read_nodes([test_node_id])
            await m_se.disconnect()

            print("NODE:", test_node_id)
            print("SIGN:", vals_sign)
            print("SIGN_ENCRYPT:", vals_se)

            ok_sign = vals_sign.get(test_node_id) is not None
            ok_se = vals_se.get(test_node_id) is not None
            if not (ok_sign and ok_se):
                raise RuntimeError("Security policy read failed")

            print("SECURITY_POLICY_TEST: PASS")
        finally:
            stop_evt.set()
            try:
                await asyncio.wait_for(server_task, timeout=5)
            except Exception:
                server_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
