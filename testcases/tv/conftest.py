"""电视测试专用 fixtures"""

import pytest
from common.tv_controller import TVController
from config.settings import settings


@pytest.fixture(scope="function")
def tv(device_log):
    """创建电视实例，测试后自动关机清理"""
    tv_ctrl = TVController(settings.DEFAULT_TV_DEVICE_ID)
    tv_ctrl.power_on()
    device_log("电视已开机")
    yield tv_ctrl
    tv_ctrl.power_off()
    device_log("电视已关机")
