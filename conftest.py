"""根 conftest：session 级配置和环境初始化"""

import pytest
from config.settings import settings


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="测试环境: dev/staging/prod")


@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="session", autouse=True)
def session_setup(env):
    print(f"\n===== 测试开始 | 环境: {env} =====")
    yield
    print(f"\n===== 测试结束 | 环境: {env} =====")
