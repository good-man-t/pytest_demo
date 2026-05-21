"""多门冰箱功能测试"""

import pytest
import yaml
from pathlib import Path
from common.fridge_controller import MultiDoorFridge, FRIDGE_TYPES


def load_data():
    path = Path(__file__).parent.parent.parent / "testdata" / "fridge_data.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestFridgeTypes:
    """多门冰箱类型测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.multi_door
    @pytest.mark.parametrize("fridge_type,name,doors,compartments", data["fridge_types"])
    def test_create_fridge_type(self, fridge_type, name, doors, compartments):
        """参数化：创建所有类型多门冰箱"""
        f = MultiDoorFridge(f"test-{fridge_type}", fridge_type)
        assert f.fridge_type == fridge_type
        assert f.type_info["name"] == name
        assert f.door_count == doors
        assert len(f.compartments) == compartments

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_invalid_fridge_type_raises(self):
        with pytest.raises(ValueError, match="未知冰箱类型"):
            MultiDoorFridge("bad", "unknown_type")

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_all_type_names_are_unique(self):
        names = [info["name"] for info in FRIDGE_TYPES.values()]
        assert len(names) == len(set(names))


class TestTwoDoorFridge:
    """双门冰箱测试"""

    @pytest.mark.p0
    @pytest.mark.multi_door
    def test_two_compartments(self, two_door_fridge):
        f = two_door_fridge
        assert len(f.compartments) == 2
        assert f.door_count == 2

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_fridge_and_freezer_only(self, two_door_fridge):
        """双门只有冷藏和冷冻"""
        comp_names = [c.name for c in two_door_fridge.compartments]
        assert all("冷藏" in n or "冷冻" in n for n in comp_names)


class TestThreeDoorFridge:
    """三门冰箱测试"""

    @pytest.mark.p0
    @pytest.mark.multi_door
    def test_three_compartments_with_variable(self, fridge):
        """三门含变温室"""
        assert len(fridge.compartments) == 3
        names = [c.name for c in fridge.compartments]
        assert any("变温" in n for n in names)

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_variable_temp_wide_range(self, fridge):
        """变温室宽幅调温 -18~5°C"""
        var_comp = fridge.compartments[1]
        assert "变温" in var_comp.name
        assert var_comp.temp_min == -18
        assert var_comp.temp_max == 5

        var_comp.set_temp(-18)
        assert var_comp.current_temp == -18
        var_comp.set_temp(5)
        assert var_comp.current_temp == 5

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_variable_temp_full_range(self, fridge):
        """变温室遍历全温度范围"""
        var_comp = fridge.compartments[1]
        for t in range(-18, 6):
            var_comp.set_temp(t)
            assert var_comp.current_temp == t


class TestFrenchDoorFridge:
    """法式多门冰箱测试"""

    @pytest.mark.p0
    @pytest.mark.multi_door
    def test_four_doors_three_compartments(self, french_door_fridge):
        """法式多门：4门3间室（2冷藏+1冷冻）"""
        f = french_door_fridge
        assert f.door_count == 4
        assert len(f.compartments) == 3

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_duplicate_fridge_compartments(self, french_door_fridge):
        """法式多门冷藏室有2个"""
        compartments = french_door_fridge.compartments
        fridge_names = [c.name for c in compartments if "冷藏" in c.name]
        assert len(fridge_names) == 2


class TestCrossDoorFridge:
    """十字对开门冰箱测试"""

    @pytest.mark.p0
    @pytest.mark.multi_door
    def test_four_doors_four_compartments(self, cross_door_fridge):
        f = cross_door_fridge
        assert f.door_count == 4
        assert len(f.compartments) == 4

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_independent_temp_control(self, cross_door_fridge):
        """每个间室独立控温"""
        comps = cross_door_fridge.compartments
        for i, comp in enumerate(comps):
            midpoint = (comp.temp_min + comp.temp_max) // 2
            comp.set_temp(midpoint)
            assert comp.current_temp == midpoint


class TestTTypeFridge:
    """T型对开门冰箱测试"""

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_three_doors_with_variable(self, t_type_fridge):
        f = t_type_fridge
        assert f.door_count == 3
        assert len(f.compartments) == 3
        names = [c.name for c in f.compartments]
        has_variable = any("变温" in n for n in names)
        assert has_variable, "T型冰箱应有变温室"


class TestMultiDoorOperations:
    """多门操作综合测试"""

    @pytest.mark.p0
    @pytest.mark.multi_door
    def test_all_doors_open_close(self, cross_door_fridge):
        """所有门开/关遍历"""
        f = cross_door_fridge
        for i in range(f.door_count):
            f.open_door(i)
            assert f.get_door_state(i) is True
        assert len(f.get_open_doors()) == f.door_count

        for i in range(f.door_count):
            f.close_door(i)
            assert f.get_door_state(i) is False
        assert f.get_open_doors() == []

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_mode_sync_across_compartments(self, cross_door_fridge):
        """模式切换对所有间室生效"""
        f = cross_door_fridge
        f.set_mode("super_cool")
        assert f.get_status()["mode"] == "super_cool"
        f.set_mode("eco")
        assert f.get_status()["mode"] == "eco"

    @pytest.mark.p1
    @pytest.mark.multi_door
    def test_power_off_resets_mode(self, two_door_fridge):
        """关机后模式回到 standby"""
        f = two_door_fridge
        f.set_mode("eco")
        f.power_off()
        assert f.power is False
        assert f.get_status()["mode"] == "standby"
