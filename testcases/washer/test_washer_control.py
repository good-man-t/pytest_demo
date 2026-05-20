"""洗衣机功能测试"""

import pytest
import yaml
from pathlib import Path


def load_washer_data():
    data_path = Path(__file__).parent.parent.parent / "testdata" / "appliance_data.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["washer"]


class TestWasherPower:
    """洗衣机开关机测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.washer
    def test_power_on(self, washer):
        assert washer.power is True

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.washer
    def test_power_off_prevents_start(self, washer):
        """关机状态下无法启动洗涤"""
        washer.power_off()
        result = washer.start_wash()
        assert result["status"] == "error"
        assert "请先开机" in result["message"]


class TestWasherMode:
    """洗衣机模式测试"""

    @pytest.mark.p0
    @pytest.mark.washer
    @pytest.mark.parametrize("mode,desc", load_washer_data()["modes"])
    def test_set_wash_mode(self, washer, mode, desc):
        """参数化：设置洗涤模式"""
        result = washer.set_mode(mode)
        assert result["status"] == "success"

    @pytest.mark.p1
    @pytest.mark.washer
    def test_start_wash_with_quick_mode(self, washer):
        """快洗模式启动后计算剩余时间"""
        washer.set_mode("quick")
        result = washer.start_wash()
        assert result["status"] == "running"
        assert result["remaining_time"] == 15


class TestWasherWaterSettings:
    """洗衣机水位/水温设置测试"""

    @pytest.mark.p1
    @pytest.mark.washer
    @pytest.mark.parametrize("level,desc", load_washer_data()["water_levels"])
    def test_set_water_level(self, washer, level, desc):
        """参数化：设置水位"""
        result = washer.set_water_level(level)
        assert result["status"] == "success"

    @pytest.mark.p1
    @pytest.mark.washer
    @pytest.mark.parametrize("temp,desc", load_washer_data()["water_temps"])
    def test_set_water_temp(self, washer, temp, desc):
        """参数化：设置水温"""
        result = washer.set_water_temp(temp)
        assert result["status"] == "success"

    @pytest.mark.p2
    @pytest.mark.washer
    def test_set_water_temp_out_of_range_raises(self, washer):
        """水温超出范围抛出异常"""
        with pytest.raises(ValueError, match="水温超出范围"):
            washer.set_water_temp(15)
        with pytest.raises(ValueError, match="水温超出范围"):
            washer.set_water_temp(95)


class TestWasherSpin:
    """洗衣机脱水转速测试"""

    @pytest.mark.p1
    @pytest.mark.washer
    @pytest.mark.parametrize("speed,desc", load_washer_data()["spin_speeds"])
    def test_set_spin_speed(self, washer, speed, desc):
        """参数化：设置脱水转速"""
        result = washer.set_spin_speed(speed)
        assert result["status"] == "success"

    @pytest.mark.p2
    @pytest.mark.washer
    def test_set_invalid_spin_speed_raises(self, washer):
        """无效转速抛出异常"""
        with pytest.raises(ValueError, match="无效转速"):
            washer.set_spin_speed(9999)


class TestWasherStatus:
    """洗衣机状态查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.washer
    def test_get_status(self, washer):
        """验证状态字段完整性"""
        washer.set_water_level("medium")
        washer.set_water_temp(40)
        washer.set_spin_speed(1000)
        status = washer.get_status()
        assert status["device_type"] == "washer"
        assert status["water_level"] == "medium"
        assert status["water_temp"] == 40
        assert status["spin_speed"] == 1000
