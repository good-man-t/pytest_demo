"""UART 串口通信协议模拟

模拟冰箱主控板(MCU)与显示板/驱动板之间的 UART 通信。
帧格式: SOI(0x7E) + ADDR(1B) + CMD(1B) + LEN(1B) + DATA(nB) + CRC16(2B) + EOI(0x7E)
"""

import struct
from enum import IntEnum


class UARTCommand(IntEnum):
    QUERY_TEMP = 0x01     # 温度查询
    SET_TEMP = 0x02       # 温度设置
    SET_MODE = 0x03       # 模式设置
    STATUS_REPORT = 0x04  # 状态上报
    FAULT_REPORT = 0x05   # 故障上报


class UARTAddress(IntEnum):
    MAIN_BOARD = 0x01     # 主控板
    DISPLAY_BOARD = 0x02  # 显示板
    DRIVER_BOARD = 0x03   # 驱动板


SOI = 0x7E
EOI = 0x7E
ESCAPE = 0x7D
ESCAPE_MASK = 0x20


class UARTFrame:
    """UART 数据帧"""

    def __init__(self, addr: int, cmd: int, data: bytes = b""):
        if not 0 <= addr <= 255 or not 0 <= cmd <= 255:
            raise ValueError("addr/cmd 必须在 0-255 范围")
        if len(data) > 255:
            raise ValueError("DATA 长度不能超过 255 字节")
        self.addr = addr
        self.cmd = cmd
        self.data = data

    def __repr__(self):
        return f"UARTFrame(addr=0x{self.addr:02X}, cmd=0x{self.cmd:02X}, data={self.data.hex()})"


def crc16(data: bytes) -> int:
    """CRC16-CCITT 校验"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def escape_data(data: bytes) -> bytes:
    """转义处理：SOI/EOI/ESCAPE 数据字节前插入 ESCAPE 并取反"""
    result = bytearray()
    for b in data:
        if b in (SOI, EOI, ESCAPE):
            result.append(ESCAPE)
            result.append(b ^ ESCAPE_MASK)
        else:
            result.append(b)
    return bytes(result)


def unescape_data(data: bytes) -> bytes:
    """反转义处理"""
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == ESCAPE and i + 1 < len(data):
            i += 1
            result.append(data[i] ^ ESCAPE_MASK)
        else:
            result.append(data[i])
        i += 1
    return bytes(result)


def pack_frame(frame: UARTFrame) -> bytes:
    """将帧打包为字节流"""
    payload = bytes([frame.addr, frame.cmd, len(frame.data)]) + frame.data
    payload_escaped = escape_data(payload)
    crc_bytes = struct.pack(">H", crc16(payload))
    crc_escaped = escape_data(crc_bytes)
    return bytes([SOI]) + payload_escaped + crc_escaped + bytes([EOI])


def unpack_frame(raw: bytes) -> UARTFrame | None:
    """从字节流解包帧，失败返回 None"""
    if len(raw) < 6:
        return None
    if raw[0] != SOI or raw[-1] != EOI:
        return None

    body = raw[1:-1]  # 去头尾
    payload_with_crc = unescape_data(body)
    if len(payload_with_crc) < 5:
        return None

    payload = payload_with_crc[:-2]
    crc_received = struct.unpack(">H", payload_with_crc[-2:])[0]
    if crc16(payload) != crc_received:
        return None

    addr, cmd, length = payload[0], payload[1], payload[2]
    data = payload[3:3 + length]
    return UARTFrame(addr, cmd, data)


def make_query_temp_frame(addr: int, compartment: int = 0) -> UARTFrame:
    """构建温度查询帧"""
    return UARTFrame(addr, UARTCommand.QUERY_TEMP, bytes([compartment]))


def make_set_temp_frame(addr: int, compartment: int, temp: int) -> UARTFrame:
    """构建温度设置帧"""
    return UARTFrame(addr, UARTCommand.SET_TEMP, bytes([compartment, temp & 0xFF]))


def make_mode_frame(addr: int, mode: int) -> UARTFrame:
    """构建模式设置帧"""
    return UARTFrame(addr, UARTCommand.SET_MODE, bytes([mode]))


class UARTChannel:
    """UART 通信通道模拟（点对点）"""

    def __init__(self, timeout_ms: int = 500, retry_max: int = 3):
        self.timeout_ms = timeout_ms
        self.retry_max = retry_max
        self._buffer_tx: list[bytes] = []
        self._buffer_rx: list[bytes] = []
        self._sent_count = 0
        self._error_count = 0

    def send(self, frame: UARTFrame) -> bytes:
        """发送帧，等待 ACK"""
        raw = pack_frame(frame)
        self._buffer_tx.append(raw)
        self._sent_count += 1
        return raw

    def send_with_retry(self, frame: UARTFrame) -> tuple[bytes | None, int]:
        """发送帧（带重试），返回（响应帧, 重试次数）"""
        for retry in range(self.retry_max + 1):
            self.send(frame)
            reply = self.receive()
            if reply is not None and reply.cmd == frame.cmd:
                return reply, retry
        self._error_count += 1
        return None, self.retry_max

    def receive(self) -> UARTFrame | None:
        """接收一帧"""
        if self._buffer_rx:
            raw = self._buffer_rx.pop(0)
            return unpack_frame(raw)
        return None

    def inject_frame(self, raw: bytes):
        """注入模拟帧（测试用）"""
        self._buffer_rx.append(raw)

    def inject_reply(self, addr: int, cmd: int, data: bytes = b""):
        """注入回复帧"""
        self.inject_frame(pack_frame(UARTFrame(addr, cmd, data)))

    @property
    def sent_count(self) -> int:
        return self._sent_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def reset_stats(self):
        self._sent_count = 0
        self._error_count = 0

    def corrupt_data(self, frame: UARTFrame, flip_byte: int = 0) -> bytes:
        """制造损坏帧（翻转指定位置字节）用于异常测试"""
        raw = bytearray(pack_frame(frame))
        pos = min(flip_byte, len(raw) - 1)
        raw[pos] ^= 0xFF
        return bytes(raw)
