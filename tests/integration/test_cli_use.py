"""Integration tests for CLI use command."""

import pytest
from typer.testing import CliRunner

from uvm.cli import app


@pytest.mark.integration
class TestCLIUse:
    """Test CLI use command integration."""

    def test_use_valid_mirror(self, mock_uv_config):
        """Test using a valid mirror."""
        runner = CliRunner()

        result = runner.invoke(app, ["use", "tsinghua"])

        assert result.exit_code == 0
        assert "已切换到镜像源: tsinghua" in result.stdout
        assert "https://pypi.tuna.tsinghua.edu.cn/simple" in result.stdout

        # Verify the change was applied
        from uvm.core.config import UVConfig
        config = UVConfig()
        current_url = config.get_current_index_url()
        assert current_url == "https://pypi.tuna.tsinghua.edu.cn/simple"

    def test_use_invalid_mirror(self, tmp_path):
        """Test using an invalid mirror."""
        runner = CliRunner()

        result = runner.invoke(app, ["use", "nonexistent"])

        assert result.exit_code != 0
        assert "未找到镜像源: nonexistent" in result.stdout
        assert "使用 'uvm list' 查看可用镜像源" in result.stdout

    def test_use_case_insensitive(self, mock_uv_config):
        """Test using mirror with different case."""
        runner = CliRunner()

        # Test uppercase
        result = runner.invoke(app, ["use", "TSINGHUA"])
        assert result.exit_code == 0

        # Test mixed case
        result = runner.invoke(app, ["use", "TsingHua"])
        assert result.exit_code == 0

    def test_use_custom_mirror(self, mock_uv_config):
        """Test using a custom mirror."""
        runner = CliRunner()

        # First add a custom mirror
        from uvm.core.mirror import MirrorManager
        manager = MirrorManager()
        manager.add_custom_mirror(
            name="test-custom",
            url="https://test.example.com/simple"
        )

        # Then use it
        result = runner.invoke(app, ["use", "test-custom"])

        assert result.exit_code == 0
        assert "已切换到镜像源: test-custom" in result.stdout