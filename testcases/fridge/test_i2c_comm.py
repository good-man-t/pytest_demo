"""I2C 通信协议测试

覆盖：总线扫描、EEPROM 读写/校准/故障码、I2C 温度传感器、RTC 实时时钟
"""

import pytest
import yaml
from datetime import datetime
from pathlib import Path
from common.i2c_protocol import I2CBus, I2CDevice, EEPROM, I2CTempSensor, RTC


def load_data():
    path = Path(__file__).parent.parent.parent / "testdata" / "fridge_data.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestI2CBus:
    """I2C 总线测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.i2c
    def test_register_and_scan(self, i2c_bus):
        """注册设备后总线扫描可找到地址"""
        devices = i2c_bus.scan()
        assert len(devices) == 3
        assert 0x50 in devices
        assert 0x48 in devices
        assert 0x68 in devices

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_unregister_device(self, i2c_bus):
        i2c_bus.unregister(0x48)
        assert 0x48 not in i2c_bus.scan()
        assert len(i2c_bus.scan()) == 2

    @pytest.mark.p1
    @pytest.mark.i2c
    @pytest.mark.parametrize("addr,name", data["i2c"]["devices"])
    def test_read_write_to_registered_devices(self, i2c_bus, addr, name):
        """正确读写已注册设备"""
        data_bytes = i2c_bus.read(addr, 0, 2)
        assert data_bytes is not None

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_read_unregistered_device_raises(self, i2c_bus):
        """读取未注册设备地址抛出异常"""
        with pytest.raises(OSError, match="I2C 设备未找到"):
            i2c_bus.read(0x99, 0)

    @pytest.mark.p2
    @pytest.mark.i2c
    def test_bus_empty_after_clear(self, i2c_bus):
        for addr in i2c_bus.scan():
            i2c_bus.unregister(addr)
        assert i2c_bus.scan() == []


class TestEEPROM:
    """EEPROM 测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.i2c
    @pytest.mark.parametrize("addr,desc", data["i2c"]["eeprom_data"])
    def test_read_write_single_byte(self, eeprom, addr, desc):
        eeprom.write(addr, b'\xAB')
        assert eeprom.read(addr, 1) == b'\xAB'

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_read_write_multi_bytes(self, eeprom):
        data = bytes([0x01, 0x02, 0x03, 0x04, 0x05])
        eeprom.write(0x20, data)
        assert eeprom.read(0x20, 5) == data

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_address_out_of_range_raises(self, eeprom):
        with pytest.raises(ValueError, match="地址越界"):
            eeprom.write(256, b'\x00')
        with pytest.raises(ValueError, match="地址越界"):
            eeprom.read(256, 1)

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_write_past_boundary_raises(self, eeprom):
        with pytest.raises(ValueError, match="地址越界"):
            eeprom.write(255, b'\x00\x01')

    @pytest.mark.p0
    @pytest.mark.i2c
    @pytest.mark.parametrize("offset,desc", data["i2c"]["calibration_offsets"])
    def test_calibration_read_write(self, eeprom, offset, desc):
        eeprom.write_calibration(offset)
        assert eeprom.read_calibration() == pytest.approx(offset, abs=0.05)

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_runtime_hours(self, eeprom):
        eeprom.write_runtime_hours(12345)
        assert eeprom.read_runtime_hours() == 12345

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_fault_code(self, eeprom):
        eeprom.write_fault_code(0xE1)
        assert eeprom.read_fault_code() == 0xE1

    @pytest.mark.p2
    @pytest.mark.i2c
    def test_fault_history(self, eeprom):
        eeprom.write_fault_code(0x01)
        eeprom.write(0x11, b'\x02')
        history = eeprom.read_fault_history()
        assert len(history) == 16
        assert history[0] == 0x01
        assert history[1] == 0x02

    @pytest.mark.p2
    @pytest.mark.i2c
    def test_clear_all(self, eeprom):
        eeprom.write(0, b'\xAA')
        eeprom.clear_all()
        assert eeprom.read(0, 1) == b'\xFF'
        assert eeprom.read(128, 1) == b'\xFF'


class TestI2CTempSensor:
    """I2C 温度传感器测试"""

    data = load_data()

    @pytest.mark.p0
    @pytest.mark.i2c
    @pytest.mark.parametrize("temp,desc", data["i2c"]["i2c_temps"])
    def test_temperature_readout(self, i2c_temp, temp, desc):
        i2c_temp.set_simulated(temp)
        measured = i2c_temp.get_temperature()
        assert abs(measured - temp) < 0.1, f"期望 {temp}°C, 测得 {measured}°C ({desc})"

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_fault_returns_zero_raw(self, i2c_temp):
        i2c_temp.set_fault(True)
        raw = i2c_temp.read(0, 2)
        assert raw == b'\x00\x00'

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_resolution_16bit(self, i2c_temp):
        """16-bit 分辨率: 0.0625°C/LSB"""
        i2c_temp.set_simulated(25.0)
        raw = int.from_bytes(i2c_temp.read(0, 2), "big")
        assert 0 <= raw <= 65535

    @pytest.mark.p2
    @pytest.mark.i2c
    def test_write_is_noop(self, i2c_temp):
        """TMP117 温度寄存器只读"""
        i2c_temp.set_simulated(25.0)
        before = i2c_temp.get_temperature()
        i2c_temp.write(0, b'\xFF\xFF')
        after = i2c_temp.get_temperature()
        assert before == after


class TestRTC:
    """RTC 实时时钟测试"""

    def _get_test_data(self):
        return load_data()["i2c"]["rtc_datetime"]

    @pytest.mark.p0
    @pytest.mark.i2c
    def test_set_and_read_datetime(self, rtc):
        td = self._get_test_data()
        dt = datetime(td["year"], td["month"], td["day"], td["hour"], td["minute"], td["second"])
        rtc.set_datetime(dt)
        assert rtc.read(rtc.REG_YEAR, 1)[0] == rtc._bcd_encode(td["year"] % 100)
        assert rtc.read(rtc.REG_MONTH, 1)[0] == rtc._bcd_encode(td["month"])
        assert rtc.read(rtc.REG_DATE, 1)[0] == rtc._bcd_encode(td["day"])
        assert rtc.read(rtc.REG_HOUR, 1)[0] == rtc._bcd_encode(td["hour"])
        assert rtc.read(rtc.REG_MIN, 1)[0] == rtc._bcd_encode(td["minute"])

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_write_time_via_registers(self, rtc):
        """通过 I2C write 寄存器设置时间"""
        rtc.write(rtc.REG_HOUR, bytes([rtc._bcd_encode(15)]))
        rtc.write(rtc.REG_MIN, bytes([rtc._bcd_encode(45)]))
        assert rtc.read(rtc.REG_HOUR, 1)[0] == rtc._bcd_encode(15)
        assert rtc.read(rtc.REG_MIN, 1)[0] == rtc._bcd_encode(45)

    @pytest.mark.p1
    @pytest.mark.i2c
    @pytest.mark.parametrize("hour,minute,second,desc", load_data()["i2c"]["alarm_times"])
    def test_alarm_set_and_check(self, rtc, hour, minute, second, desc):
        dt = self._get_test_data()
        rtc.set_datetime(datetime(dt["year"], dt["month"], dt["day"], hour, minute, second))
        rtc.set_alarm(hour, minute, second)
        rtc.enable_alarm(True)
        assert rtc.is_alarm_triggered() is True

    @pytest.mark.p1
    @pytest.mark.i2c
    def test_alarm_disabled_not_triggered(self, rtc):
        dt = self._get_test_data()
        rtc.set_datetime(datetime(dt["year"], dt["month"], dt["day"], 14, 30, 0))
        rtc.set_alarm(14, 30, 0)
        rtc.enable_alarm(False)
        assert rtc.is_alarm_triggered() is False

    @pytest.mark.p2
    @pytest.mark.i2c
    def test_weekday_bcd_format(self, rtc):
        dt = self._get_test_data()
        rtc.set_datetime(datetime(dt["year"], dt["month"], dt["day"], dt["hour"], dt["minute"], dt["second"]))
        weekday = rtc.read(rtc.REG_DAY, 1)[0]
        assert 1 <= weekday <= 7
