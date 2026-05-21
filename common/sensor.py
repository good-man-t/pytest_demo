"""冰箱电子系统传感器模拟

模拟 NTC 温度、门磁、湿度、化霜、环境温度等传感器。
每个传感器支持：原始值读取、工程值转换、故障自检、模拟值注入（测试用）。
"""

import time


class NTCTempSensor:
    """NTC 热敏电阻温度传感器

    NTC 特性: 温度升高 → 电阻下降（负温度系数）。
    使用 Steinhart-Hart 简化模型做电阻-温度转换。
    ADC 12-bit 采样，参考电压 3.3V，分压电阻 10kΩ。
    """

    ADC_MAX = 4095
    VREF = 3.3
    R_SERIES = 10000.0  # 分压上拉电阻 10kΩ
    R_T0 = 10000.0      # 25°C 时标称电阻 10kΩ
    B_VALUE = 3950      # NTC B 值
    T0 = 298.15         # 25°C 开尔文温度

    def __init__(self, name: str = "NTC-1"):
        self.name = name
        self._sim_temp = None   # 模拟注入温度, None=使用物理模型
        self._fault = None      # "short" | "open" | None

    def set_simulated(self, temp_c: float | None):
        """注入模拟温度(°C)，设为 None 取消模拟"""
        self._sim_temp = temp_c

    def set_fault(self, fault: str | None):
        """注入故障: 'short' 短路, 'open' 断路, None 正常"""
        if fault not in (None, "short", "open"):
            raise ValueError(f"无效故障类型: {fault}")
        self._fault = fault

    def is_fault(self) -> bool:
        return self._fault is not None

    def read_raw(self) -> int:
        """读取 ADC 原始值 (0-4095)"""
        temp = self._sim_temp if self._sim_temp is not None else 25.0
        if self._fault == "short":
            return self.ADC_MAX
        if self._fault == "open":
            return 0
        resistance = self.R_T0 * pow(2.71828, self.B_VALUE * (1 / (temp + 273.15) - 1 / self.T0))
        voltage = self.VREF * resistance / (self.R_SERIES + resistance)
        return int(voltage / self.VREF * self.ADC_MAX)

    def get_value(self) -> float:
        """获取工程温度值(°C)"""
        adc = self.read_raw()
        if adc >= self.ADC_MAX:
            return -40.0  # 短路 → 最低温度
        if adc <= 0:
            return 125.0  # 断路 → 最高温度
        voltage = adc / self.ADC_MAX * self.VREF
        resistance = self.R_SERIES * voltage / (self.VREF - voltage) if voltage < self.VREF else 1e6
        temp_k = 1 / (1 / self.T0 + (1 / self.B_VALUE) * __import__("math").log(resistance / self.R_T0))
        return round(temp_k - 273.15, 1)


class DoorSensor:
    """门磁开关传感器

    检测冰箱门开/关状态，支持开门超时告警。
    """

    def __init__(self, door_name: str = "door-1"):
        self.door_name = door_name
        self._open = False
        self._open_since = 0.0
        self._alarm_threshold = 90  # 秒

    def set_alarm_threshold(self, seconds: int):
        self._alarm_threshold = seconds

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def open_duration(self) -> float:
        """开门持续秒数，门关则返回 0"""
        if not self._open:
            return 0.0
        return time.time() - self._open_since

    def open_door(self):
        """开门"""
        if not self._open:
            self._open = True
            self._open_since = time.time()

    def close_door(self):
        """关门"""
        self._open = False
        self._open_since = 0.0

    def is_alarm(self) -> bool:
        """开门超时告警"""
        return self._open and self.open_duration >= self._alarm_threshold

    def get_value(self) -> dict:
        return {
            "door": self.door_name,
            "open": self._open,
            "duration": round(self.open_duration, 1),
            "alarm": self.is_alarm(),
        }


class HumiditySensor:
    """湿度传感器 (0-100% RH)"""

    def __init__(self, name: str = "HUM-1"):
        self.name = name
        self._sim_rh = 50.0
        self._fault = False

    def set_simulated(self, rh: float):
        if not 0 <= rh <= 100:
            raise ValueError(f"湿度超出范围: {rh}%")
        self._sim_rh = rh

    def set_fault(self, fault: bool):
        self._fault = fault

    def is_fault(self) -> bool:
        return self._fault

    def get_value(self) -> float:
        if self._fault:
            return -1.0  # 故障标识
        return round(self._sim_rh, 1)


class DefrostSensor:
    """化霜传感器

    检测蒸发器结霜程度，通过温度判断是否需要化霜。
    """

    def __init__(self, name: str = "DEF-1"):
        self.name = name
        self._evap_temp = -5.0  # 蒸发器温度
        self._trigger_temp = -10.0  # 触发化霜阈值
        self._frost_level = 0  # 0-100 结霜程度

    @property
    def frost_level(self) -> int:
        return self._frost_level

    def set_trigger_temp(self, temp: float):
        self._trigger_temp = temp

    def set_simulated(self, temp: float, frost: int = 0):
        self._evap_temp = temp
        self._frost_level = max(0, min(100, frost))

    def should_defrost(self) -> bool:
        """判断是否需要化霜"""
        return self._evap_temp <= self._trigger_temp or self._frost_level >= 80

    def get_value(self) -> dict:
        return {
            "evap_temp": self._evap_temp,
            "frost_level": self._frost_level,
            "should_defrost": self.should_defrost(),
        }

    def is_fault(self) -> bool:
        return self._evap_temp > 125  # 传感器异常高温


class AmbientTempSensor:
    """环境温度传感器

    用于环温补偿，影响压缩机运行策略。
    """

    def __init__(self, name: str = "AMB-1"):
        self.name = name
        self._ambient_temp = 25.0

    def set_simulated(self, temp: float):
        self._ambient_temp = temp

    def get_value(self) -> float:
        return round(self._ambient_temp, 1)

    def is_fault(self) -> bool:
        return not (-30 <= self._ambient_temp <= 60)

    def compensation_offset(self) -> float:
        """环温补偿偏移量：环温高 → 需更强制冷 → 负偏移"""
        if self._ambient_temp > 38:
            return -3.0
        if self._ambient_temp > 32:
            return -2.0
        if self._ambient_temp < 5:
            return 4.0
        if self._ambient_temp < 10:
            return 2.0
        return 0.0
