from custom_components.opcua.weather import OpcUaWeather

def test_weather_values(coordinator_all):
    e=OpcUaWeather("e","opc.tcp://127.0.0.1:4846",{"name":"W","node_id":"ns=2;s=EntityMatrix.Weather.Temp","humidity_node_id":"ns=2;s=EntityMatrix.Weather.Humidity","pressure_node_id":"ns=2;s=EntityMatrix.Weather.Pressure","wind_speed_node_id":"ns=2;s=EntityMatrix.Weather.Wind","condition_node_id":"ns=2;s=EntityMatrix.Weather.Condition"},coordinator_all)
    assert e.native_temperature==19.0
    assert e.condition=="sunny"
