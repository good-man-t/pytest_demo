"""家电设备抽象基类，定义通用行为"""


class ApplianceBase:
    def __init__(self, device_id: str, device_type: str):
        self.device_id = device_id
        self.device_type = device_type
        self._power = False
        self._mode = "standby"

    @property
    def power(self) -> bool:
        return self._power

    def power_on(self) -> dict:
        self._power = True
        self._mode = "active"
        return {"device_id": self.device_id, "power": "on", "status": "success"}

    def power_off(self) -> dict:
        self._power = False
        self._mode = "standby"
        return {"device_id": self.device_id, "power": "off", "status": "success"}

    def get_status(self) -> dict:
        return {
            "device_id": self.device_id,
            "power": self._power,
            "mode": self._mode,
            "device_type": self.device_type,
        }

    def set_mode(self, mode: str) -> dict:
        self._mode = mode
        return {"device_id": self.device_id, "mode": mode, "status": "success"}
