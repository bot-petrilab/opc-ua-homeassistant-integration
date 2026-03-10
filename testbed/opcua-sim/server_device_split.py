import asyncio
import datetime as dt
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.1.0-entity-matrix"
PORT = 4842


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

    uri = "urn:machine-assistant:opcua-entity-matrix"
    idx = await server.register_namespace(uri)

    matrix = await server.nodes.objects.add_object(f"ns={idx};s=EntityMatrix", "EntityMatrix")
    operation = await matrix.add_object(f"ns={idx};s=EntityMatrix.Operation", "Operation")
    process = await matrix.add_object(f"ns={idx};s=EntityMatrix.Process", "Process")
    control = await matrix.add_object(f"ns={idx};s=EntityMatrix.Control", "Control")
    lighting = await matrix.add_object(f"ns={idx};s=EntityMatrix.Lighting", "Lighting")
    weather = await matrix.add_object(f"ns={idx};s=EntityMatrix.Weather", "Weather")
    diagnostics = await matrix.add_object(f"ns={idx};s=EntityMatrix.Diagnostics", "Diagnostics")

    # Base nodes for all platforms
    running = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Running", "Running", False, True)
    alarm = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Alarm", "Alarm", False, True)
    mode = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Mode", "Mode", "Idle", True)
    heartbeat = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Heartbeat", "Heartbeat", 0)

    temperature = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Temperature", "Temperature", 21.5, True)
    humidity = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Humidity", "Humidity", 45.0)
    pressure = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Pressure", "Pressure", 1.02)
    wind_speed = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.WindSpeed", "WindSpeed", 12.0)
    setpoint = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.TemperatureSetpoint", "TemperatureSetpoint", 22.0, True)
    speed_setpoint = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.SpeedSetpoint", "SpeedSetpoint", 1200, True)
    recipe_name = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.RecipeName", "RecipeName", "Recipe-A", True)

    last_start_utc = await _add_var(
        operation,
        f"ns={idx};s=EntityMatrix.Operation.LastStartUtc",
        "LastStartUtc",
        dt.datetime.now(dt.UTC),
        True,
    )

    cmd_start = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Start", "Start", False, True)
    cmd_stop = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Stop", "Stop", False, True)
    cmd_open = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Open", "Open", False, True)
    cmd_close = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Close", "Close", False, True)
    cmd_scene = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.SceneActivate", "SceneActivate", False, True)
    cover_position = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Cover.Position", "Position", 50.0, True)

    light_on = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.On", "On", False, True)
    light_brightness = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Brightness", "Brightness", 128, True)
    light_color_temp = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.ColorTemp", "ColorTemp", 370, True)
    light_hue = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Hue", "Hue", 180.0, True)
    light_sat = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Saturation", "Saturation", 70.0, True)
    light_effect = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Effect", "Effect", "off", True)
    light_transition = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Transition", "Transition", 1, True)
    light_flash = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Flash", "Flash", "short", True)

    # Object-based Light discovery testbed (LightType via HasTypeDefinition)
    light_type = await server.nodes.base_object_type.add_object_type(
        f"ns={idx};s=EntityMatrix.Types.LightType", "LightType"
    )
    device_type = await server.nodes.base_object_type.add_object_type(
        f"ns={idx};s=EntityMatrix.Types.DeviceType", "DeviceType"
    )

    home = await server.nodes.objects.add_object(f"ns={idx};s=Home", "Home")
    home_devices = await home.add_object(f"ns={idx};s=Home.Devices", "Devices")

    device_panel = await home_devices.add_object(
        f"ns={idx};s=Home.Devices.Panel01", "Panel 01", objecttype=device_type
    )
    await _add_var(device_panel, f"ns={idx};s=Home.Devices.Panel01.Manufacturer", "Manufacturer", "Petri Automation", False)
    await _add_var(device_panel, f"ns={idx};s=Home.Devices.Panel01.Model", "Model", "PA-LightPanel", False)
    await _add_var(device_panel, f"ns={idx};s=Home.Devices.Panel01.SerialNumber", "SerialNumber", "PA-PANEL-0001", False)
    panel_lights = await device_panel.add_object(f"ns={idx};s=Home.Devices.Panel01.Lights", "Lights")

    device_rgb = await home_devices.add_object(
        f"ns={idx};s=Home.Devices.RgbController01", "RGB Controller 01", objecttype=device_type
    )
    await _add_var(device_rgb, f"ns={idx};s=Home.Devices.RgbController01.Manufacturer", "Manufacturer", "Petri Automation", False)
    await _add_var(device_rgb, f"ns={idx};s=Home.Devices.RgbController01.Model", "Model", "PA-RGBWW", False)
    await _add_var(device_rgb, f"ns={idx};s=Home.Devices.RgbController01.SerialNumber", "SerialNumber", "PA-RGB-0001", False)
    rgb_lights = await device_rgb.add_object(f"ns={idx};s=Home.Devices.RgbController01.Lights", "Lights")

    light_obj_main = await panel_lights.add_object(
        f"ns={idx};s=Home.Lights.MatrixMain", "Matrix Main", objecttype=light_type
    )
    await _add_var(light_obj_main, f"ns={idx};s=Home.Lights.MatrixMain.State", "State", False, True)
    await _add_var(light_obj_main, f"ns={idx};s=Home.Lights.MatrixMain.Brightness", "Brightness", 128, True)

    light_obj_corridor = await panel_lights.add_object(
        f"ns={idx};s=Home.Lights.Corridor", "Corridor", objecttype=light_type
    )
    await _add_var(light_obj_corridor, f"ns={idx};s=Home.Lights.Corridor.State", "State", True, True)

    # Full-featured light object for Home Assistant light platform options coverage
    light_obj_full = await rgb_lights.add_object(
        f"ns={idx};s=Home.Lights.RainbowPro", "Rainbow Pro", objecttype=light_type
    )
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.State", "State", False, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Brightness", "Brightness", 180, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.ColorTempKelvin", "ColorTempKelvin", 3500, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Hue", "Hue", 210.0, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Saturation", "Saturation", 65.0, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.R", "R", 120, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.G", "G", 90, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.B", "B", 255, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBW_R", "RGBW_R", 120, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBW_G", "RGBW_G", 90, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBW_B", "RGBW_B", 255, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBW_W", "RGBW_W", 40, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_R", "RGBWW_R", 120, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_G", "RGBWW_G", 90, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_B", "RGBWW_B", 255, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_CW", "RGBWW_CW", 45, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.RGBWW_WW", "RGBWW_WW", 55, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.White", "White", 80, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.X", "X", 0.31, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Y", "Y", 0.33, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Effect", "Effect", "off", True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Transition", "Transition", 1.0, True)
    await _add_var(light_obj_full, f"ns={idx};s=Home.Lights.RainbowPro.Flash", "Flash", "short", True)

    weather_condition = await _add_var(weather, f"ns={idx};s=EntityMatrix.Weather.Condition", "Condition", "sunny", True)
    weather_message = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Message", "Message", "System OK", True)
    weather_title = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Title", "Title", "Matrix", True)

    zeroconf: Zeroconf | None = None
    service_info: ServiceInfo | None = None
    try:
        host_ip = _best_ipv4()
        service_type = "_opcua-tcp._tcp.local."
        service_name = f"Entity Matrix OPC UA Simulator {host_ip}.{service_type}"
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
            server=f"opcua-entity-matrix-{host_ip.replace('.', '-')}.local.",
        )
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(service_info)
        print(f"mDNS announced: {service_name}")
    except Exception as err:
        print(f"mDNS announce skipped: {err}")

    try:
        async with server:
            print(f"OPC UA entity-matrix simulator running at opc.tcp://0.0.0.0:{PORT}")
            print(f"Namespace URI: {uri} (ns={idx})")
            print("Entity matrix runs in static mode: values stay unchanged unless a client writes them.")
            while True:
                if await cmd_start.read_value():
                    await running.write_value(True)
                    await cmd_start.write_value(False)
                    await last_start_utc.write_value(dt.datetime.now(dt.UTC))
                if await cmd_stop.read_value():
                    await running.write_value(False)
                    await cmd_stop.write_value(False)
                if await cmd_open.read_value():
                    await cover_position.write_value(100.0)
                    await cmd_open.write_value(False)
                if await cmd_close.read_value():
                    await cover_position.write_value(0.0)
                    await cmd_close.write_value(False)
                if await cmd_scene.read_value():
                    await light_on.write_value(True)
                    await light_effect.write_value("pulse")
                    await cmd_scene.write_value(False)

                # Keep all process/weather/diagnostics values static for deterministic tests.
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
