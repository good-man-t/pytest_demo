"""空调功能测试"""

import pytest
import yaml
from pathlib import Path


def load_ac_data():
    data_path = Path(__file__).parent.parent.parent / "testdata" / "appliance_data.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["ac"]


class TestACPower:
    """空调开关机测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.ac
    def test_power_on(self, ac):
        """验证开机后电源状态"""
        assert ac.power is True
        status = ac.get_status()
        assert status["power"] is True

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.ac
    def test_power_off(self, ac):
        """验证关机后电源状态"""
        ac.power_off()
        assert ac.power is False
        status = ac.get_status()
        assert status["power"] is False

    @pytest.mark.p1
    @pytest.mark.ac
    def test_power_toggle(self, ac):
        """验证反复开关机"""
        ac.power_off()
        assert ac.power is False
        ac.power_on()
        assert ac.power is True


class TestACTemperature:
    """空调温度控制测试"""

    @pytest.mark.p0
    @pytest.mark.ac
    @pytest.mark.parametrize("temp,desc", load_ac_data()["valid_temperatures"])
    def test_set_valid_temperature(self, ac, temp, desc):
        """参数化：设置有效温度"""
        result = ac.set_temperature(temp)
        assert result["status"] == "success"
        assert ac.temperature == temp

    @pytest.mark.p1
    @pytest.mark.ac
    @pytest.mark.parametrize("temp,desc", load_ac_data()["invalid_temperatures"])
    def test_set_invalid_temperature_raises(self, ac, temp, desc):
        """参数化：无效温度应抛出 ValueError"""
        with pytest.raises(ValueError, match="温度超出范围"):
            ac.set_temperature(temp)

    @pytest.mark.p1
    @pytest.mark.ac
    def test_default_temperature(self, ac):
        """验证默认温度为 26°C"""
        assert ac.temperature == 26


class TestACMode:
    """空调模式切换测试"""

    @pytest.mark.p0
    @pytest.mark.ac
    @pytest.mark.parametrize("mode,desc", load_ac_data()["modes"])
    def test_set_mode(self, ac, mode, desc):
        """参数化：切换工作模式"""
        result = ac.set_mode(mode)
        assert result["status"] == "success"
        assert ac.get_status()["mode"] == mode

    @pytest.mark.p2
    @pytest.mark.ac
    def test_set_invalid_mode(self, ac):
        """无效模式应使用基类直接设值（此处基类不过滤）"""
        # 基类 ApplianceBase.set_mode 不校验，将值直接写入
        result = ac.set_mode("invalid_mode")
        assert result["status"] == "success"


class TestACFanSpeed:
    """空调风速控制测试"""

    @pytest.mark.p1
    @pytest.mark.ac
    @pytest.mark.parametrize("speed,desc", load_ac_data()["fan_speeds"])
    def test_set_fan_speed(self, ac, speed, desc):
        """参数化：设置风速"""
        result = ac.set_fan_speed(speed)
        assert result["status"] == "success"
        assert ac.fan_speed == speed

    @pytest.mark.p2
    @pytest.mark.ac
    def test_set_invalid_fan_speed(self, ac):
        """无效风速应抛出 ValueError"""
        with pytest.raises(ValueError, match="无效风速"):
            ac.set_fan_speed("hurricane")


class TestACSwing:
    """空调摆风测试"""

    @pytest.mark.p2
    @pytest.mark.ac
    def test_swing_on(self, ac):
        """开启摆风"""
        result = ac.set_swing(True)
        assert result["status"] == "success"

    @pytest.mark.p2
    @pytest.mark.ac
    def test_swing_off(self, ac):
        """关闭摆风"""
        ac.set_swing(True)
        result = ac.set_swing(False)
        assert result["status"] == "success"


class TestACStatus:
    """空调状态查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.ac
    def test_get_status_contains_keys(self, ac):
        """验证状态返回包含所有必要字段"""
        ac.set_temperature(24)
        ac.set_fan_speed("high")
        ac.set_swing(True)
        status = ac.get_status()
        assert status["device_type"] == "ac"
        assert "temperature" in status
        assert "fan_speed" in status
        assert "swing" in status
        assert status["temperature"] == 24
        assert status["fan_speed"] == "high"
        assert status["swing"] is True
