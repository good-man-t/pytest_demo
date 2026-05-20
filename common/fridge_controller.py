"""冰箱控制器"""

from common.appliance_base import ApplianceBase


class FridgeController(ApplianceBase):
    VALID_MODES = ["normal", "eco", "super_cool", "super_freeze", "vacation"]

    def __init__(self, device_id: str):
        super().__init__(device_id, "fridge")
        self._fridge_temp = 4
        self._freezer_temp = -18
        self._door_open = False

    @property
    def fridge_temp(self) -> int:
        return self._fridge_temp

    @property
    def freezer_temp(self) -> int:
        return self._freezer_temp

    def set_fridge_temp(self, temp: int) -> dict:
        if not 1 <= temp <= 9:
            raise ValueError(f"冷藏温度超出范围: {temp}, 允许范围 1-9°C")
        self._fridge_temp = temp
        return {"device_id": self.device_id, "fridge_temp": temp, "status": "success"}

    def set_freezer_temp(self, temp: int) -> dict:
        if not -24 <= temp <= -15:
            raise ValueError(f"冷冻温度超出范围: {temp}, 允许范围 -24 ~ -15°C")
        self._freezer_temp = temp
        return {"device_id": self.device_id, "freezer_temp": temp, "status": "success"}

    def get_status(self) -> dict:
        status = super().get_status()
        status.update(
            {
                "fridge_temp": self._fridge_temp,
                "freezer_temp": self._freezer_temp,
            }
        )
        return status
