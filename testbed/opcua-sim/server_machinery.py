import asyncio
import datetime as dt
import random
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.3.0-machinery"
PORT = 4844


def _best_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return "127.0.0.1"


async def _add_var(parent, node_id: str, name: str, initial, writable: bool = False):
    var = await parent.add_variable(node_id, name, initial)
    if writable:
        await var.set_writable()
    return var


async def _create_machine_variables(machine_obj, ns: int, machine_idx: int) -> list:
    """Create ~220 variables per machine, grouped by logical subsystems."""
    vars_created = []
    prefix = f"M{machine_idx:02d}"

    groups = {
        "General": 20,
        "Kinematics": 40,
        "Drive": 35,
        "Thermal": 25,
        "Hydraulics": 25,
        "Pneumatics": 20,
        "Quality": 20,
        "Maintenance": 20,
        "Alarms": 15,
    }

    for group_name, count in groups.items():
        group_obj = await machine_obj.add_object(
            f"ns={ns};s=Machinery.{prefix}.{group_name}", group_name
        )

        for i in range(1, count + 1):
            node_id = f"ns={ns};s=Machinery.{prefix}.{group_name}.Var{i:03d}"
            var_name = f"Var{i:03d}"

            if group_name in {"Alarms"}:
                initial = False
                writable = True
            elif group_name in {"General", "Maintenance"}:
                initial = i
                writable = i % 3 == 0
            elif group_name in {"Quality"}:
                initial = round(95.0 + random.uniform(-2.0, 2.0), 2)
                writable = False
            else:
                initial = round(random.uniform(0.0, 100.0), 3)
                writable = i % 10 == 0

            var = await _add_var(group_obj, node_id, var_name, initial, writable=writable)
            vars_created.append((group_name, var))

    # Additional model-like nodes common in Machinery profiles
    ident_obj = await machine_obj.add_object(
        f"ns={ns};s=Machinery.{prefix}.Identification", "Identification"
    )
    vars_created.append(
        (
            "Identification",
            await _add_var(
                ident_obj,
                f"ns={ns};s=Machinery.{prefix}.Identification.Manufacturer",
                "Manufacturer",
                "Fictional Machines GmbH",
            ),
        )
    )
    vars_created.append(
        (
            "Identification",
            await _add_var(
                ident_obj,
                f"ns={ns};s=Machinery.{prefix}.Identification.Model",
                "Model",
                f"FM-{1000 + machine_idx}",
            ),
        )
    )
    vars_created.append(
        (
            "Identification",
            await _add_var(
                ident_obj,
                f"ns={ns};s=Machinery.{prefix}.Identification.SerialNumber",
                "SerialNumber",
                f"SN-{machine_idx:02d}-{dt.datetime.now().year}",
            ),
        )
    )

    return vars_created


async def main() -> None:
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{PORT}")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    # Namespace aligned to OPC UA for Machinery context
    machinery_uri = "http://opcfoundation.org/UA/Machinery/"
    ns = await server.register_namespace(machinery_uri)

    machinery_set = await server.nodes.objects.add_object(
        f"ns={ns};s=MachinerySet", "MachinerySet"
    )

    all_vars = []
    # 10 machines x ~220 vars + identification => >2200 variables
    for machine_idx in range(1, 11):
        machine_obj = await machinery_set.add_object(
            f"ns={ns};s=Machinery.M{machine_idx:02d}", f"Machine_{machine_idx:02d}"
        )
        machine_vars = await _create_machine_variables(machine_obj, ns, machine_idx)
        all_vars.extend(machine_vars)

    zeroconf: Zeroconf | None = None
    service_info: ServiceInfo | None = None

    try:
        host_ip = _best_ipv4()
        service_type = "_opcua-tcp._tcp.local."
        service_name = f"Machinery OPC UA Simulator {host_ip}.{service_type}"
        service_info = ServiceInfo(
            type_=service_type,
            name=service_name,
            addresses=[socket.inet_aton(host_ip)],
            port=PORT,
            properties={
                b"path": b"/",
                b"endpoint": f"opc.tcp://{host_ip}:{PORT}".encode(),
                b"sim_version": SIM_VERSION.encode(),
                b"profile": b"OPC UA for Machinery",
            },
            server=f"opcua-machinery-{host_ip.replace('.', '-')}.local.",
        )
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(service_info)
        print(f"mDNS announced: {service_name}")
    except Exception as err:
        print(f"mDNS announce skipped: {err}")

    print(f"OPC UA Machinery simulator running at opc.tcp://0.0.0.0:{PORT}")
    print(f"Namespace URI: {machinery_uri} (ns={ns})")
    print(f"Variables created: {len(all_vars)}")

    try:
        tick = 0
        async with server:
            while True:
                tick += 1
                # Update a subset each cycle for realism/performance
                for group_name, var in all_vars[::7]:
                    try:
                        val = await var.read_value()
                        if isinstance(val, bool):
                            if random.random() < 0.02:
                                await var.write_value(not val)
                        elif isinstance(val, (int, float)):
                            await var.write_value(round(float(val) + random.uniform(-0.5, 0.5), 3))
                        elif isinstance(val, str) and group_name == "Identification" and tick % 300 == 0:
                            await var.write_value(val)
                    except Exception:
                        pass
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
