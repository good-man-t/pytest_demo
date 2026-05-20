"""洗衣机控制器"""

from common.appliance_base import ApplianceBase


class WasherController(ApplianceBase):
    VALID_MODES = ["standard", "quick", "delicate", "heavy", "rinse_spin", "wool", "self_clean"]
    VALID_WATER_LEVELS = ["low", "medium", "high", "auto"]
    VALID_SPIN_SPEEDS = [400, 600, 800, 1000, 1200, 1400]

    def __init__(self, device_id: str):
        super().__init__(device_id, "washer")
        self._water_level = "auto"
        self._water_temp = 30
        self._rinse_times = 2
        self._spin_speed = 800
        self._remaining_time = 0

    @property
    def remaining_time(self) -> int:
        return self._remaining_time

    def set_water_level(self, level: str) -> dict:
        if level not in self.VALID_WATER_LEVELS:
            raise ValueError(f"无效水位: {level}, 可选: {self.VALID_WATER_LEVELS}")
        self._water_level = level
        return {"device_id": self.device_id, "water_level": level, "status": "success"}

    def set_water_temp(self, temp: int) -> dict:
        if not 20 <= temp <= 90:
            raise ValueError(f"水温超出范围: {temp}, 允许范围 20-90°C")
        self._water_temp = temp
        return {"device_id": self.device_id, "water_temp": temp, "status": "success"}

    def set_spin_speed(self, speed: int) -> dict:
        if speed not in self.VALID_SPIN_SPEEDS:
            raise ValueError(f"无效转速: {speed}, 可选: {self.VALID_SPIN_SPEEDS}")
        self._spin_speed = speed
        return {"device_id": self.device_id, "spin_speed": speed, "status": "success"}

    def start_wash(self) -> dict:
        if not self._power:
            return {"status": "error", "message": "请先开机"}
        mode_times = {
            "quick": 15, "rinse_spin": 20, "delicate": 45,
            "standard": 60, "heavy": 90, "wool": 40, "self_clean": 120,
        }
        self._remaining_time = mode_times.get(self._mode, 60)
        self._mode = "running"
        return {"device_id": self.device_id, "status": "running", "remaining_time": self._remaining_time}

    def get_status(self) -> dict:
        status = super().get_status()
        status.update(
            {
                "water_level": self._water_level,
                "water_temp": self._water_temp,
                "rinse_times": self._rinse_times,
                "spin_speed": self._spin_speed,
                "remaining_time": self._remaining_time,
            }
        )
        return status
