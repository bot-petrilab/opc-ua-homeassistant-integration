import asyncio
import datetime as dt
import random
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.1.0-entity-matrix"
PORT = 4846


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

    last_start_utc = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.LastStartUtc", "LastStartUtc", dt.datetime.utcnow(), True)

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

    weather_condition = await _add_var(weather, f"ns={idx};s=EntityMatrix.Weather.Condition", "Condition", "sunny", True)
    weather_message = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Message", "Message", "System OK", True)
    weather_title = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Title", "Title", "Matrix", True)

    modes = ["Idle", "Run", "Service"]
    conditions = ["sunny", "cloudy", "rainy", "partlycloudy"]
    recipes = ["Recipe-A", "Recipe-B", "Recipe-C"]

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
            counter = 0
            while True:
                counter += 1
                if await cmd_start.read_value():
                    await running.write_value(True)
                    await cmd_start.write_value(False)
                    await last_start_utc.write_value(dt.datetime.utcnow())
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

                run = bool(await running.read_value())
                temp = float(await temperature.read_value())
                temp = min(32.0, temp + random.uniform(0.1, 0.6)) if run else max(18.0, temp - random.uniform(0.1, 0.4))

                await temperature.write_value(round(temp, 2))
                await humidity.write_value(round(40 + random.uniform(-8, 8), 1))
                await pressure.write_value(round(1.0 + random.uniform(-0.08, 0.08), 3))
                await wind_speed.write_value(round(10 + random.uniform(0, 8), 1))
                await heartbeat.write_value(counter)

                if counter % 20 == 0:
                    await mode.write_value(modes[(counter // 20) % len(modes)])
                if counter % 25 == 0:
                    await recipe_name.write_value(recipes[(counter // 25) % len(recipes)])
                if counter % 15 == 0:
                    await weather_condition.write_value(conditions[(counter // 15) % len(conditions)])
                if counter % 30 == 0:
                    await weather_message.write_value(f"Status tick {counter}")

                # Keep light related values moving
                if bool(await light_on.read_value()):
                    await light_brightness.write_value(int(max(1, min(255, await light_brightness.read_value() + random.randint(-10, 10)))))
                    await light_hue.write_value(float((await light_hue.read_value() + 7) % 360))
                    await light_sat.write_value(float(max(1, min(100, await light_sat.read_value() + random.uniform(-3, 3)))))

                # Random alarm pulses for binary sensor / notify testing
                if counter % 40 == 0:
                    await alarm.write_value(True)
                elif counter % 40 == 6:
                    await alarm.write_value(False)

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
