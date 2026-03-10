import asyncio
from pathlib import Path
import socket

from asyncua import Server, ua
from asyncua.server.user_managers import User, UserRole
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.1.0-basic256-userpass"
PORT = 4851

BASE_DIR = Path(__file__).resolve().parent
CERT_PATH = BASE_DIR / "certs" / "server_basic256_cert.pem"
KEY_PATH = BASE_DIR / "certs" / "server_basic256_key.pem"

USERNAME = "admin"
PASSWORD = "Admin123"


def _best_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return "127.0.0.1"


class _StrictUserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        if username == USERNAME and password == PASSWORD:
            return User(role=UserRole.User)
        return None


async def main() -> None:
    if not CERT_PATH.exists() or not KEY_PATH.exists():
        raise RuntimeError(
            f"Missing cert/key. Expected: {CERT_PATH} and {KEY_PATH}"
        )

    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{PORT}")

    # Enforce secure channel + username/password token.
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    server.set_identity_tokens([ua.UserNameIdentityToken])
    server.iserver.set_user_manager(_StrictUserManager())

    await server.load_certificate(str(CERT_PATH))
    await server.load_private_key(str(KEY_PATH))

    uri = "urn:machine-assistant:opcua-basic256-userpass"
    idx = await server.register_namespace(uri)

    root = await server.nodes.objects.add_object(f"ns={idx};s=SecureBasic256UserPass", "SecureBasic256UserPass")
    await root.add_variable(f"ns={idx};s=SecureBasic256UserPass.Connected", "Connected", True)
    secure_switch = await root.add_variable(
        f"ns={idx};s=SecureBasic256UserPass.SecureSwitch", "SecureSwitch", False
    )
    await secure_switch.set_writable()

    zeroconf: Zeroconf | None = None
    service_info: ServiceInfo | None = None
    try:
        host_ip = _best_ipv4()
        service_type = "_opcua-tcp._tcp.local."
        service_name = f"Basic256 UserPass OPC UA Simulator {host_ip}.{service_type}"
        service_info = ServiceInfo(
            type_=service_type,
            name=service_name,
            addresses=[socket.inet_aton(host_ip)],
            port=PORT,
            properties={
                b"path": b"/",
                b"endpoint": f"opc.tcp://{host_ip}:{PORT}".encode(),
                b"sim_version": SIM_VERSION.encode(),
                b"security": b"Basic256Sha256_SignAndEncrypt",
                b"identity": b"Username",
                b"username": USERNAME.encode(),
            },
            server=f"opcua-basic256-userpass-{host_ip.replace('.', '-')}.local.",
        )
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(service_info)
        print(f"mDNS announced: {service_name}")
    except Exception as err:
        print(f"mDNS announce skipped: {err}")

    try:
        async with server:
            print(f"OPC UA Basic256+UserPass simulator running at opc.tcp://0.0.0.0:{PORT}")
            print(f"Namespace URI: {uri} (ns={idx})")
            print("Security: Basic256Sha256_SignAndEncrypt")
            print(f"Identity token: Username (user={USERNAME})")
            while True:
                await asyncio.sleep(1)
    finally:
        if zeroconf is not None and service_info is not None:
            try:
                zeroconf.unregister_service(service_info)
            except Exception:
                pass
            zeroconf.close()


if __name__ == "__main__":
    asyncio.run(main())
