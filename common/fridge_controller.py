"""多门冰箱控制器

支持：双门、三门、法式多门、十字对开门、T型对开门
每个间室独立控温、独立门开关检测、模式联动。
"""

from common.appliance_base import ApplianceBase


# 冰箱类型定义
FRIDGE_TYPES = {
    "two_door": {"name": "双门冰箱", "compartments": ["fridge", "freezer"]},
    "three_door": {"name": "三门冰箱", "compartments": ["fridge", "variable", "freezer"]},
    "french_door": {"name": "法式多门", "compartments": ["fridge", "fridge", "freezer"], "doors": 4},
    "cross_door": {"name": "十字对开门", "compartments": ["fridge", "fridge", "freezer", "freezer"], "doors": 4},
    "t_type_door": {"name": "T型对开门", "compartments": ["fridge", "freezer", "variable"], "doors": 3},
}


class Compartment:
    """冰箱间室"""

    def __init__(self, name: str, temp_min: int, temp_max: int, default_temp: int):
        self.name = name
        self.temp_min = temp_min
        self.temp_max = temp_max
        self._target_temp = default_temp
        self._current_temp = default_temp

    @property
    def target_temp(self) -> int:
        return self._target_temp

    @property
    def current_temp(self) -> int:
        return self._current_temp

    def set_temp(self, temp: int) -> dict:
        if not self.temp_min <= temp <= self.temp_max:
            raise ValueError(f"{self.name}温度超出范围: {temp}, 允许 {self.temp_min}~{self.temp_max}°C")
        self._target_temp = temp
        self._current_temp = temp
        return {"compartment": self.name, "temperature": temp, "status": "success"}

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "target_temp": self._target_temp,
            "current_temp": self._current_temp,
            "range": f"{self.temp_min}~{self.temp_max}°C",
        }


class MultiDoorFridge(ApplianceBase):
    """多门冰箱控制器"""

    COMPARTMENT_DEFS = {
        "fridge": {"name": "冷藏室", "min": 1, "max": 9, "default": 4},
        "freezer": {"name": "冷冻室", "min": -24, "max": -15, "default": -18},
        "variable": {"name": "变温室", "min": -18, "max": 5, "default": -7},
        "ice_bar": {"name": "冰吧", "min": -5, "max": 5, "default": 0},
    }
    VALID_MODES = ["normal", "eco", "super_cool", "super_freeze", "vacation"]

    def __init__(self, device_id: str, fridge_type: str = "three_door"):
        super().__init__(device_id, "multi_door_fridge")
        if fridge_type not in FRIDGE_TYPES:
            raise ValueError(f"未知冰箱类型: {fridge_type}, 可选: {list(FRIDGE_TYPES.keys())}")
        self.fridge_type = fridge_type
        self.type_info = FRIDGE_TYPES[fridge_type]
        self._compartments: list[Compartment] = []
        self._door_states: dict[str, bool] = {}
        self._build_compartments()

    def _build_compartments(self):
        """根据冰箱类型构建间室和门"""
        comp_types = self.type_info["compartments"]
        for i, ct in enumerate(comp_types):
            cfg = self.COMPARTMENT_DEFS[ct]
            name = f"{cfg['name']}{i + 1}" if comp_types.count(ct) > 1 else cfg["name"]
            comp = Compartment(name, cfg["min"], cfg["max"], cfg["default"])
            self._compartments.append(comp)

        # 门数使用 type_info 中的 doors 字段，默认等于间室数
        door_num = self.type_info.get("doors", len(comp_types))
        for i in range(door_num):
            door_name = f"门{i + 1}"
            self._door_states[door_name] = False

    @property
    def compartments(self) -> list[Compartment]:
        return self._compartments

    @property
    def door_count(self) -> int:
        return len(self._door_states)

    def get_compartment(self, index: int) -> Compartment:
        if not 0 <= index < len(self._compartments):
            raise ValueError(f"间室索引无效: {index}, 共 {len(self._compartments)} 个间室")
        return self._compartments[index]

    def set_compartment_temp(self, index: int, temp: int) -> dict:
        """设置指定间室温度"""
        comp = self.get_compartment(index)
        result = comp.set_temp(temp)
        result["device_id"] = self.device_id
        return result

    def set_mode(self, mode: str) -> dict:
        """设置模式（含联动逻辑）"""
        if mode not in self.VALID_MODES:
            raise ValueError(f"无效模式: {mode}, 可选: {self.VALID_MODES}")
        result = super().set_mode(mode)
        # 模式联动
        if mode == "super_cool":
            for comp in self._compartments:
                if "冷藏" in comp.name:
                    comp.set_temp(1)
        elif mode == "super_freeze":
            for comp in self._compartments:
                if "冷冻" in comp.name:
                    comp.set_temp(-24)
        result["fridge_type"] = self.fridge_type
        return result

    def open_door(self, door_index: int):
        """开门"""
        door_name = list(self._door_states.keys())[door_index]
        self._door_states[door_name] = True

    def close_door(self, door_index: int):
        """关门"""
        door_name = list(self._door_states.keys())[door_index]
        self._door_states[door_name] = False

    def get_door_state(self, door_index: int) -> bool:
        """获取门状态"""
        door_name = list(self._door_states.keys())[door_index]
        return self._door_states[door_name]

    def get_open_doors(self) -> list[str]:
        """获取所有打开的门"""
        return [name for name, opened in self._door_states.items() if opened]

    def get_status(self) -> dict:
        status = super().get_status()
        status.update({
            "fridge_type": self.fridge_type,
            "type_name": self.type_info["name"],
            "compartments": [c.get_status() for c in self._compartments],
            "doors": {name: "open" if opened else "closed" for name, opened in self._door_states.items()},
            "open_doors": self.get_open_doors(),
            "door_count": self.door_count,
            "compartment_count": len(self._compartments),
        })
        return status
