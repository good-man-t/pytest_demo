"""传感器信号测试

覆盖：NTC温度传感器、门磁开关、湿度传感器、化霜传感器、环温传感器
"""

import pytest
import yaml
from pathlib import Path


def load_data():
    path = Path(__file__).parent.parent.parent / "testdata" / "fridge_data.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["sensor"]


class TestNTCTempSensor:
    """NTC 温度传感器测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.sensor
    def test_default_reading_valid(self, ntc):
        """默认读数应在合理范围"""
        assert not ntc.is_fault()
        temp = ntc.get_value()
        assert -40 <= temp <= 125

    @pytest.mark.p0
    @pytest.mark.sensor
    @pytest.mark.parametrize("temp,desc", data["ntc_temps"])
    def test_simulated_temperature(self, ntc, temp, desc):
        """模拟注入温度，验证 ADC 采样和工程值转换"""
        ntc.set_simulated(temp)
        adc = ntc.read_raw()
        assert 0 <= adc <= 4095
        measured = ntc.get_value()
        assert abs(measured - temp) < 2.0, f"期望 {temp}°C, 测得 {measured}°C"

    @pytest.mark.p1
    @pytest.mark.sensor
    @pytest.mark.parametrize("fault_type,desc", data["ntc_faults"])
    def test_fault_detection(self, ntc, fault_type, desc):
        """NTC 短路/断路故障检测"""
        ntc.set_fault(fault_type)
        assert ntc.is_fault()

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_short_returns_min_temp(self, ntc):
        """短路时返回最低温度"""
        ntc.set_fault("short")
        assert ntc.read_raw() == 4095

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_open_returns_max_temp(self, ntc):
        """断路时 ADC 读数为 0"""
        ntc.set_fault("open")
        assert ntc.read_raw() == 0

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_clear_fault(self, ntc):
        """清除故障后恢复正常"""
        ntc.set_fault("short")
        ntc.set_fault(None)
        assert not ntc.is_fault()

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_ntc_negative_temp_coefficient(self, ntc):
        """NTC 负温度系数特性：温度越高，ADC 读数越低"""
        ntc.set_simulated(-20)
        adc_cold = ntc.read_raw()
        ntc.set_simulated(60)
        adc_hot = ntc.read_raw()
        assert adc_hot < adc_cold, "NTC 应为负温度系数"


class TestDoorSensor:
    """门磁开关传感器测试"""

    @pytest.mark.p0
    @pytest.mark.sensor
    def test_initial_closed(self, door_sensor):
        assert not door_sensor.is_open

    @pytest.mark.p0
    @pytest.mark.sensor
    def test_open_and_close(self, door_sensor):
        door_sensor.open_door()
        assert door_sensor.is_open
        door_sensor.close_door()
        assert not door_sensor.is_open

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_open_duration_reset_on_close(self, door_sensor):
        door_sensor.open_door()
        door_sensor.close_door()
        assert door_sensor.open_duration == 0.0

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_alarm_threshold_exceeded(self, door_sensor):
        """设置极短阈值模拟超时告警"""
        door_sensor.set_alarm_threshold(0)
        door_sensor.open_door()
        assert door_sensor.is_alarm()

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_get_value_dict(self, door_sensor):
        val = door_sensor.get_value()
        assert "door" in val
        assert "open" in val
        assert "duration" in val
        assert "alarm" in val


class TestHumiditySensor:
    """湿度传感器测试"""

    data = load_data()

    @pytest.mark.p1
    @pytest.mark.sensor
    @pytest.mark.parametrize("rh,desc", data["humidity_values"])
    def test_humidity_range(self, humidity, rh, desc):
        humidity.set_simulated(rh)
        assert humidity.get_value() == rh

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_humidity_out_of_range_raises(self, humidity):
        with pytest.raises(ValueError, match="湿度超出范围"):
            humidity.set_simulated(101)

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_fault_returns_minus_one(self, humidity):
        humidity.set_fault(True)
        assert humidity.is_fault()
        assert humidity.get_value() == -1.0


class TestDefrostSensor:
    """化霜传感器测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.sensor
    def test_default_no_defrost_needed(self, defrost):
        """默认状态 -5°C 蒸发器温度 > -10°C 触发阈值，不触发化霜"""
        assert defrost.should_defrost() is False

    @pytest.mark.p0
    @pytest.mark.sensor
    @pytest.mark.parametrize("temp,frost,expected,desc", data["defrost_scenarios"])
    def test_defrost_scenarios(self, defrost, temp, frost, expected, desc):
        defrost.set_simulated(temp, frost)
        assert defrost.should_defrost() == expected, desc

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_frost_level_bounds(self, defrost):
        """结霜程度应在 0-100 范围内"""
        defrost.set_simulated(-10, 150)
        assert 0 <= defrost.frost_level <= 100
        defrost.set_simulated(-10, -50)
        assert 0 <= defrost.frost_level <= 100


class TestAmbientTempSensor:
    """环境温度传感器测试"""

    data = load_data()

    @pytest.mark.p1
    @pytest.mark.sensor
    @pytest.mark.parametrize("temp,expected_offset,desc", data["ambient_temps"])
    def test_compensation_offset(self, ambient, temp, expected_offset, desc):
        ambient.set_simulated(temp)
        assert ambient.compensation_offset() == expected_offset, desc

    @pytest.mark.p1
    @pytest.mark.sensor
    def test_fault_detection(self, ambient):
        ambient.set_simulated(80)
        assert ambient.is_fault()
        ambient.set_simulated(-40)
        assert ambient.is_fault()

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_normal_range_no_fault(self, ambient):
        ambient.set_simulated(25)
        assert not ambient.is_fault()

    @pytest.mark.p2
    @pytest.mark.sensor
    def test_compensation_no_offset_at_room_temp(self, ambient):
        """常温(25°C)无补偿"""
        ambient.set_simulated(25)
        assert ambient.compensation_offset() == 0.0
