"""testcases 层 conftest：模块级公共 fixtures"""

import pytest


@pytest.fixture(scope="function")
def device_log():
    """记录每次测试的设备操作日志"""
    logs = []

    def _log(msg):
        logs.append(msg)
        print(f"[DEVICE] {msg}")

    yield _log
    if logs:
        print(f"\n[LOG] 本次测试操作记录: {len(logs)} 条")
