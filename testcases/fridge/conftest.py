"""冰箱测试专用 fixtures"""

import pytest
from common.fridge_controller import FridgeController
from config.settings import settings


@pytest.fixture(scope="function")
def fridge(device_log):
    """创建冰箱实例，测试后自动关机清理"""
    fridge_ctrl = FridgeController(settings.DEFAULT_FRIDGE_DEVICE_ID)
    fridge_ctrl.power_on()
    device_log("冰箱已开机")
    yield fridge_ctrl
    fridge_ctrl.power_off()
    device_log("冰箱已关机")
