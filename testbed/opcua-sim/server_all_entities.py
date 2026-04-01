import asyncio
import datetime as dt
import os
import random
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.3.0-all-entities-random-device"
PORT = int(os.environ.get("OPCUA_SIM_PORT", "4840"))
ZEROCONF_TYPE = "_opcua-tcp._tcp.local."


async def _add_var(parent, node_id: str, name: str, initial, writable: bool = False):
    var = await parent.add_variable(node_id, name, initial)
    if writable:
        await var.set_writable()
    return var


def _best_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def register_zeroconf() -> tuple[Zeroconf | None, ServiceInfo | None]:
    try:
        host_ip = _best_ipv4()
        service_name = f"opcua-all-entities-{host_ip}.{ZEROCONF_TYPE}"
        info = ServiceInfo(
            type_=ZEROCONF_TYPE,
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
        zeroconf.register_service(info)
        print(f"mDNS announced: {service_name}", flush=True)
        return zeroconf, info
    except Exception as err:
        print(f"mDNS announce skipped: {err}", flush=True)
        return None, None


async def main() -> None:
    zeroconf, info = register_zeroconf()
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{PORT}")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    uri = "urn:machine-assistant:opcua-all-entities"
    idx = await server.register_namespace(uri)

    # Legacy matrix tree kept for CI smoke and regression tests
    matrix = await server.nodes.objects.add_object(f"ns={idx};s=EntityMatrix", "EntityMatrix")
    operation = await matrix.add_object(f"ns={idx};s=EntityMatrix.Operation", "Operation")
    process = await matrix.add_object(f"ns={idx};s=EntityMatrix.Process", "Process")
    control = await matrix.add_object(f"ns={idx};s=EntityMatrix.Control", "Control")
    lighting = await matrix.add_object(f"ns={idx};s=EntityMatrix.Lighting", "Lighting")
    weather = await matrix.add_object(f"ns={idx};s=EntityMatrix.Weather", "Weather")
    diagnostics = await matrix.add_object(f"ns={idx};s=EntityMatrix.Diagnostics", "Diagnostics")

    running = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Running", "Running", False, True)
    alarm = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Alarm", "Alarm", False, True)
    mode = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Mode", "Mode", "Idle", True)
    heartbeat = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.Heartbeat", "Heartbeat", 0)
    last_start_utc = await _add_var(operation, f"ns={idx};s=EntityMatrix.Operation.LastStartUtc", "LastStartUtc", dt.datetime.now(dt.UTC), True)

    temperature = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Temperature", "Temperature", 21.5, True)
    humidity = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Humidity", "Humidity", 45.0)
    pressure = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.Pressure", "Pressure", 1.02)
    wind_speed = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.WindSpeed", "WindSpeed", 12.0)
    temp_setpoint = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.TemperatureSetpoint", "TemperatureSetpoint", 22.0, True)
    speed_setpoint = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.SpeedSetpoint", "SpeedSetpoint", 1200, True)
    recipe_name = await _add_var(process, f"ns={idx};s=EntityMatrix.Process.RecipeName", "RecipeName", "Recipe-A", True)

    cmd_start = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Start", "Start", False, True)
    cmd_stop = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Stop", "Stop", False, True)
    cmd_open = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Open", "Open", False, True)
    cmd_close = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.Close", "Close", False, True)
    cmd_scene = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.SceneActivate", "SceneActivate", False, True)
    cmd_valve_open = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.ValveOpen", "ValveOpen", False, True)
    cmd_valve_close = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.ValveClose", "ValveClose", False, True)
    cmd_valve_stop = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Commands.ValveStop", "ValveStop", False, True)
    cover_position = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Cover.Position", "Position", 50.0, True)
    valve_position = await _add_var(control, f"ns={idx};s=EntityMatrix.Control.Valve.Position", "ValvePosition", 30.0, True)

    light_on = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.On", "On", False, True)
    light_brightness = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Brightness", "Brightness", 128, True)
    light_color_temp = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.ColorTemp", "ColorTemp", 370, True)
    light_hue = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Hue", "Hue", 180.0, True)
    light_sat = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Saturation", "Saturation", 70.0, True)
    light_effect = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Effect", "Effect", "off", True)
    light_transition = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Transition", "Transition", 1.0, True)
    light_flash = await _add_var(lighting, f"ns={idx};s=EntityMatrix.Lighting.Main.Flash", "Flash", "short", True)

    weather_condition = await _add_var(weather, f"ns={idx};s=EntityMatrix.Weather.Condition", "Condition", "sunny", True)
    notify_message = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Message", "Message", "System OK", True)
    notify_title = await _add_var(diagnostics, f"ns={idx};s=EntityMatrix.Diagnostics.Title", "Title", "Matrix", True)

    # One complete device with all entity capabilities the integration supports
    device_type = await server.nodes.base_object_type.add_object_type(f"ns={idx};s=Demo.Types.DeviceType", "DeviceType")
    light_type = await server.nodes.base_object_type.add_object_type(f"ns={idx};s=Demo.Types.LightType", "LightType")

    home = await server.nodes.objects.add_object(f"ns={idx};s=Home", "Home")
    devices = await home.add_object(f"ns={idx};s=Home.Devices", "Devices")
    demo = await devices.add_object(f"ns={idx};s=Home.Devices.PaDemoCell", "PA-DemoCell", objecttype=device_type)

    await _add_var(demo, f"ns={idx};s=Home.Devices.PaDemoCell.Manufacturer", "Manufacturer", "Petri Automation")
    await _add_var(demo, f"ns={idx};s=Home.Devices.PaDemoCell.Model", "Model", "PA-DemoCell")
    await _add_var(demo, f"ns={idx};s=Home.Devices.PaDemoCell.SerialNumber", "SerialNumber", "PA-DEMO-0001")

    demo_operation = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Operation", "Operation")
    demo_climate = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Climate", "Climate")
    demo_motion = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Motion", "Motion")
    demo_cover = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Cover", "Cover")
    demo_valve = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Valve", "Valve")
    demo_weather = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Weather", "Weather")
    demo_notify = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Notify", "Notify")
    demo_sensor = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Sensor", "Sensor")
    demo_switch = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Switch", "Switch")
    demo_select = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Select", "Select")
    demo_text = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Text", "Text")
    demo_button = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Button", "Button")
    demo_number = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Number", "Number")
    demo_scene = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Scene", "Scene")
    demo_date_obj = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.DateObject", "DateObject")
    demo_datetime_obj = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.DateTimeObject", "DateTimeObject")
    demo_time_obj = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.TimeObject", "TimeObject")
    demo_fan = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.Fan", "Fan")
    demo_light = await demo.add_object(f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro", "Rainbow Pro", objecttype=light_type)

    dev_running = await _add_var(demo_operation, f"ns={idx};s=Home.Devices.PaDemoCell.Operation.Running", "Running", True, True)
    dev_alarm = await _add_var(demo_operation, f"ns={idx};s=Home.Devices.PaDemoCell.Operation.Alarm", "Alarm", False, True)
    dev_mode = await _add_var(demo_select, f"ns={idx};s=Home.Devices.PaDemoCell.Select.Mode", "Mode", "Auto", True)
    dev_recipe = await _add_var(demo_text, f"ns={idx};s=Home.Devices.PaDemoCell.Text.RecipeName", "RecipeName", "Blend-A", True)
    dev_heartbeat = await _add_var(demo_sensor, f"ns={idx};s=Home.Devices.PaDemoCell.Sensor.Heartbeat", "Heartbeat", 0)
    dev_last_start = await _add_var(demo_sensor, f"ns={idx};s=Home.Devices.PaDemoCell.Sensor.LastStartUtc", "LastStartUtc", dt.datetime.now(dt.UTC), True)
    dev_start = await _add_var(demo_button, f"ns={idx};s=Home.Devices.PaDemoCell.Button.Start", "Start", False, True)

    dev_temperature = await _add_var(demo_sensor, f"ns={idx};s=Home.Devices.PaDemoCell.Sensor.Temperature", "Temperature", 22.4, True)
    dev_setpoint = await _add_var(demo_climate, f"ns={idx};s=Home.Devices.PaDemoCell.Climate.TargetTemperature", "TargetTemperature", 23.0, True)
    dev_hvac = await _add_var(demo_climate, f"ns={idx};s=Home.Devices.PaDemoCell.Climate.HvacMode", "HvacMode", "auto", True)
    dev_speed = await _add_var(demo_number, f"ns={idx};s=Home.Devices.PaDemoCell.Number.FanSpeed", "FanSpeed", 1100, True)
    dev_humidity = await _add_var(demo_weather, f"ns={idx};s=Home.Devices.PaDemoCell.Weather.Humidity", "Humidity", 48.0, True)
    dev_pressure = await _add_var(demo_weather, f"ns={idx};s=Home.Devices.PaDemoCell.Weather.Pressure", "Pressure", 1.01, True)
    dev_wind = await _add_var(demo_weather, f"ns={idx};s=Home.Devices.PaDemoCell.Weather.WindSpeed", "WindSpeed", 8.0, True)
    dev_condition = await _add_var(demo_weather, f"ns={idx};s=Home.Devices.PaDemoCell.Weather.Condition", "Condition", "partlycloudy", True)

    dev_motion_detected = await _add_var(demo_motion, f"ns={idx};s=Home.Devices.PaDemoCell.Motion.Detected", "MotionDetected", False, True)
    dev_switch_enabled = await _add_var(demo_switch, f"ns={idx};s=Home.Devices.PaDemoCell.Switch.Enabled", "Enabled", True, True)
    dev_cover_position = await _add_var(demo_cover, f"ns={idx};s=Home.Devices.PaDemoCell.Cover.Position", "Position", 35.0, True)
    dev_cover_tilt = await _add_var(demo_cover, f"ns={idx};s=Home.Devices.PaDemoCell.Cover.TiltPosition", "TiltPosition", 20.0, True)
    dev_cover_open = await _add_var(demo_cover, f"ns={idx};s=Home.Devices.PaDemoCell.Cover.Open", "Open", False, True)
    dev_cover_close = await _add_var(demo_cover, f"ns={idx};s=Home.Devices.PaDemoCell.Cover.Close", "Close", False, True)
    dev_valve_position = await _add_var(demo_valve, f"ns={idx};s=Home.Devices.PaDemoCell.Valve.Position", "Position", 55.0, True)
    dev_valve_open = await _add_var(demo_valve, f"ns={idx};s=Home.Devices.PaDemoCell.Valve.Open", "Open", False, True)
    dev_valve_close = await _add_var(demo_valve, f"ns={idx};s=Home.Devices.PaDemoCell.Valve.Close", "Close", False, True)
    dev_valve_stop = await _add_var(demo_valve, f"ns={idx};s=Home.Devices.PaDemoCell.Valve.Stop", "Stop", False, True)
    dev_fan_running = await _add_var(demo_fan, f"ns={idx};s=Home.Devices.PaDemoCell.Fan.Running", "Running", True, True)

    dev_notify_message = await _add_var(demo_notify, f"ns={idx};s=Home.Devices.PaDemoCell.Notify.Message", "Message", "No alerts", True)
    dev_notify_title = await _add_var(demo_notify, f"ns={idx};s=Home.Devices.PaDemoCell.Notify.Title", "Title", "PA-DemoCell", True)
    dev_scene = await _add_var(demo_scene, f"ns={idx};s=Home.Devices.PaDemoCell.Scene.Activate", "Activate", False, True)
    dev_date = await _add_var(demo_date_obj, f"ns={idx};s=Home.Devices.PaDemoCell.DateObject.Date", "Date", dt.datetime.now(dt.UTC), True)
    dev_datetime = await _add_var(demo_datetime_obj, f"ns={idx};s=Home.Devices.PaDemoCell.DateTimeObject.DateTime", "DateTime", dt.datetime.now(dt.UTC), True)
    dev_time = await _add_var(demo_time_obj, f"ns={idx};s=Home.Devices.PaDemoCell.TimeObject.Time", "Time", dt.datetime.now(dt.UTC), True)

    dev_light_state = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.State", "State", True, True)
    dev_light_brightness = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Brightness", "Brightness", 180, True)
    dev_light_temp = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.ColorTempKelvin", "ColorTempKelvin", 3500, True)
    dev_light_hue = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Hue", "Hue", 210.0, True)
    dev_light_sat = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Saturation", "Saturation", 65.0, True)
    dev_light_r = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.R", "R", 120, True)
    dev_light_g = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.G", "G", 90, True)
    dev_light_b = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.B", "B", 255, True)
    dev_light_cw = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.CW", "CW", 45, True)
    dev_light_ww = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.WW", "WW", 55, True)
    dev_light_white = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.White", "White", 80, True)
    dev_light_x = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.X", "X", 0.31, True)
    dev_light_y = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Y", "Y", 0.33, True)
    dev_light_effect = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Effect", "Effect", "rainbow", True)
    dev_light_transition = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Transition", "Transition", 1.5, True)
    dev_light_flash = await _add_var(demo_light, f"ns={idx};s=Home.Devices.PaDemoCell.RainbowPro.Flash", "Flash", "short", True)

    weather_cycle = ["sunny", "partlycloudy", "cloudy", "rainy", "windy"]
    effect_cycle = ["off", "pulse", "rainbow", "aurora", "night"]
    mode_cycle = ["Idle", "Run", "Service"]
    hvac_cycle = ["off", "heat", "cool", "auto"]
    recipe_cycle = ["Recipe-A", "Recipe-B", "Recipe-C"]
    notify_cycle = ["System OK", "Maintenance due", "Filter warning", "Batch complete"]

    try:
        async with server:
            print(f"OPC UA all-entities simulator running at opc.tcp://0.0.0.0:{PORT}")
            print(f"Namespace URI: {uri} (ns={idx})")
            print("Randomized demo device active: PA-DemoCell", flush=True)
            rng = random.Random(42)
            while True:
                # command semantics
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
                if await cmd_valve_open.read_value():
                    await valve_position.write_value(100.0)
                    await cmd_valve_open.write_value(False)
                if await cmd_valve_close.read_value():
                    await valve_position.write_value(0.0)
                    await cmd_valve_close.write_value(False)
                if await cmd_valve_stop.read_value():
                    await cmd_valve_stop.write_value(False)

                if await dev_start.read_value():
                    await dev_running.write_value(True)
                    await dev_last_start.write_value(dt.datetime.now(dt.UTC))
                    await dev_start.write_value(False)
                if await dev_cover_open.read_value():
                    await dev_cover_position.write_value(100.0)
                    await dev_cover_open.write_value(False)
                if await dev_cover_close.read_value():
                    await dev_cover_position.write_value(0.0)
                    await dev_cover_close.write_value(False)
                if await dev_valve_open.read_value():
                    await dev_valve_position.write_value(100.0)
                    await dev_valve_open.write_value(False)
                if await dev_valve_close.read_value():
                    await dev_valve_position.write_value(0.0)
                    await dev_valve_close.write_value(False)
                if await dev_valve_stop.read_value():
                    await dev_valve_stop.write_value(False)
                if await dev_scene.read_value():
                    await dev_light_state.write_value(True)
                    await dev_light_effect.write_value("pulse")
                    await dev_scene.write_value(False)

                # random drift for legacy matrix
                await heartbeat.write_value(int(await heartbeat.read_value()) + 1)
                await temperature.write_value(round(20.0 + rng.random() * 6.0, 2))
                await humidity.write_value(round(35.0 + rng.random() * 30.0, 1))
                await pressure.write_value(round(0.98 + rng.random() * 0.08, 3))
                await wind_speed.write_value(round(3.0 + rng.random() * 20.0, 1))
                await recipe_name.write_value(rng.choice(recipe_cycle))
                await mode.write_value(rng.choice(mode_cycle))
                await light_brightness.write_value(rng.randint(10, 255))
                await light_hue.write_value(round(rng.random() * 360.0, 1))
                await light_sat.write_value(round(rng.random() * 100.0, 1))
                await light_effect.write_value(rng.choice(effect_cycle))
                await weather_condition.write_value(rng.choice(weather_cycle))
                await notify_message.write_value(rng.choice(notify_cycle))
                await notify_title.write_value("Matrix")
                await alarm.write_value(rng.random() < 0.15)
                await running.write_value(rng.random() < 0.7)

                # random drift for complete demo device
                await dev_heartbeat.write_value(int(await dev_heartbeat.read_value()) + 1)
                await dev_running.write_value(rng.random() < 0.8)
                await dev_alarm.write_value(rng.random() < 0.12)
                await dev_mode.write_value(rng.choice(["Auto", "Manual", "Service"]))
                await dev_recipe.write_value(rng.choice(["Blend-A", "Blend-B", "Blend-C"]))
                await dev_motion_detected.write_value(rng.random() < 0.25)
                await dev_switch_enabled.write_value(rng.random() < 0.9)
                await dev_temperature.write_value(round(19.5 + rng.random() * 8.0, 2))
                await dev_setpoint.write_value(round(20.0 + rng.random() * 6.0, 1))
                await dev_hvac.write_value(rng.choice(hvac_cycle))
                await dev_speed.write_value(rng.randint(600, 2400))
                await dev_fan_running.write_value(rng.random() < 0.85)
                await dev_humidity.write_value(round(30.0 + rng.random() * 45.0, 1))
                await dev_pressure.write_value(round(0.97 + rng.random() * 0.09, 3))
                await dev_wind.write_value(round(rng.random() * 18.0, 1))
                await dev_condition.write_value(rng.choice(weather_cycle))
                await dev_notify_message.write_value(rng.choice(["No alerts", "Door open", "Temperature drift", "Batch finished"]))
                await dev_notify_title.write_value("PA-DemoCell")
                now = dt.datetime.now(dt.UTC)
                await dev_date.write_value(now)
                await dev_datetime.write_value(now)
                await dev_time.write_value(now)
                await dev_cover_position.write_value(round(rng.random() * 100.0, 1))
                await dev_cover_tilt.write_value(round(rng.random() * 100.0, 1))
                await dev_valve_position.write_value(round(rng.random() * 100.0, 1))
                await dev_light_state.write_value(rng.random() < 0.85)
                await dev_light_brightness.write_value(rng.randint(1, 255))
                await dev_light_temp.write_value(rng.randint(2200, 6500))
                hue = round(rng.random() * 360.0, 1)
                sat = round(rng.random() * 100.0, 1)
                await dev_light_hue.write_value(hue)
                await dev_light_sat.write_value(sat)
                await dev_light_r.write_value(rng.randint(0, 255))
                await dev_light_g.write_value(rng.randint(0, 255))
                await dev_light_b.write_value(rng.randint(0, 255))
                await dev_light_cw.write_value(rng.randint(0, 255))
                await dev_light_ww.write_value(rng.randint(0, 255))
                await dev_light_white.write_value(rng.randint(0, 255))
                await dev_light_x.write_value(round(0.2 + rng.random() * 0.5, 3))
                await dev_light_y.write_value(round(0.2 + rng.random() * 0.5, 3))
                await dev_light_effect.write_value(rng.choice(effect_cycle))
                await dev_light_transition.write_value(round(0.1 + rng.random() * 3.0, 2))
                await dev_light_flash.write_value(rng.choice(["short", "long", "off"]))
                await dev_last_start.write_value(now)

                await asyncio.sleep(1)
    finally:
        if zeroconf is not None and info is not None:
            try:
                zeroconf.unregister_service(info)
            except Exception:
                pass
            zeroconf.close()


if __name__ == "__main__":
    asyncio.run(main())
