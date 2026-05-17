'''
Author: oliver
Date: 2025-10-16 23:10:04
LastEditors: oliver
LastEditTime: 2025-11-26 21:37:31
Description: 
'''
"""Integration tests for CLI list command."""

import pytest
from typer.testing import CliRunner
from pathlib import Path

from uvm.cli import app


@pytest.mark.integration
class TestCLIList:
    """Test CLI list command integration."""

    def test_list_basic(self, tmp_path):
        """Test basic list command."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "可用镜像源" in result.stdout
            assert "official" in result.stdout
            assert "tsinghua" in result.stdout

    def test_list_with_custom_mirrors(self, mock_uv_config):
        """Test list command with custom mirrors."""
        runner = CliRunner()

        # Add custom mirror first
        from uvm.core.mirror import MirrorManager
        manager = MirrorManager()
        manager.add_custom_mirror(
            name="test-custom",
            url="https://test.example.com/simple",
            description="Test custom mirror"
        )

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "test-custom" in result.stdout
        assert "自定义" in result.stdout

    def test_list_with_current_mirror(self, mock_uv_config):
        """Test list command showing current mirror."""
        runner = CliRunner()

        from uvm.core.mirror import MirrorManager
        manager = MirrorManager()
        manager.use_mirror("tsinghua")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "tsinghua" in result.stdout
        # Current mirror should be marked
        assert "->" in result.stdout

    def test_list_statistics(self, tmp_path):
        """Test list command shows statistics."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "总计" in result.stdout
            assert "内置" in result.stdout
            assert "自定义" in result.stdout