"""冰箱功能测试"""

import pytest
import yaml
from pathlib import Path


def load_fridge_data():
    data_path = Path(__file__).parent.parent.parent / "testdata" / "appliance_data.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["fridge"]


class TestFridgePower:
    """冰箱开关机测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.fridge
    def test_power_on(self, fridge):
        assert fridge.power is True

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.fridge
    def test_power_off(self, fridge):
        fridge.power_off()
        assert fridge.power is False


class TestFridgeTemperature:
    """冰箱温度控制测试"""

    @pytest.mark.p0
    @pytest.mark.fridge
    @pytest.mark.parametrize("temp,desc", load_fridge_data()["valid_fridge_temps"])
    def test_set_fridge_temp(self, fridge, temp, desc):
        """参数化：设置冷藏室温度"""
        result = fridge.set_fridge_temp(temp)
        assert result["status"] == "success"
        assert fridge.fridge_temp == temp

    @pytest.mark.p1
    @pytest.mark.fridge
    @pytest.mark.parametrize("temp,desc", load_fridge_data()["valid_freezer_temps"])
    def test_set_freezer_temp(self, fridge, temp, desc):
        """参数化：设置冷冻室温度"""
        result = fridge.set_freezer_temp(temp)
        assert result["status"] == "success"
        assert fridge.freezer_temp == temp

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_set_fridge_temp_out_of_range_raises(self, fridge):
        """冷藏温度超出范围抛出异常"""
        with pytest.raises(ValueError, match="冷藏温度超出范围"):
            fridge.set_fridge_temp(10)
        with pytest.raises(ValueError, match="冷藏温度超出范围"):
            fridge.set_fridge_temp(0)

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_set_freezer_temp_out_of_range_raises(self, fridge):
        """冷冻温度超出范围抛出异常"""
        with pytest.raises(ValueError, match="冷冻温度超出范围"):
            fridge.set_freezer_temp(-10)
        with pytest.raises(ValueError, match="冷冻温度超出范围"):
            fridge.set_freezer_temp(-30)

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_default_temperatures(self, fridge):
        """验证默认温度"""
        assert fridge.fridge_temp == 4
        assert fridge.freezer_temp == -18


class TestFridgeMode:
    """冰箱模式测试"""

    @pytest.mark.p1
    @pytest.mark.fridge
    @pytest.mark.parametrize("mode,desc", load_fridge_data()["modes"])
    def test_set_mode(self, fridge, mode, desc):
        """参数化：切换冰箱模式"""
        result = fridge.set_mode(mode)
        assert result["status"] == "success"
        assert fridge.get_status()["mode"] == mode


class TestFridgeStatus:
    """冰箱状态查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.fridge
    def test_get_status(self, fridge):
        """验证状态字段完整性"""
        fridge.set_fridge_temp(3)
        fridge.set_freezer_temp(-20)
        status = fridge.get_status()
        assert status["device_type"] == "fridge"
        assert status["fridge_temp"] == 3
        assert status["freezer_temp"] == -20
        assert "mode" in status
