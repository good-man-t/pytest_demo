"""电视功能测试"""

import pytest
import yaml
from pathlib import Path


def load_tv_data():
    data_path = Path(__file__).parent.parent.parent / "testdata" / "appliance_data.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["tv"]


class TestTVPower:
    """电视开关机测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.tv
    def test_power_on(self, tv):
        assert tv.power is True

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.tv
    def test_power_off(self, tv):
        tv.power_off()
        assert tv.power is False


class TestTVVolume:
    """电视音量控制测试"""

    @pytest.mark.p0
    @pytest.mark.tv
    @pytest.mark.parametrize("volume,desc", load_tv_data()["volumes"])
    def test_set_volume(self, tv, volume, desc):
        """参数化：设置音量"""
        result = tv.set_volume(volume)
        assert result["status"] == "success"
        assert tv.volume == volume

    @pytest.mark.p1
    @pytest.mark.tv
    def test_set_volume_out_of_range_raises(self, tv):
        """音量超出范围抛出异常"""
        with pytest.raises(ValueError, match="音量超出范围"):
            tv.set_volume(-1)
        with pytest.raises(ValueError, match="音量超出范围"):
            tv.set_volume(101)

    @pytest.mark.p1
    @pytest.mark.tv
    def test_default_volume(self, tv):
        """验证默认音量"""
        assert tv.volume == 20


class TestTVChannel:
    """电视频道控制测试"""

    @pytest.mark.p1
    @pytest.mark.tv
    @pytest.mark.parametrize("channel", [1, 100, 500, 999])
    def test_set_channel(self, tv, channel):
        """设置频道"""
        result = tv.set_channel(channel)
        assert result["status"] == "success"
        assert tv.channel == channel

    @pytest.mark.p1
    @pytest.mark.tv
    def test_set_channel_out_of_range_raises(self, tv):
        """频道超出范围抛出异常"""
        with pytest.raises(ValueError, match="频道超出范围"):
            tv.set_channel(0)
        with pytest.raises(ValueError, match="频道超出范围"):
            tv.set_channel(1000)


class TestTVSource:
    """电视输入源测试"""

    @pytest.mark.p1
    @pytest.mark.tv
    @pytest.mark.parametrize("source,desc", load_tv_data()["sources"])
    def test_set_source(self, tv, source, desc):
        """参数化：切换输入源"""
        result = tv.set_source(source)
        assert result["status"] == "success"
        assert tv.get_status()["source"] == source

    @pytest.mark.p2
    @pytest.mark.tv
    def test_set_invalid_source_raises(self, tv):
        """无效输入源抛出异常"""
        with pytest.raises(ValueError, match="无效输入源"):
            tv.set_source("vga")


class TestTVBrightness:
    """电视亮度控制测试"""

    @pytest.mark.p1
    @pytest.mark.tv
    @pytest.mark.parametrize("brightness,desc", load_tv_data()["brightness_levels"])
    def test_set_brightness(self, tv, brightness, desc):
        """参数化：设置亮度"""
        result = tv.set_brightness(brightness)
        assert result["status"] == "success"

    @pytest.mark.p2
    @pytest.mark.tv
    def test_set_brightness_out_of_range_raises(self, tv):
        """亮度超范围抛出异常"""
        with pytest.raises(ValueError, match="亮度超出范围"):
            tv.set_brightness(-1)
        with pytest.raises(ValueError, match="亮度超出范围"):
            tv.set_brightness(101)


class TestTVStatus:
    """电视状态查询测试"""

    @pytest.mark.smoke
    @pytest.mark.p0
    @pytest.mark.tv
    def test_get_status(self, tv):
        """验证状态字段完整性"""
        tv.set_volume(30)
        tv.set_channel(5)
        tv.set_source("usb")
        tv.set_brightness(80)
        status = tv.get_status()
        assert status["device_type"] == "tv"
        assert status["volume"] == 30
        assert status["channel"] == 5
        assert status["source"] == "usb"
        assert status["brightness"] == 80
