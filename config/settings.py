"""家电测试平台全局配置"""

import os


class Settings:
    ENV = os.getenv("TEST_ENV", "dev")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8080/api/v1")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "appliance_test")

    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    DEVICE_RESPONSE_TIMEOUT = int(os.getenv("DEVICE_RESPONSE_TIMEOUT", "10"))
    RETRY_COUNT = int(os.getenv("RETRY_COUNT", "2"))

    DEFAULT_AC_DEVICE_ID = os.getenv("DEFAULT_AC_DEVICE_ID", "ac-test-001")
    DEFAULT_FRIDGE_DEVICE_ID = os.getenv("DEFAULT_FRIDGE_DEVICE_ID", "fridge-test-001")
    DEFAULT_WASHER_DEVICE_ID = os.getenv("DEFAULT_WASHER_DEVICE_ID", "washer-test-001")
    DEFAULT_TV_DEVICE_ID = os.getenv("DEFAULT_TV_DEVICE_ID", "tv-test-001")


settings = Settings()
