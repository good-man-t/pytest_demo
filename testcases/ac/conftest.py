"""空调测试专用 fixtures"""

import pytest
from common.ac_controller import ACController
from config.settings import settings


@pytest.fixture(scope="function")
def ac(device_log):
    """创建空调实例，测试后自动关机清理"""
    ac_ctrl = ACController(settings.DEFAULT_AC_DEVICE_ID)
    ac_ctrl.power_on()
    device_log("空调已开机")
    yield ac_ctrl
    ac_ctrl.power_off()
    device_log("空调已关机")
