"""电视控制器"""

from common.appliance_base import ApplianceBase


class TVController(ApplianceBase):
    VALID_MODES = ["standard", "movie", "sports", "game", "eco"]
    VALID_SOURCES = ["hdmi1", "hdmi2", "av", "tv", "usb"]

    def __init__(self, device_id: str):
        super().__init__(device_id, "tv")
        self._volume = 20
        self._channel = 1
        self._source = "hdmi1"
        self._brightness = 50

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def channel(self) -> int:
        return self._channel

    def set_volume(self, volume: int) -> dict:
        if not 0 <= volume <= 100:
            raise ValueError(f"音量超出范围: {volume}, 允许范围 0-100")
        self._volume = volume
        return {"device_id": self.device_id, "volume": volume, "status": "success"}

    def set_channel(self, channel: int) -> dict:
        if not 1 <= channel <= 999:
            raise ValueError(f"频道超出范围: {channel}, 允许范围 1-999")
        self._channel = channel
        return {"device_id": self.device_id, "channel": channel, "status": "success"}

    def set_source(self, source: str) -> dict:
        if source not in self.VALID_SOURCES:
            raise ValueError(f"无效输入源: {source}, 可选: {self.VALID_SOURCES}")
        self._source = source
        return {"device_id": self.device_id, "source": source, "status": "success"}

    def set_brightness(self, brightness: int) -> dict:
        if not 0 <= brightness <= 100:
            raise ValueError(f"亮度超出范围: {brightness}, 允许范围 0-100")
        self._brightness = brightness
        return {"device_id": self.device_id, "brightness": brightness, "status": "success"}

    def get_status(self) -> dict:
        status = super().get_status()
        status.update(
            {
                "volume": self._volume,
                "channel": self._channel,
                "source": self._source,
                "brightness": self._brightness,
            }
        )
        return status
