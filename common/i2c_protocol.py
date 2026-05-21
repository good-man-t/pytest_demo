"""I2C 总线协议模拟

模拟冰箱主控板通过 I2C 总线与 EEPROM、温度传感器、RTC 等外设的通信。
"""

from datetime import datetime


class I2CDevice:
    """I2C 从设备基类"""

    def __init__(self, addr: int, name: str = ""):
        self.addr = addr
        self.name = name or f"DEV_0x{addr:02X}"

    def read(self, reg: int, length: int = 1) -> bytes:
        raise NotImplementedError

    def write(self, reg: int, data: bytes):
        raise NotImplementedError


class EEPROM(I2CDevice):
    """I2C EEPROM (如 AT24C02，256 字节)

    用于存储冰箱运行参数：温度校准值、运行总时长、故障码历史等。
    """

    SIZE = 256

    def __init__(self, addr: int = 0x50):
        super().__init__(addr, "EEPROM")
        self._memory = bytearray(self.SIZE)

    def read(self, reg: int, length: int = 1) -> bytes:
        if reg < 0 or reg + length > self.SIZE:
            raise ValueError(f"EEPROM 地址越界: reg={reg}, len={length}")
        return bytes(self._memory[reg:reg + length])

    def write(self, reg: int, data: bytes):
        if reg < 0 or reg + len(data) > self.SIZE:
            raise ValueError(f"EEPROM 地址越界: reg={reg}, len={len(data)}")
        self._memory[reg:reg + len(data)] = data

    def read_calibration(self) -> float:
        """读取温度校准值（地址 0x00, 2字节, int16, 单位 0.1°C）"""
        raw = int.from_bytes(self.read(0, 2), "big", signed=True)
        return raw / 10.0

    def write_calibration(self, offset_c: float):
        """写入温度校准值"""
        raw = int(offset_c * 10)
        self.write(0, raw.to_bytes(2, "big", signed=True))

    def read_runtime_hours(self) -> int:
        """读取运行总时长（地址 0x02, 4字节）"""
        return int.from_bytes(self.read(2, 4), "big")

    def write_runtime_hours(self, hours: int):
        self.write(2, hours.to_bytes(4, "big"))

    def read_fault_code(self) -> int:
        """读取最新故障码（地址 0x10）"""
        return self.read(0x10, 1)[0]

    def write_fault_code(self, code: int):
        self.write(0x10, bytes([code & 0xFF]))

    def read_fault_history(self) -> list[int]:
        """读取故障历史（地址 0x10-0x1F, 最多 16 条）"""
        return list(self.read(0x10, 16))

    def clear_all(self):
        """擦除全部 EEPROM（全写0xFF）"""
        self._memory = bytearray([0xFF] * self.SIZE)


class I2CTempSensor(I2CDevice):
    """I2C 温度传感器 (如 TMP117, 16-bit 精度, 0.0625°C/LSB)

    寄存器: 0x00 = TEMP (2B)
    """

    def __init__(self, addr: int = 0x48):
        super().__init__(addr, "I2C_TEMP")
        self._temperature = 25.0
        self._fault = False

    def set_simulated(self, temp_c: float):
        self._temperature = temp_c

    def set_fault(self, fault: bool):
        self._fault = fault

    def read(self, reg: int, length: int = 2) -> bytes:
        if self._fault:
            return b'\x00\x00'
        if reg == 0x00:
            raw = int((self._temperature + 256) / 0.0625)
            return raw.to_bytes(2, "big")
        return b'\x00\x00'

    def write(self, reg: int, data: bytes):
        pass  # TMP117 温度寄存器只读

    def get_temperature(self) -> float:
        """直接获取温度值"""
        raw = int.from_bytes(self.read(0, 2), "big")
        if raw == 0:
            return -256.0  # 故障时最低读数
        return round(raw * 0.0625 - 256.0, 2)


class RTC(I2CDevice):
    """I2C RTC 实时时钟 (如 DS3231)

    寄存器: 0x00=秒, 0x01=分, 0x02=时, 0x03=星期, 0x04=日, 0x05=月, 0x06=年
    闹钟: 0x07-0x09 (秒/分/时), 0x0E=控制
    """

    REG_SEC = 0x00
    REG_MIN = 0x01
    REG_HOUR = 0x02
    REG_DAY = 0x03
    REG_DATE = 0x04
    REG_MONTH = 0x05
    REG_YEAR = 0x06
    REG_ALARM1_SEC = 0x07
    REG_ALARM1_MIN = 0x08
    REG_ALARM1_HOUR = 0x09
    REG_CONTROL = 0x0E

    def __init__(self, addr: int = 0x68):
        super().__init__(addr, "RTC_DS3231")
        self._datetime = datetime(2026, 1, 1, 0, 0, 0)
        self._alarm_enabled = False
        self._alarm_time = (0, 0, 0)

    def set_datetime(self, dt: datetime):
        self._datetime = dt

    def set_alarm(self, hour: int, minute: int, second: int = 0):
        self._alarm_time = (hour, minute, second)

    def enable_alarm(self, enable: bool):
        self._alarm_enabled = enable

    def is_alarm_triggered(self) -> bool:
        if not self._alarm_enabled:
            return False
        h, m, s = self._alarm_time
        return (self._datetime.hour == h and
                self._datetime.minute == m and
                self._datetime.second == s)

    def _bcd_encode(self, val: int) -> int:
        return ((val // 10) << 4) | (val % 10)

    def _bcd_decode(self, bcd: int) -> int:
        return ((bcd >> 4) & 0x0F) * 10 + (bcd & 0x0F)

    def read(self, reg: int, length: int = 1) -> bytes:
        if reg == self.REG_SEC:
            return bytes([self._bcd_encode(self._datetime.second)])
        if reg == self.REG_MIN:
            return bytes([self._bcd_encode(self._datetime.minute)])
        if reg == self.REG_HOUR:
            return bytes([self._bcd_encode(self._datetime.hour)])
        if reg == self.REG_DAY:
            return bytes([self._datetime.isoweekday()])
        if reg == self.REG_DATE:
            return bytes([self._bcd_encode(self._datetime.day)])
        if reg == self.REG_MONTH:
            return bytes([self._bcd_encode(self._datetime.month)])
        if reg == self.REG_YEAR:
            return bytes([self._bcd_encode(self._datetime.year % 100)])
        if reg == self.REG_ALARM1_SEC:
            return bytes([self._bcd_encode(self._alarm_time[2])])
        if reg == self.REG_ALARM1_MIN:
            return bytes([self._bcd_encode(self._alarm_time[1])])
        if reg == self.REG_ALARM1_HOUR:
            return bytes([self._bcd_encode(self._alarm_time[0])])
        if reg == self.REG_CONTROL:
            return bytes([0x01 if self._alarm_enabled else 0x00])
        return b'\x00'

    def write(self, reg: int, data: bytes):
        val = self._bcd_decode(data[0]) if data else 0
        if reg == self.REG_SEC:
            self._datetime = self._datetime.replace(second=val % 60)
        elif reg == self.REG_MIN:
            self._datetime = self._datetime.replace(minute=val % 60)
        elif reg == self.REG_HOUR:
            self._datetime = self._datetime.replace(hour=val % 24)
        elif reg == self.REG_DATE:
            self._datetime = self._datetime.replace(day=max(1, min(31, val)))
        elif reg == self.REG_MONTH:
            self._datetime = self._datetime.replace(month=max(1, min(12, val)))
        elif reg == self.REG_YEAR:
            self._datetime = self._datetime.replace(year=2000 + val % 100)


class I2CBus:
    """I2C 总线控制器"""

    def __init__(self):
        self._devices: dict[int, I2CDevice] = {}

    def register(self, device: I2CDevice):
        self._devices[device.addr] = device

    def unregister(self, addr: int):
        self._devices.pop(addr, None)

    def scan(self) -> list[int]:
        """扫描总线上的设备地址"""
        return sorted(self._devices.keys())

    def read(self, addr: int, reg: int, length: int = 1) -> bytes:
        dev = self._devices.get(addr)
        if dev is None:
            raise OSError(f"I2C 设备未找到: 0x{addr:02X}")
        return dev.read(reg, length)

    def write(self, addr: int, reg: int, data: bytes):
        dev = self._devices.get(addr)
        if dev is None:
            raise OSError(f"I2C 设备未找到: 0x{addr:02X}")
        dev.write(reg, data)
