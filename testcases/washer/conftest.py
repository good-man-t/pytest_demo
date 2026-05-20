"""洗衣机测试专用 fixtures"""

import pytest
from common.washer_controller import WasherController
from config.settings import settings


@pytest.fixture(scope="function")
def washer(device_log):
    """创建洗衣机实例，测试后自动关机清理"""
    washer_ctrl = WasherController(settings.DEFAULT_WASHER_DEVICE_ID)
    washer_ctrl.power_on()
    device_log("洗衣机已开机")
    yield washer_ctrl
    washer_ctrl.power_off()
    device_log("洗衣机已关机")
