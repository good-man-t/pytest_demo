"""冰箱测试专用 fixtures"""

import pytest
from common.fridge_controller import MultiDoorFridge
from common.sensor import (
    NTCTempSensor, DoorSensor, HumiditySensor,
    DefrostSensor, AmbientTempSensor,
)
from common.uart_protocol import UARTChannel, UARTFrame, UARTCommand
from common.i2c_protocol import I2CBus, EEPROM, I2CTempSensor, RTC
from config.settings import settings


# ===== 冰箱设备 fixtures =====

@pytest.fixture(scope="function")
def fridge(device_log):
    """创建标准三门冰箱实例"""
    f = MultiDoorFridge(settings.DEFAULT_FRIDGE_DEVICE_ID, "three_door")
    f.power_on()
    device_log(f"{f.type_info['name']}已开机")
    yield f
    f.power_off()
    device_log("冰箱已关机")


@pytest.fixture(scope="function")
def two_door_fridge(device_log):
    f = MultiDoorFridge("fridge-2door-001", "two_door")
    f.power_on()
    yield f
    f.power_off()


@pytest.fixture(scope="function")
def french_door_fridge(device_log):
    f = MultiDoorFridge("fridge-french-001", "french_door")
    f.power_on()
    yield f
    f.power_off()


@pytest.fixture(scope="function")
def cross_door_fridge(device_log):
    f = MultiDoorFridge("fridge-cross-001", "cross_door")
    f.power_on()
    yield f
    f.power_off()


@pytest.fixture(scope="function")
def t_type_fridge(device_log):
    f = MultiDoorFridge("fridge-ttype-001", "t_type_door")
    f.power_on()
    yield f
    f.power_off()


# ===== 传感器 fixtures =====

@pytest.fixture(scope="function")
def ntc():
    return NTCTempSensor("NTC-R1")


@pytest.fixture(scope="function")
def ntc_freezer():
    return NTCTempSensor("NTC-F1")


@pytest.fixture(scope="function")
def door_sensor():
    return DoorSensor("冷藏室门")


@pytest.fixture(scope="function")
def humidity():
    return HumiditySensor("HUM-1")


@pytest.fixture(scope="function")
def defrost():
    return DefrostSensor("DEF-1")


@pytest.fixture(scope="function")
def ambient():
    return AmbientTempSensor("AMB-1")


# ===== UART fixtures =====

@pytest.fixture(scope="function")
def uart():
    return UARTChannel(settings.UART_TIMEOUT_MS, settings.UART_RETRY_MAX)


# ===== I2C fixtures =====

@pytest.fixture(scope="function")
def i2c_bus():
    bus = I2CBus()
    bus.register(EEPROM(settings.I2C_EEPROM_ADDR))
    bus.register(I2CTempSensor(settings.I2C_TEMP_SENSOR_ADDR))
    bus.register(RTC(settings.I2C_RTC_ADDR))
    return bus


@pytest.fixture(scope="function")
def eeprom():
    e = EEPROM()
    e.clear_all()
    return e


@pytest.fixture(scope="function")
def i2c_temp():
    return I2CTempSensor()


@pytest.fixture(scope="function")
def rtc():
    return RTC()
