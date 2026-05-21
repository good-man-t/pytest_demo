"""冰箱基础功能测试"""

import pytest
import yaml
from pathlib import Path


def load_data():
    path = Path(__file__).parent.parent.parent / "testdata" / "fridge_data.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestFridgePower:
    """开关机测试"""

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

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_power_toggle(self, fridge):
        fridge.power_off()
        assert fridge.power is False
        fridge.power_on()
        assert fridge.power is True


class TestFridgeTemperature:
    """温度控制测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.fridge
    def test_default_compartment_temps(self, fridge):
        """默认三间室温度：冷藏 4°C, 变温 -7°C, 冷冻 -18°C"""
        comp = fridge.compartments
        assert comp[0].current_temp == 4
        assert comp[1].current_temp == -7
        assert comp[2].current_temp == -18

    @pytest.mark.p0
    @pytest.mark.fridge
    @pytest.mark.parametrize("index,temp,desc", data["multi_door"]["compartment_temps"])
    def test_set_compartment_temp(self, fridge, index, temp, desc):
        result = fridge.set_compartment_temp(index, temp)
        assert result["status"] == "success"
        assert fridge.get_compartment(index).current_temp == temp

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_set_temp_out_of_range_raises(self, fridge):
        with pytest.raises(ValueError, match="温度超出范围"):
            fridge.get_compartment(0).set_temp(10)
        with pytest.raises(ValueError, match="温度超出范围"):
            fridge.get_compartment(2).set_temp(-30)

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_invalid_compartment_index_raises(self, fridge):
        with pytest.raises(ValueError, match="间室索引无效"):
            fridge.get_compartment(10)


class TestFridgeMode:
    """模式切换测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.fridge
    @pytest.mark.parametrize("mode,desc", data["modes"])
    def test_set_mode(self, fridge, mode, desc):
        result = fridge.set_mode(mode)
        assert result["status"] == "success"
        assert fridge.get_status()["mode"] == mode

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_super_cool_lowers_fridge_temp(self, fridge):
        """速冷模式：冷藏间室温度强制降到 1°C"""
        fridge.set_mode("super_cool")
        for comp in fridge.compartments:
            if "冷藏" in comp.name:
                assert comp.current_temp == 1

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_super_freeze_lowers_freezer_temp(self, fridge):
        """速冻模式：冷冻间室温度强制降到 -24°C"""
        fridge.set_mode("super_freeze")
        for comp in fridge.compartments:
            if "冷冻" in comp.name:
                assert comp.current_temp == -24

    @pytest.mark.p2
    @pytest.mark.fridge
    def test_invalid_mode_raises(self, fridge):
        with pytest.raises(ValueError, match="无效模式"):
            fridge.set_mode("invalid")


class TestFridgeDoor:
    """门开关检测测试"""

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_initial_all_doors_closed(self, fridge):
        assert fridge.get_open_doors() == []

    @pytest.mark.p1
    @pytest.mark.fridge
    @pytest.mark.parametrize("index,desc", load_data()["multi_door"]["door_indices"])
    def test_open_door(self, fridge, index, desc):
        fridge.open_door(index)
        assert fridge.get_door_state(index) is True

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_close_door(self, fridge):
        fridge.open_door(0)
        fridge.close_door(0)
        assert fridge.get_door_state(0) is False
        assert fridge.get_open_doors() == []

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_multiple_doors_open(self, fridge):
        fridge.open_door(0)
        fridge.open_door(1)
        assert len(fridge.get_open_doors()) == 2


class TestFridgeStatus:
    """状态查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.fridge
    def test_get_status_keys(self, fridge):
        status = fridge.get_status()
        assert status["device_type"] == "multi_door_fridge"
        assert "fridge_type" in status
        assert "type_name" in status
        assert "compartments" in status
        assert len(status["compartments"]) == 3
        assert status["door_count"] == 3
        assert "doors" in status

    @pytest.mark.p1
    @pytest.mark.fridge
    def test_status_after_operations(self, fridge):
        fridge.set_compartment_temp(0, 2)
        fridge.open_door(1)
        fridge.set_mode("eco")
        status = fridge.get_status()
        assert status["compartments"][0]["current_temp"] == 2
        assert status["compartments"][0]["range"] == "1~9°C"
        assert len(status["open_doors"]) == 1
        assert status["mode"] == "eco"
