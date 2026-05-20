"""空调控制器"""

from common.appliance_base import ApplianceBase


class ACController(ApplianceBase):
    VALID_MODES = ["cool", "heat", "fan", "dry", "auto"]
    VALID_FAN_SPEEDS = ["low", "medium", "high", "auto"]

    def __init__(self, device_id: str):
        super().__init__(device_id, "ac")
        self._temperature = 26
        self._target_temp = 26
        self._fan_speed = "auto"
        self._swing = False

    @property
    def temperature(self) -> int:
        return self._temperature

    @property
    def fan_speed(self) -> str:
        return self._fan_speed

    def set_temperature(self, temp: int) -> dict:
        if not 16 <= temp <= 30:
            raise ValueError(f"温度超出范围: {temp}, 允许范围 16-30°C")
        self._target_temp = temp
        self._temperature = temp
        return {"device_id": self.device_id, "temperature": temp, "status": "success"}

    def set_fan_speed(self, speed: str) -> dict:
        if speed not in self.VALID_FAN_SPEEDS:
            raise ValueError(f"无效风速: {speed}, 可选: {self.VALID_FAN_SPEEDS}")
        self._fan_speed = speed
        return {"device_id": self.device_id, "fan_speed": speed, "status": "success"}

    def set_swing(self, enable: bool) -> dict:
        self._swing = enable
        return {"device_id": self.device_id, "swing": enable, "status": "success"}

    def get_status(self) -> dict:
        status = super().get_status()
        status.update(
            {
                "temperature": self._temperature,
                "target_temp": self._target_temp,
                "fan_speed": self._fan_speed,
                "swing": self._swing,
            }
        )
        return status
