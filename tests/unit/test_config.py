"""Test config module."""

import pytest
import tomlkit
from pathlib import Path

from uvm.core.config import UVConfig


@pytest.mark.unit
class TestUVConfig:
    """Test UVConfig class."""

    def test_config_paths(self, tmp_path):
        """Test config path resolution."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        def mock_user_config_path(self) -> Path:
            return tmp_path / "uv"

        platformdirs.PlatformDirs.user_config_path = mock_user_config_path

        try:
            config = UVConfig()
            expected_uv_path = tmp_path / "uv" / "uv.toml"
            expected_backup_path = tmp_path / "uv" / "uv.toml.bak"

            assert config.uv_config_path == expected_uv_path
            assert config.uv_config_backup_path == expected_backup_path
        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_ensure_uv_config_dir(self, tmp_path):
        """Test ensuring UV config directory exists."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        def mock_user_config_path(self) -> Path:
            return tmp_path / "uv"

        platformdirs.PlatformDirs.user_config_path = mock_user_config_path

        try:
            config = UVConfig()
            config_dir = config.ensure_uv_config_dir()

            assert config_dir.exists()
            assert config_dir.is_dir()
            assert config_dir == tmp_path / "uv"
        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_read_write_uv_config(self, tmp_path):
        """Test reading and writing UV config."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        def mock_user_config_path(self) -> Path:
            return tmp_path / "uv"

        platformdirs.PlatformDirs.user_config_path = mock_user_config_path

        try:
            config = UVConfig()

            # Test reading non-existent config
            assert config.read_uv_config() == {}

            # Test writing config
            test_config = {
                "uv": {
                    "index_url": "https://example.com/simple",
                    "timeout": 30
                }
            }
            config.write_uv_config(test_config)

            # Verify file was created
            assert config.uv_config_path.exists()

            # Test reading config back
            read_config = config.read_uv_config()
            assert read_config["uv"]["index_url"] == "https://example.com/simple"
            assert read_config["uv"]["timeout"] == 30

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_backup_restore(self, tmp_path):
        """Test backup and restore functionality."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        def mock_user_config_path(self) -> Path:
            return tmp_path / "uv"

        platformdirs.PlatformDirs.user_config_path = mock_user_config_path

        try:
            config = UVConfig()

            # Create initial config
            initial_config = {"uv": {"index_url": "https://initial.com/simple"}}
            config.write_uv_config(initial_config)

            # Create backup
            backup_path = config.create_backup()
            assert backup_path.exists()
            assert backup_path == config.uv_config_backup_path

            # Modify original config
            modified_config = {"uv": {"index_url": "https://modified.com/simple"}}
            config.write_uv_config(modified_config, create_backup=False)

            # Restore from backup
            config.restore_backup()
            restored_config = config.read_uv_config()

            assert restored_config["uv"]["index_url"] == "https://initial.com/simple"

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_index_url_operations(self, tmp_path):
        """Test index URL get/set/reset operations."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        import platformdirs
        original_platform_dirs = platformdirs.PlatformDirs
        
        class MockPlatformDirs:
            def __init__(self, *args, **kwargs):
                pass
            @property
            def user_config_path(self) -> Path:
                return tmp_path / "uv"
        
        platformdirs.PlatformDirs = MockPlatformDirs

        try:
            config = UVConfig()

            # Test getting URL from non-existent config
            assert config.get_current_index_url() is None

            # Test setting URL
            config.set_index_url("https://test.com/simple")
            assert config.get_current_index_url() == "https://test.com/simple"

            # Test resetting URL
            config.reset_index_url()
            assert config.get_current_index_url() is None

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_uvm_config_operations(self, tmp_path):
        """Test UVM custom mirror configuration."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path
        original_uvm_user_config_path = platformdirs.PlatformDirs.user_config_path

        class MockPlatformDirs:
            def __init__(self, *args, **kwargs):
                pass
            @property
            def user_config_path(self) -> Path:
                return tmp_path / "uv"
        
        platformdirs.PlatformDirs = MockPlatformDirs

        # Monkey patch for UVM dirs
        import uvm.core.config
        original_uvm_dirs = uvm.core.config.PlatformDirs

        class MockUVMDirs:
            def __init__(self, *args, **kwargs):
                pass
            def user_config_path(self) -> Path:
                return tmp_path / "uvm"

        uvm.core.config.PlatformDirs = MockUVMDirs

        try:
            config = UVConfig()

            # Test reading default UVM config
            default_config = config.read_uvm_config()
            assert default_config["meta"]["version"] == 1
            assert "mirrors" in default_config
            assert "custom" in default_config["mirrors"]

            # Test adding custom mirror
            config.add_custom_mirror(
                name="test-mirror",
                url="https://test.com/simple",
                description="Test mirror"
            )

            custom_mirrors = config.get_custom_mirrors()
            assert "test-mirror" in custom_mirrors
            assert custom_mirrors["test-mirror"]["url"] == "https://test.com/simple"
            assert custom_mirrors["test-mirror"]["description"] == "Test mirror"

            # Test removing custom mirror
            success = config.remove_custom_mirror("test-mirror")
            assert success is True

            custom_mirrors = config.get_custom_mirrors()
            assert "test-mirror" not in custom_mirrors

            # Test removing non-existent mirror
            success = config.remove_custom_mirror("non-existent")
            assert success is False

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path
            uvm.core.config.PlatformDirs = original_uvm_dirs

    def test_backup_file_not_exists(self, tmp_path):
        """Test backup creation when file doesn't exist."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        class MockPlatformDirs:
            def __init__(self, *args, **kwargs):
                pass
            @property
            def user_config_path(self) -> Path:
                return tmp_path / "uv"
        
        platformdirs.PlatformDirs = MockPlatformDirs

        try:
            config = UVConfig()

            with pytest.raises(FileNotFoundError, match="UV config file does not exist"):
                config.create_backup()

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_restore_backup_not_exists(self, tmp_path):
        """Test restore when backup doesn't exist."""
        import platformdirs
        original_user_config_path = platformdirs.PlatformDirs.user_config_path

        class MockPlatformDirs:
            def __init__(self, *args, **kwargs):
                pass
            @property
            def user_config_path(self) -> Path:
                return tmp_path / "uv"
        
        platformdirs.PlatformDirs = MockPlatformDirs

        try:
            config = UVConfig()

            with pytest.raises(FileNotFoundError, match="UV config backup file does not exist"):
                config.restore_backup()

        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path