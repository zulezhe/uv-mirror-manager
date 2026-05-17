'''
Author: oliver
Date: 2025-10-16 23:10:04
LastEditors: oliver
LastEditTime: 2025-11-26 21:36:26
Description: 
'''
"""Integration tests for CLI current command."""

import pytest
from typer.testing import CliRunner

from uvm.cli import app


@pytest.mark.integration
class TestCLICurrent:
    """Test CLI current command integration."""

    def test_current_no_mirror(self, mock_uv_config):
        """Test current command with no mirror set."""
        runner = CliRunner()

        result = runner.invoke(app, ["current"])

        assert result.exit_code == 0
        assert "[INFO] 当前使用默认官方源" in result.stdout

    def test_current_builtin_mirror(self, mock_uv_config):
        """Test current command with built-in mirror."""
        runner = CliRunner()

        # Set a built-in mirror
        from uvm.core.mirror import MirrorManager
        manager = MirrorManager()
        manager.use_mirror("tsinghua")

        result = runner.invoke(app, ["current"])

        assert result.exit_code == 0
        assert "[INFO] 当前镜像源: tsinghua" in result.stdout
        assert "https://pypi.tuna.tsinghua.edu.cn/simple" in result.stdout
        assert "清华大学镜像源" in result.stdout

    def test_current_custom_url(self, mock_uv_config):
        """Test current command with custom URL."""
        runner = CliRunner()

        # Set a custom URL directly
        from uvm.core.config import UVConfig
        config = UVConfig()
        config.set_index_url("https://custom.example.com/simple")

        result = runner.invoke(app, ["current"])

        assert result.exit_code == 0
        assert "[INFO] 当前镜像源: 自定义URL" in result.stdout
        assert "https://custom.example.com/simple" in result.stdout