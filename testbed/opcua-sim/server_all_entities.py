import asyncio
import datetime as dt
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.2.0-all-entities"
PORT = 4840


async def _add_var(parent, node_id: str, name: str, initial, writable: bool = False):
    var = await parent.add_variable(node_id, name, initial)
    if writable:
        await var.set_writable()
    return var


def _best_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return "127.0.0.1"


async def main() -> None:
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{PORT}")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    uri = "urn:machine-assistant:opcua-all-entities"
    idx = await server.register_namespace(uri)

    matrix = await server.nodes.objects.add_object(
        f"ns={idx};s=EntityMatrix", "EntityMatrix"
    )
    operation = await matrix.add_object(
        f"ns={idx};s=EntityMatrix.Operation", "Operation"
    )
    process = await matrix.add_object(f"ns={idx};s=EntityMatrix.Process", "Process")
    control = await matrix.add_object(f"ns={idx};s=EntityMatrix.Control", "Control")
    lighting = await matrix.add_object(f"ns={idx};s=EntityMatrix.Lighting", "Lighting")
    weather = await matrix.add_object(f"ns={idx};s=EntityMatrix.Weather", "Weather")
    diagnostics = await matrix.add_object(
        f"ns={idx};s=EntityMatrix.Diagnostics", "Diagnostics"
    )

    await _add_var(
        operation, f"ns={idx};s=EntityMatrix.Operation.Running", "Running", False, True
    )
    await _add_var(
        operation, f"ns={idx};s=EntityMatrix.Operation.Alarm", "Alarm", False, True
    )
    await _add_var(
        operation, f"ns={idx};s=EntityMatrix.Operation.Mode", "Mode", "Idle", True
    )
    await _add_var(
        operation, f"ns={idx};s=EntityMatrix.Operation.Heartbeat", "Heartbeat", 0
    )
    await _add_var(
        operation,
        f"ns={idx};s=EntityMatrix.Operation.LastStartUtc",
        "LastStartUtc",
        dt.datetime.now(dt.UTC),
        True,
    )

    await _add_var(
        process,
        f"ns={idx};s=EntityMatrix.Process.Temperature",
        "Temperature",
        21.5,
        True,
    )
    await _add_var(
        process, f"ns={idx};s=EntityMatrix.Process.Humidity", "Humidity", 45.0
    )
    await _add_var(
        process, f"ns={idx};s=EntityMatrix.Process.Pressure", "Pressure", 1.02
    )
    await _add_var(
        process, f"ns={idx};s=EntityMatrix.Process.WindSpeed", "WindSpeed", 12.0
    )
    await _add_var(
        process,
        f"ns={idx};s=EntityMatrix.Process.TemperatureSetpoint",
        "TemperatureSetpoint",
        22.0,
        True,
    )
    await _add_var(
        process,
        f"ns={idx};s=EntityMatrix.Process.SpeedSetpoint",
        "SpeedSetpoint",
        1200,
        True,
    )
    await _add_var(
        process,
        f"ns={idx};s=EntityMatrix.Process.RecipeName",
        "RecipeName",
        "Recipe-A",
        True,
    )

    await _add_var(
        control, f"ns={idx};s=EntityMatrix.Control.Commands.Start", "Start", False, True
    )
    await _add_var(
        control, f"ns={idx};s=EntityMatrix.Control.Commands.Stop", "Stop", False, True
    )
    await _add_var(
        control, f"ns={idx};s=EntityMatrix.Control.Commands.Open", "Open", False, True
    )
    await _add_var(
        control, f"ns={idx};s=EntityMatrix.Control.Commands.Close", "Close", False, True
    )
    await _add_var(
        control,
        f"ns={idx};s=EntityMatrix.Control.Commands.SceneActivate",
        "SceneActivate",
        False,
        True,
    )
    await _add_var(
        control,
        f"ns={idx};s=EntityMatrix.Control.Cover.Position",
        "Position",
        50.0,
        True,
    )

    await _add_var(
        lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.On", "On", False, True
    )
    await _add_var(
        lighting,
        f"ns={idx};s=EntityMatrix.Lighting.Main.Brightness",
        "Brightness",
        128,
        True,
    )
    await _add_var(
        lighting,
        f"ns={idx};s=EntityMatrix.Lighting.Main.ColorTemp",
        "ColorTemp",
        370,
        True,
    )
    await _add_var(
        lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Hue", "Hue", 180.0, True
    )
    await _add_var(
        lighting,
        f"ns={idx};s=EntityMatrix.Lighting.Main.Saturation",
        "Saturation",
        70.0,
        True,
    )
    await _add_var(
        lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Effect", "Effect", "off", True
    )
    await _add_var(
        lighting,
        f"ns={idx};s=EntityMatrix.Lighting.Main.Transition",
        "Transition",
        1.0,
        True,
    )
    await _add_var(
        lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Flash", "Flash", "short", True
    )

    light_type = await server.nodes.base_object_type.add_object_type(
        f"ns={idx};s=EntityMatrix.Types.LightType", "LightType"
    )
    home = await server.nodes.objects.add_object(f"ns={idx};s=Home", "Home")
    home_lights = await home.add_object(f"ns={idx};s=Home.Lights", "Lights")
    rainbow = await home_lights.add_object(
        f"ns={idx};s=Home.Lights.RainbowPro", "Rainbow Pro", objecttype=light_type
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.State", "State", False, True
    )
    await _add_var(
        rainbow,
        f"ns={idx};s=Home.Lights.RainbowPro.Brightness",
        "Brightness",
        180,
        True,
    )
    await _add_var(
        rainbow,
        f"ns={idx};s=Home.Lights.RainbowPro.ColorTempKelvin",
        "ColorTempKelvin",
        3500,
        True,
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.Hue", "Hue", 210.0, True
    )
    await _add_var(
        rainbow,
        f"ns={idx};s=Home.Lights.RainbowPro.Saturation",
        "Saturation",
        65.0,
        True,
    )
    await _add_var(rainbow, f"ns={idx};s=Home.Lights.RainbowPro.R", "R", 120, True)
    await _add_var(rainbow, f"ns={idx};s=Home.Lights.RainbowPro.G", "G", 90, True)
    await _add_var(rainbow, f"ns={idx};s=Home.Lights.RainbowPro.B", "B", 255, True)
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_R", "RGBWW_R", 120, True
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_G", "RGBWW_G", 90, True
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_B", "RGBWW_B", 255, True
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_CW", "RGBWW_CW", 45, True
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_WW", "RGBWW_WW", 55, True
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.White", "White", 80, True
    )
    await _add_var(rainbow, f"ns={idx};s=Home.Lights.RainbowPro.X", "X", 0.31, True)
    await _add_var(rainbow, f"ns={idx};s=Home.Lights.RainbowPro.Y", "Y", 0.33, True)
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.Effect", "Effect", "off", True
    )
    await _add_var(
        rainbow,
        f"ns={idx};s=Home.Lights.RainbowPro.Transition",
        "Transition",
        1.0,
        True,
    )
    await _add_var(
        rainbow, f"ns={idx};s=Home.Lights.RainbowPro.Flash", "Flash", "short", True
    )

    await _add_var(
        weather,
        f"ns={idx};s=EntityMatrix.Weather.Condition",
        "Condition",
        "sunny",
        True,
    )
    await _add_var(
        diagnostics,
        f"ns={idx};s=EntityMatrix.Diagnostics.Message",
        "Message",
        "System OK",
        True,
    )
    await _add_var(
        diagnostics,
        f"ns={idx};s=EntityMatrix.Diagnostics.Title",
        "Title",
        "Matrix",
        True,
    )

    zeroconf: Zeroconf | None = None
    service_info: ServiceInfo | None = None
    try:
        host_ip = _best_ipv4()
        service_type = "_opcua-tcp._tcp.local."
        service_name = f"All Entities OPC UA Simulator {host_ip}.{service_type}"
        service_info = ServiceInfo(
            type_=service_type,
            name=service_name,
            addresses=[socket.inet_aton(host_ip)],
            port=PORT,
            properties={
                b"path": b"/",
                b"endpoint": f"opc.tcp://{host_ip}:{PORT}".encode(),
                b"sim_version": SIM_VERSION.encode(),
            },
            server=f"opcua-all-entities-{host_ip.replace('.', '-')}.local.",
        )
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(service_info)
        print(f"mDNS announced: {service_name}")
    except Exception as err:
        print(f"mDNS announce skipped: {err}")

    try:
        async with server:
            print(f"OPC UA all-entities simulator running at opc.tcp://0.0.0.0:{PORT}")
            print(f"Namespace URI: {uri} (ns={idx})")
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
