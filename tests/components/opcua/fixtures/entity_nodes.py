from __future__ import annotations

BASE_ENDPOINT = "opc.tcp://127.0.0.1:4846"

NODE_IDS = {
    "sensor": "ns=2;s=EntityMatrix.Process.Temp",
    "binary_sensor": "ns=2;s=EntityMatrix.Test.Node",
    "switch": "ns=2;s=EntityMatrix.Test.Node",
    "light": "ns=2;s=EntityMatrix.Light.On",
    "button": "ns=2;s=EntityMatrix.Test.Node",
    "climate": "ns=2;s=EntityMatrix.Process.Temp",
    "cover": "ns=2;s=EntityMatrix.Cover.Pos",
    "date": "ns=2;s=EntityMatrix.Test.Node",
    "datetime": "ns=2;s=EntityMatrix.Test.Node",
    "fan": "ns=2;s=EntityMatrix.Test.Node",
    "notify": "ns=2;s=EntityMatrix.Test.Node",
    "number": "ns=2;s=EntityMatrix.Test.Node",
    "scene": "ns=2;s=EntityMatrix.Test.Node",
    "select": "ns=2;s=EntityMatrix.Select.Mode",
    "text": "ns=2;s=EntityMatrix.Text.Value",
    "time": "ns=2;s=EntityMatrix.Test.Node",
    "weather": "ns=2;s=EntityMatrix.Weather.Temp",
}
