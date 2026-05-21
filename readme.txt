================================================================================
                       制冷家电电子系统自动化测试台
                 Refrigeration Appliance Electronic System
                           Automation Test Bench
================================================================================

【项目简介】
  本项目是基于 pytest 的制冷家电（冰箱/冷柜）电子系统自动化测试框架。
  覆盖多门冰箱功能测试、传感器信号采集、UART/I2C 通信协议验证。

【环境要求】
  Python >= 3.10
  pytest >= 7.4.0

【快速开始】

  1. 安装依赖
     $ pip install -r requirements.txt

  2. 执行全部测试
     $ pytest

  3. 按模块筛选执行
     $ pytest -m fridge         # 冰箱基础功能
     $ pytest -m multi_door     # 多门冰箱功能
     $ pytest -m sensor         # 传感器信号测试
     $ pytest -m uart           # UART 通信协议测试
     $ pytest -m i2c            # I2C 通信协议测试

  4. 按优先级筛选
     $ pytest -m smoke          # 冒烟测试
     $ pytest -m p0             # P0 核心用例
     $ pytest -m p1             # P1 重要用例

  5. 指定测试环境
     $ pytest --env staging
     $ pytest --env prod

  6. 并发执行
     $ pytest -n auto

【项目结构】

  pytestDemo/
  ├── pytest.ini              # pytest 配置（markers、报告路径）
  ├── requirements.txt        # Python 依赖
  ├── conftest.py             # 全局 fixtures（session 级）
  ├── config/
  │   └── settings.py         # 全局配置（环境变量、传感器/UART/I2C 参数）
  ├── common/
  │   ├── appliance_base.py   # 家电设备抽象基类
  │   ├── fridge_controller.py# 多门冰箱控制器（5种类型）
  │   ├── sensor.py           # 传感器模拟（NTC/门磁/湿度/化霜/环温）
  │   ├── uart_protocol.py    # UART 通信协议（帧格式/CRC/转义）
  │   └── i2c_protocol.py     # I2C 总线协议（EEPROM/传感器/RTC）
  ├── testdata/
  │   └── fridge_data.yaml    # YAML 参数化测试数据
  ├── testcases/
  │   └── fridge/
  │       ├── conftest.py     # 冰箱模块 fixtures
  │       ├── test_fridge_basic.py      # 基础功能（开关机/温度/模式）
  │       ├── test_multi_door.py        # 多门冰箱（5种类型间室控温）
  │       ├── test_sensor.py            # 传感器信号（ADC/故障/阈值）
  │       ├── test_uart_comm.py         # UART 协议（帧/校验/重试）
  │       └── test_i2c_comm.py          # I2C 协议（EEPROM/RTC/传感器）
  └── reports/
      ├── allure-results/     # Allure 源数据
      └── report.html         # pytest-html 报告

【多门冰箱类型】

  类型           间室数  门数  说明
  -------------------------------------------------
  two_door       2      2     双门冰箱（冷藏+冷冻）
  three_door     3      3     三门冰箱（冷藏+变温+冷冻）
  french_door    3      4     法式多门（2冷藏+冷冻）
  cross_door     4      4     十字对开门（2冷藏+2冷冻）
  t_type_door    3      3     T型对开门（冷藏+冷冻+变温）

  间室温度范围：
    冷藏室:   1 ~ 9 °C
    冷冻室:  -24 ~ -15 °C
    变温室:  -18 ~ 5 °C
    冰吧:    -5 ~ 5 °C

【传感器模块】

  传感器          接口      功能
  -------------------------------------------------
  NTCTempSensor   模拟ADC   NTC 热敏电阻温度采集、短路/断路检测
  DoorSensor      数字IO    门磁开关状态、开门超时告警
  HumiditySensor  模拟ADC   湿度采集 (0-100% RH)
  DefrostSensor   模拟ADC   蒸发器结霜检测、化霜触发判断
  AmbientTempSensor 模拟ADC 环境温度采集、环温补偿算法

【UART 协议】
  帧格式: SOI(0x7E) + ADDR + CMD + LEN + DATA + CRC16 + EOI(0x7E)
  命令集: 温度查询(0x01) 温度设置(0x02) 模式设置(0x03)
          状态上报(0x04) 故障上报(0x05)
  CRC16:  CCITT 标准多项式 0x1021
  转义:   0x7D + (原字节 ^ 0x20)

【I2C 协议】
  外设地址:
    0x50  AT24C02 EEPROM (256字节，存储校准值/运行时长/故障码)
    0x48  TMP117 温度传感器 (16-bit, 0.0625°C/LSB)
    0x68  DS3231 RTC (BCD编码时钟 + 闹钟)

【测试报告】

  HTML 报告（自动生成）:
    每次运行自动输出到 reports/report.html

  Allure 报告：
    $ allure generate reports/allure-results -o reports/allure-report --clean
    $ allure open reports/allure-report

【配置说明】

  可通过环境变量覆盖默认配置：
    TEST_ENV             测试环境 (dev/staging/prod)
    BASE_URL             API 地址
    UART_BAUDRATE        UART 波特率 (默认 9600)
    UART_TIMEOUT_MS      超时 (默认 500ms)
    UART_RETRY_MAX       重试次数 (默认 3)
    I2C_FREQ_HZ          I2C 频率 (默认 100000)
    I2C_EEPROM_ADDR      EEPROM 地址 (默认 0x50)
    I2C_TEMP_SENSOR_ADDR 温度传感器地址 (默认 0x48)
    I2C_RTC_ADDR         RTC 地址 (默认 0x68)
    NTC_SHORT_THRESHOLD  NTC 短路阈值 (Ω, 默认 50)
    NTC_OPEN_THRESHOLD   NTC 断路阈值 (Ω, 默认 500000)
    DOOR_OPEN_ALARM_SEC  开门超时告警 (秒, 默认 90)
    DEFROST_TRIGGER_TEMP 化霜触发温度 (°C, 默认 -10)

【用例统计】

  测试文件                      用例数
  -------------------------------------------------
  test_fridge_basic.py          31
  test_multi_door.py            20
  test_sensor.py                35
  test_uart_comm.py             27
  test_i2c_comm.py              34
  -------------------------------------------------
  合计                         147
================================================================================
