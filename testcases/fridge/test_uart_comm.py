"""UART 通信协议测试

覆盖：帧打包/解包、CRC16 校验、转义处理、命令构建、通道收发、异常帧检测
"""

import pytest
import yaml
from pathlib import Path
from common.uart_protocol import (
    UARTFrame, UARTChannel, UARTCommand,
    pack_frame, unpack_frame, crc16, escape_data, unescape_data,
    make_query_temp_frame, make_set_temp_frame, make_mode_frame,
    ESCAPE, SOI, EOI,
)


def load_data():
    path = Path(__file__).parent.parent.parent / "testdata" / "fridge_data.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestUARTFrame:
    """帧构建/解析测试"""

    @pytest.mark.p0
    @pytest.mark.uart
    def test_create_frame(self):
        frame = UARTFrame(0x01, 0x02, b'\x01\x02')
        assert frame.addr == 1
        assert frame.cmd == 2
        assert frame.data == b'\x01\x02'

    @pytest.mark.p0
    @pytest.mark.uart
    def test_pack_unpack_roundtrip(self):
        """打包再解包应一致"""
        frame = UARTFrame(0x01, UARTCommand.QUERY_TEMP, bytes([0]))
        raw = pack_frame(frame)
        unpacked = unpack_frame(raw)
        assert unpacked is not None
        assert unpacked.addr == frame.addr
        assert unpacked.cmd == frame.cmd
        assert unpacked.data == frame.data

    @pytest.mark.p1
    @pytest.mark.uart
    def test_pack_unpack_with_data(self):
        for length in [0, 1, 10, 255]:
            frame = UARTFrame(0x02, 0x04, bytes(range(length)))
            raw = pack_frame(frame)
            unpacked = unpack_frame(raw)
            assert unpacked is not None
            assert unpacked.data == frame.data

    @pytest.mark.p2
    @pytest.mark.uart
    def test_data_too_long_raises(self):
        with pytest.raises(ValueError, match="长度不能超过"):
            UARTFrame(0x01, 0x01, bytes(300))


class TestCRC16:
    """CRC16 校验测试"""

    @pytest.mark.p1
    @pytest.mark.uart
    def test_crc16_same_input_same_output(self):
        a = crc16(b'\x01\x02\x03')
        b = crc16(b'\x01\x02\x03')
        assert a == b

    @pytest.mark.p1
    @pytest.mark.uart
    def test_crc16_different_input_different_output(self):
        a = crc16(b'\x01\x02\x03')
        b = crc16(b'\x01\x02\x04')
        assert a != b

    @pytest.mark.p2
    @pytest.mark.uart
    def test_crc16_empty_data(self):
        assert crc16(b'') == 0xFFFF

    @pytest.mark.p1
    @pytest.mark.uart
    def test_crc16_detects_corruption(self):
        """CRC 应检测到数据损坏"""
        frame = UARTFrame(0x01, UARTCommand.QUERY_TEMP, bytes([0]))
        raw = bytearray(pack_frame(frame))
        raw[3] ^= 0x01  # 翻转数据位
        assert unpack_frame(bytes(raw)) is None


class TestEscape:
    """转义处理测试"""

    data = load_data()

    @pytest.mark.p1
    @pytest.mark.uart
    @pytest.mark.parametrize("byte_val,desc", data["uart"]["escape_test_data"])
    def test_escape_roundtrip(self, byte_val, desc):
        data = bytes([byte_val])
        escaped = escape_data(data)
        unescaped = unescape_data(escaped)
        assert unescaped == data, desc

    @pytest.mark.p1
    @pytest.mark.uart
    def test_soi_is_escaped_in_data(self):
        data = bytes([SOI])
        escaped = escape_data(data)
        assert SOI not in escaped[1:]  # SOI 不应出现在转义后数据中
        assert ESCAPE in escaped

    @pytest.mark.p2
    @pytest.mark.uart
    def test_frame_contains_soi_at_start_and_end(self):
        """帧必须以 SOI 开头 EOI 结尾"""
        frame = UARTFrame(0x01, 0x01)
        raw = pack_frame(frame)
        assert raw[0] == SOI
        assert raw[-1] == EOI


class TestUARTCommands:
    """命令构建测试"""

    data = load_data()

    @pytest.mark.p1
    @pytest.mark.uart
    @pytest.mark.parametrize("cmd_id,desc", data["uart"]["commands"])
    def test_command_enum_values(self, cmd_id, desc):
        """验证命令码定义"""
        assert cmd_id in [c.value for c in UARTCommand]

    @pytest.mark.p1
    @pytest.mark.uart
    def test_make_query_temp(self):
        frame = make_query_temp_frame(0x01, compartment=0)
        assert frame.cmd == UARTCommand.QUERY_TEMP
        assert frame.data == bytes([0])

    @pytest.mark.p1
    @pytest.mark.uart
    def test_make_set_temp(self):
        frame = make_set_temp_frame(0x01, 2, -18)
        assert frame.cmd == UARTCommand.SET_TEMP
        assert frame.data[0] == 2       # 间室号
        assert frame.data[1] & 0xFF == (-18 & 0xFF)

    @pytest.mark.p1
    @pytest.mark.uart
    def test_make_mode(self):
        frame = make_mode_frame(0x01, 2)  # 速冷模式
        assert frame.cmd == UARTCommand.SET_MODE
        assert frame.data == bytes([2])


class TestUARTChannel:
    """通道通信测试"""

    @pytest.mark.p0
    @pytest.mark.uart
    def test_send_frame(self, uart):
        frame = make_query_temp_frame(0x01)
        raw = uart.send(frame)
        assert raw[0] == SOI and raw[-1] == EOI
        assert uart.sent_count == 1

    @pytest.mark.p0
    @pytest.mark.uart
    def test_send_with_reply(self, uart):
        """发送后收到对应回复"""
        frame = make_query_temp_frame(0x01)
        uart.inject_reply(0x01, UARTCommand.QUERY_TEMP, b'\x04')  # 回复 4°C
        reply, retries = uart.send_with_retry(frame)
        assert reply is not None
        assert reply.cmd == UARTCommand.QUERY_TEMP
        assert retries == 0

    @pytest.mark.p1
    @pytest.mark.uart
    def test_retry_on_no_reply(self, uart):
        """无回复时重试"""
        frame = make_query_temp_frame(0x01)
        reply, retries = uart.send_with_retry(frame)
        assert reply is None
        assert retries == uart.retry_max
        assert uart.error_count == 1

    @pytest.mark.p1
    @pytest.mark.uart
    def test_receive_none_when_empty(self, uart):
        assert uart.receive() is None

    @pytest.mark.p2
    @pytest.mark.uart
    def test_corrupted_frame_not_accepted(self, uart):
        """损坏帧应被拒绝"""
        frame = UARTFrame(0x01, 0x02, b'\x00')
        corrupted = uart.corrupt_data(frame, flip_byte=2)
        result = unpack_frame(corrupted)
        assert result is None

    @pytest.mark.p2
    @pytest.mark.uart
    def test_empty_frame_rejected(self):
        assert unpack_frame(b'') is None
        assert unpack_frame(b'\x7E\x7E') is None
