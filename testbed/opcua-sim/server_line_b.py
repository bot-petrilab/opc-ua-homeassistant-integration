import asyncio
import datetime as dt
import math
import random
import socket

from asyncua import Server, ua
from zeroconf import IPVersion, ServiceInfo, Zeroconf

SIM_VERSION = "0.2.0"


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
    server.set_endpoint("opc.tcp://0.0.0.0:4842")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    uri = "urn:machine-assistant:opcua-sim-lineb"
    idx = await server.register_namespace(uri)

    # Root
    machine = await server.nodes.objects.add_object(f"ns={idx};s=LineB", "LineB")

    # Keep top-level clean: only a few logical groups
    operation = await machine.add_object(f"ns={idx};s=LineB.Operation", "Operation")
    process = await machine.add_object(f"ns={idx};s=LineB.Process", "Process")
    assets = await machine.add_object(f"ns={idx};s=LineB.Assets", "Assets")
    control = await machine.add_object(f"ns={idx};s=LineB.Control", "Control")
    diagnostics = await machine.add_object(f"ns={idx};s=LineB.Diagnostics", "Diagnostics")

    # Assets sub-groups
    assets_energy = await assets.add_object(f"ns={idx};s=LineB.Assets.Energy", "Energy")
    assets_maintenance = await assets.add_object(
        f"ns={idx};s=LineB.Assets.Maintenance", "Maintenance"
    )
    assets_drive = await assets.add_object(f"ns={idx};s=LineB.Assets.Drive", "Drive")
    assets_sensors = await assets.add_object(f"ns={idx};s=LineB.Assets.Sensors", "Sensors")

    # Control sub-groups
    commands = await control.add_object(f"ns={idx};s=LineB.Control.Commands", "Commands")
    setpoints = await control.add_object(f"ns={idx};s=LineB.Control.Setpoints", "Setpoints")
    stack_light = await control.add_object(f"ns={idx};s=LineB.Control.StackLight", "StackLight")

    # Operation
    running = await _add_var(
        operation, f"ns={idx};s=LineB.Operation.Running", "Running", False, writable=True
    )
    alarm = await _add_var(operation, f"ns={idx};s=LineB.Operation.Alarm", "Alarm", False, writable=True)
    warning_active = await _add_var(
        operation, f"ns={idx};s=LineB.Operation.WarningActive", "WarningActive", False, writable=True
    )
    mode = await _add_var(operation, f"ns={idx};s=LineB.Operation.Mode", "Mode", "Idle", writable=True)
    state_code = await _add_var(operation, f"ns={idx};s=LineB.Operation.StateCode", "StateCode", 100)
    heartbeat = await _add_var(operation, f"ns={idx};s=LineB.Operation.Heartbeat", "Heartbeat", 0)
    last_start_utc = await _add_var(
        operation,
        f"ns={idx};s=LineB.Operation.LastStartUtc",
        "LastStartUtc",
        dt.datetime.utcnow(),
    )

    # Process
    temperature = await _add_var(
        process, f"ns={idx};s=LineB.Process.Temperature", "Temperature", 35.0, writable=True
    )
    rpm = await _add_var(process, f"ns={idx};s=LineB.Process.RPM", "RPM", 0, writable=True)
    pressure_bar = await _add_var(
        process, f"ns={idx};s=LineB.Process.PressureBar", "PressureBar", 5.5, writable=True
    )
    flow_l_min = await _add_var(
        process, f"ns={idx};s=LineB.Process.FlowLMin", "FlowLMin", 120.0, writable=True
    )
    humidity_pct = await _add_var(process, f"ns={idx};s=LineB.Process.HumidityPct", "HumidityPct", 40.0)
    vibration_mm_s = await _add_var(
        process, f"ns={idx};s=LineB.Process.VibrationMmS", "VibrationMmS", 1.8
    )

    product_count = await _add_var(
        process, f"ns={idx};s=LineB.Process.ProductCount", "ProductCount", 0, writable=True
    )
    reject_count = await _add_var(
        process, f"ns={idx};s=LineB.Process.RejectCount", "RejectCount", 0, writable=True
    )
    recipe_name = await _add_var(
        process, f"ns={idx};s=LineB.Process.RecipeName", "RecipeName", "Recipe-A", writable=True
    )
    batch_id = await _add_var(
        process, f"ns={idx};s=LineB.Process.BatchId", "BatchId", "BATCH-0001", writable=True
    )

    oee = await _add_var(process, f"ns={idx};s=LineB.Process.OEE", "OEE", 78.0)
    availability = await _add_var(
        process, f"ns={idx};s=LineB.Process.Availability", "Availability", 88.0
    )
    performance = await _add_var(
        process, f"ns={idx};s=LineB.Process.Performance", "Performance", 82.0
    )
    quality_rate = await _add_var(
        process, f"ns={idx};s=LineB.Process.QualityRate", "QualityRate", 96.0
    )

    # Assets/Energy
    power_kw = await _add_var(assets_energy, f"ns={idx};s=LineB.Assets.Energy.PowerKW", "PowerKW", 8.5)
    energy_kwh = await _add_var(
        assets_energy, f"ns={idx};s=LineB.Assets.Energy.EnergyKWh", "EnergyKWh", 0.0
    )
    voltage_v = await _add_var(
        assets_energy, f"ns={idx};s=LineB.Assets.Energy.VoltageV", "VoltageV", 400.0
    )
    current_a = await _add_var(
        assets_energy, f"ns={idx};s=LineB.Assets.Energy.CurrentA", "CurrentA", 12.0
    )
    pf = await _add_var(
        assets_energy, f"ns={idx};s=LineB.Assets.Energy.PowerFactor", "PowerFactor", 0.92
    )

    # Assets/Maintenance
    runtime_hours = await _add_var(
        assets_maintenance,
        f"ns={idx};s=LineB.Assets.Maintenance.RuntimeHours",
        "RuntimeHours",
        0.0,
    )
    next_service_hours = await _add_var(
        assets_maintenance,
        f"ns={idx};s=LineB.Assets.Maintenance.NextServiceHours",
        "NextServiceHours",
        500,
    )
    grease_level_pct = await _add_var(
        assets_maintenance,
        f"ns={idx};s=LineB.Assets.Maintenance.GreaseLevelPct",
        "GreaseLevelPct",
        100.0,
    )

    # Assets/Drive
    axis_position = await _add_var(
        assets_drive, f"ns={idx};s=LineB.Assets.Drive.AxisPosition", "AxisPosition", 0.0, writable=True
    )
    axis_velocity = await _add_var(
        assets_drive, f"ns={idx};s=LineB.Assets.Drive.AxisVelocity", "AxisVelocity", 0.0, writable=True
    )
    axis_accel = await _add_var(
        assets_drive,
        f"ns={idx};s=LineB.Assets.Drive.AxisAcceleration",
        "AxisAcceleration",
        0.0,
    )
    torque_nm = await _add_var(assets_drive, f"ns={idx};s=LineB.Assets.Drive.TorqueNm", "TorqueNm", 15.0)

    # Assets/Sensors
    proximity_1 = await _add_var(
        assets_sensors, f"ns={idx};s=LineB.Assets.Sensors.Proximity1", "Proximity1", False
    )
    proximity_2 = await _add_var(
        assets_sensors, f"ns={idx};s=LineB.Assets.Sensors.Proximity2", "Proximity2", False
    )

    # Diagnostics
    recent_temps = await _add_var(
        diagnostics,
        f"ns={idx};s=LineB.Diagnostics.RecentTemperatures",
        "RecentTemperatures",
        [35.0] * 10,
    )
    recent_errors = await _add_var(
        diagnostics,
        f"ns={idx};s=LineB.Diagnostics.RecentErrorCodes",
        "RecentErrorCodes",
        [0, 0, 0, 0, 0],
    )
    spectrum = await _add_var(
        diagnostics,
        f"ns={idx};s=LineB.Diagnostics.VibrationSpectrum",
        "VibrationSpectrum",
        [0.0] * 16,
    )
    system_message = await _add_var(
        diagnostics,
        f"ns={idx};s=LineB.Diagnostics.SystemMessage",
        "SystemMessage",
        "System OK",
    )
    last_reject_reason = await _add_var(
        diagnostics,
        f"ns={idx};s=LineB.Diagnostics.LastRejectReason",
        "LastRejectReason",
        "None",
    )

    # Control/Commands
    cmd_start = await _add_var(
        commands, f"ns={idx};s=LineB.Control.Commands.Start", "Start", False, writable=True
    )
    cmd_stop = await _add_var(
        commands, f"ns={idx};s=LineB.Control.Commands.Stop", "Stop", False, writable=True
    )
    cmd_reset = await _add_var(
        commands, f"ns={idx};s=LineB.Control.Commands.Reset", "Reset", False, writable=True
    )
    cmd_ack = await _add_var(
        commands,
        f"ns={idx};s=LineB.Control.Commands.Acknowledge",
        "Acknowledge",
        False,
        writable=True,
    )

    # Control/Setpoints
    speed_sp = await _add_var(
        setpoints,
        f"ns={idx};s=LineB.Control.Setpoints.SpeedSetpoint",
        "SpeedSetpoint",
        1800,
        writable=True,
    )
    temp_sp = await _add_var(
        setpoints,
        f"ns={idx};s=LineB.Control.Setpoints.TemperatureSetpoint",
        "TemperatureSetpoint",
        70.0,
        writable=True,
    )
    pressure_sp = await _add_var(
        setpoints,
        f"ns={idx};s=LineB.Control.Setpoints.PressureSetpoint",
        "PressureSetpoint",
        6.0,
        writable=True,
    )

    # Control/StackLight
    stack_light_green = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Green",
        "Green",
        False,
        writable=True,
    )
    stack_light_yellow = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Yellow",
        "Yellow",
        False,
        writable=True,
    )
    stack_light_red = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Red",
        "Red",
        False,
        writable=True,
    )
    stack_light_blue = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Blue",
        "Blue",
        False,
        writable=True,
    )
    stack_light_white = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.White",
        "White",
        False,
        writable=True,
    )
    stack_light_effect = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Effect",
        "Effect",
        "off",
        writable=True,
    )
    stack_light_brightness = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Brightness",
        "Brightness",
        80,
        writable=True,
    )
    stack_light_manual_test = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.ManualTest",
        "ManualTest",
        False,
        writable=True,
    )
    buzzer = await _add_var(
        stack_light,
        f"ns={idx};s=LineB.Control.StackLight.Buzzer",
        "Buzzer",
        False,
        writable=True,
    )

    # Simulation state
    mode_values = ["Idle", "Setup", "Auto", "Alarm"]
    recipe_values = ["Recipe-A", "Recipe-B", "Recipe-C"]
    reject_reasons = ["None", "Dimension", "Surface", "Sensor", "Unknown"]

    mode_idx = 0
    recipe_idx = 0
    msg_idx = 0
    energy_acc = 0.0
    runtime_acc_h = 0.0
    counter = 0

    zeroconf: Zeroconf | None = None
    service_info: ServiceInfo | None = None
    try:
        host_ip = _best_ipv4()
        service_type = "_opcua-tcp._tcp.local."
        service_name = f"Line B OPC UA Simulator {host_ip}.{service_type}"
        service_info = ServiceInfo(
            type_=service_type,
            name=service_name,
            addresses=[socket.inet_aton(host_ip)],
            port=4842,
            properties={
                b"path": b"/",
                b"endpoint": f"opc.tcp://{host_ip}:4842".encode(),
                b"sim_version": SIM_VERSION.encode(),
            },
            server=f"opcua-sim-{host_ip.replace('.', '-')}.local.",
        )
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(service_info)
        print(f"mDNS announced: {service_name}")
    except Exception as err:
        print(f"mDNS announce skipped: {err}")

    try:
        async with server:
            print("OPC UA simulator running at opc.tcp://0.0.0.0:4842")
            print(f"Simulator version: {SIM_VERSION}")
            print(f"Namespace URI: {uri} (ns={idx})")
            print("Top-level under LineB: Operation, Process, Assets, Control, Diagnostics")

            while True:
                counter += 1
    
                start_pressed = bool(await cmd_start.read_value())
                stop_pressed = bool(await cmd_stop.read_value())
                reset_pressed = bool(await cmd_reset.read_value())
                ack_pressed = bool(await cmd_ack.read_value())
    
                is_running = bool(await running.read_value())
                if start_pressed:
                    is_running = True
                    await cmd_start.write_value(False)
                    await last_start_utc.write_value(dt.datetime.utcnow())
                if stop_pressed:
                    is_running = False
                    await cmd_stop.write_value(False)
                if reset_pressed:
                    await alarm.write_value(False)
                    await warning_active.write_value(False)
                    await cmd_reset.write_value(False)
                if ack_pressed:
                    await warning_active.write_value(False)
                    await cmd_ack.write_value(False)
    
                cur_temp = float(await temperature.read_value())
                speed_target = int(await speed_sp.read_value())
                pressure_target = float(await pressure_sp.read_value())
    
                if is_running:
                    cur_temp = min(130.0, cur_temp + random.uniform(0.0, 1.4))
                    cur_rpm = int(max(300, min(3200, speed_target + random.randint(-120, 120))))
                    cur_pressure = max(3.5, min(9.5, pressure_target + random.uniform(-0.4, 0.4)))
                    cur_flow = max(40.0, min(220.0, cur_rpm / 18.0 + random.uniform(-8.0, 8.0)))
                    runtime_acc_h += 1.0 / 3600.0
                else:
                    cur_temp = max(22.0, cur_temp - random.uniform(0.3, 1.2))
                    cur_rpm = 0
                    cur_pressure = max(0.2, pressure_target - random.uniform(1.0, 2.0))
                    cur_flow = 0.0
    
                cur_alarm = cur_temp > 95.0 or cur_pressure < 2.0
                cur_warning = 85.0 < cur_temp <= 95.0
    
                cur_power = 1.2 + (cur_rpm / 400.0) + random.uniform(-0.5, 0.5)
                cur_power = max(0.2, min(22.0, cur_power))
                energy_acc += cur_power / 3600.0
    
                cur_voltage = 400.0 + random.uniform(-6.0, 6.0)
                cur_current = cur_power * 1000.0 / max(cur_voltage * 0.9, 1.0)
                cur_pf = max(0.7, min(0.99, 0.9 + random.uniform(-0.05, 0.05)))
    
                t = counter / 8.0
                pos = 250.0 * math.sin(t / 4.0)
                vel = 120.0 * math.cos(t / 4.0)
                acc = -30.0 * math.sin(t / 4.0)
                torque = max(0.0, min(120.0, abs(vel) / 5.0 + random.uniform(0.0, 8.0)))
    
                prox1 = random.random() > 0.8
                prox2 = random.random() > 0.85
    
                if is_running:
                    pc = int(await product_count.read_value()) + random.randint(1, 4)
                    rc = int(await reject_count.read_value()) + (1 if random.random() < 0.03 else 0)
                else:
                    pc = int(await product_count.read_value())
                    rc = int(await reject_count.read_value())
    
                if counter % 20 == 0:
                    mode_idx = (mode_idx + 1) % len(mode_values)
                if counter % 35 == 0:
                    recipe_idx = (recipe_idx + 1) % len(recipe_values)
    
                if cur_alarm:
                    mode_val = "Alarm"
                    state_val = 400
                elif is_running:
                    mode_val = mode_values[mode_idx]
                    state_val = 300
                else:
                    mode_val = "Idle"
                    state_val = 100
    
                avail = max(40.0, min(99.0, 80.0 + random.uniform(-6, 6)))
                perf = max(30.0, min(99.0, 85.0 + random.uniform(-8, 8)))
                qual = max(70.0, min(100.0, 96.0 - rc / max(pc, 1) * 100.0 + random.uniform(-1.5, 1.5)))
                oee_val = max(20.0, min(98.0, avail * perf * qual / 10000.0))
    
                temps = list(await recent_temps.read_value())
                temps.append(round(cur_temp, 2))
                temps = temps[-10:]
    
                err_codes = [0, 0, 0, 101, 203, 405, 512]
                errs = [random.choice(err_codes) for _ in range(5)]
                if not cur_alarm:
                    errs = [0, 0, 0, 0, 0]
    
                vib_base = max(0.2, min(7.5, abs(vel) / 40.0 + random.uniform(0.0, 1.0)))
                spec = [round(vib_base * random.uniform(0.3, 1.2), 3) for _ in range(16)]
    
                green = is_running and not cur_alarm
                yellow = cur_warning and not cur_alarm
                red = cur_alarm
                blue = not is_running and not cur_alarm
                white = random.random() > 0.94
                effect = "flash" if cur_alarm else ("blink" if cur_warning else "off")
                brightness = 100 if cur_alarm else (85 if is_running else 50)
    
                await running.write_value(is_running)
                await alarm.write_value(cur_alarm)
                await warning_active.write_value(cur_warning)
    
                await temperature.write_value(round(cur_temp, 2))
                await rpm.write_value(cur_rpm)
                await pressure_bar.write_value(round(cur_pressure, 2))
                await flow_l_min.write_value(round(cur_flow, 2))
                await humidity_pct.write_value(round(35.0 + random.uniform(0, 25), 1))
                await vibration_mm_s.write_value(round(vib_base, 2))
    
                await mode.write_value(mode_val)
                await state_code.write_value(state_val)
                await heartbeat.write_value(counter)
    
                await product_count.write_value(pc)
                await reject_count.write_value(rc)
                await recipe_name.write_value(recipe_values[recipe_idx])
                await batch_id.write_value(f"BATCH-{(counter // 50) + 1:04d}")
    
                await power_kw.write_value(round(cur_power, 2))
                await energy_kwh.write_value(round(energy_acc, 3))
                await voltage_v.write_value(round(cur_voltage, 1))
                await current_a.write_value(round(cur_current, 2))
                await pf.write_value(round(cur_pf, 3))
    
                await availability.write_value(round(avail, 2))
                await performance.write_value(round(perf, 2))
                await quality_rate.write_value(round(qual, 2))
                await oee.write_value(round(oee_val, 2))
                await last_reject_reason.write_value(random.choice(reject_reasons))
    
                await runtime_hours.write_value(round(runtime_acc_h, 3))
                await next_service_hours.write_value(max(0, 500 - int(runtime_acc_h)))
                await grease_level_pct.write_value(max(0.0, round(100.0 - runtime_acc_h * 0.02, 2)))
    
                await proximity_1.write_value(prox1)
                await proximity_2.write_value(prox2)
                await axis_position.write_value(round(pos, 3))
                await axis_velocity.write_value(round(vel, 3))
                await axis_accel.write_value(round(acc, 3))
                await torque_nm.write_value(round(torque, 2))
    
                await recent_temps.write_value(temps)
                await recent_errors.write_value(errs)
                await spectrum.write_value(spec)
                msg_idx = (msg_idx + 1) % 4
                await system_message.write_value(
                    ["System OK", "Monitoring active", "No maintenance required", "Ready for command"][msg_idx]
                )
    
                await stack_light_green.write_value(green)
                await stack_light_yellow.write_value(yellow)
                await stack_light_red.write_value(red)
                await stack_light_blue.write_value(blue)
                await stack_light_white.write_value(white)
                await stack_light_effect.write_value(effect)
                await stack_light_brightness.write_value(brightness)
                await buzzer.write_value(cur_alarm and random.random() > 0.5)
    
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
