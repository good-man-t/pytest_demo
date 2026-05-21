"""制冷家电电子系统自动化测试台 —— 全局配置"""

import os


class Settings:
    # ===== 基础环境 =====
    ENV = os.getenv("TEST_ENV", "dev")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8080/api/v1")

    # ===== 数据库 =====
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "fridge_test")

    # ===== 超时/重试 =====
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    DEVICE_RESPONSE_TIMEOUT = int(os.getenv("DEVICE_RESPONSE_TIMEOUT", "10"))
    RETRY_COUNT = int(os.getenv("RETRY_COUNT", "2"))

    # ===== 冰箱设备 =====
    DEFAULT_FRIDGE_DEVICE_ID = os.getenv("DEFAULT_FRIDGE_DEVICE_ID", "fridge-test-001")

    # ===== 传感器阈值 =====
    NTC_SHORT_THRESHOLD = int(os.getenv("NTC_SHORT_THRESHOLD", "50"))       # 短路判定电阻值(Ω)
    NTC_OPEN_THRESHOLD = int(os.getenv("NTC_OPEN_THRESHOLD", "500000"))     # 断路判定电阻值(Ω)
    DOOR_OPEN_ALARM_SEC = int(os.getenv("DOOR_OPEN_ALARM_SEC", "90"))       # 开门超时告警(秒)
    DEFROST_TRIGGER_TEMP = int(os.getenv("DEFROST_TRIGGER_TEMP", "-10"))    # 化霜触发温度(°C)

    # ===== UART 通信参数 =====
    UART_BAUDRATE = int(os.getenv("UART_BAUDRATE", "9600"))
    UART_TIMEOUT_MS = int(os.getenv("UART_TIMEOUT_MS", "500"))
    UART_RETRY_MAX = int(os.getenv("UART_RETRY_MAX", "3"))

    # ===== I2C 总线参数 =====
    I2C_FREQ_HZ = int(os.getenv("I2C_FREQ_HZ", "100000"))
    I2C_EEPROM_ADDR = int(os.getenv("I2C_EEPROM_ADDR", "0x50"), 16)
    I2C_TEMP_SENSOR_ADDR = int(os.getenv("I2C_TEMP_SENSOR_ADDR", "0x48"), 16)
    I2C_RTC_ADDR = int(os.getenv("I2C_RTC_ADDR", "0x68"), 16)


settings = Settings()
