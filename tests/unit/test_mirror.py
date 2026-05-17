"""Test mirror management module."""

import pytest

from uvm.core.mirror import MirrorManager
from uvm.models.mirror import Mirror


@pytest.mark.unit
class TestMirrorManager:
    """Test MirrorManager class."""

    def test_builtin_mirrors(self):
        """Test built-in mirrors are loaded correctly."""
        manager = MirrorManager()
        builtin_mirrors = manager.builtin_mirrors

        assert len(builtin_mirrors) > 0
        assert all(mirror.builtin for mirror in builtin_mirrors)

        # Check for common mirrors
        mirror_names = [mirror.name for mirror in builtin_mirrors]
        assert "official" in mirror_names
        assert "tsinghua" in mirror_names

    def test_get_mirror_by_name(self, tmp_path):
        """Test getting mirror by name."""
        from pathlib import Path
        # Mock config to avoid path issues
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
            manager = MirrorManager()

            # Test case-insensitive lookup
            official = manager.get_mirror_by_name("official")
            official_upper = manager.get_mirror_by_name("OFFICIAL")
            assert official == official_upper
            assert official.name == "official"

            # Test non-existent mirror
            none_result = manager.get_mirror_by_name("non-existent")
            assert none_result is None
        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_get_current_mirror(self, mock_uv_config):
        """Test getting current mirror."""
        manager = MirrorManager()

        # Clear any existing configuration first
        mock_uv_config.reset_index_url()

        # No current URL set
        current = manager.get_current_mirror()
        assert current is None

        # Set current URL to a known mirror
        mock_uv_config.set_index_url("https://pypi.tuna.tsinghua.edu.cn/simple")
        current = manager.get_current_mirror()
        assert current is not None
        assert current.name == "tsinghua"

        # Set to custom URL
        mock_uv_config.set_index_url("https://custom.example.com/simple")
        current = manager.get_current_mirror()
        assert current is None  # Not in built-in mirrors

    def test_use_mirror(self, mock_uv_config):
        """Test using a mirror."""
        manager = MirrorManager()

        # Use valid mirror
        success = manager.use_mirror("tsinghua")
        assert success is True
        assert mock_uv_config.get_current_index_url() == "https://pypi.tuna.tsinghua.edu.cn/simple"

        # Use invalid mirror
        success = manager.use_mirror("non-existent")
        assert success is False

    def test_reset_mirror(self, mock_uv_config):
        """Test resetting mirror."""
        manager = MirrorManager()

        # Set a mirror first
        mock_uv_config.set_index_url("https://pypi.tuna.tsinghua.edu.cn/simple")
        assert mock_uv_config.get_current_index_url() is not None

        # Reset
        manager.reset_mirror()
        assert mock_uv_config.get_current_index_url() is None

    def test_add_custom_mirror(self, mock_uv_config):
        """Test adding custom mirror."""
        manager = MirrorManager()

        # Add valid custom mirror
        success = manager.add_custom_mirror(
            name="test-mirror",
            url="https://test.example.com/simple",
            description="Test custom mirror"
        )
        assert success is True

        # Verify it was added
        custom_mirrors = manager.custom_mirrors
        custom_names = [m.name for m in custom_mirrors]
        assert "test-mirror" in custom_names

        # Try to add duplicate
        success = manager.add_custom_mirror(
            name="test-mirror",
            url="https://another.example.com/simple"
        )
        assert success is False

        # Add invalid URL
        success = manager.add_custom_mirror(
            name="invalid-mirror",
            url="https://example.com/invalid"  # Missing /simple
        )
        assert success is False

    def test_remove_custom_mirror(self, mock_uv_config):
        """Test removing custom mirror."""
        manager = MirrorManager()

        # Add a custom mirror first
        manager.add_custom_mirror(
            name="test-mirror",
            url="https://test.example.com/simple"
        )

        # Remove it
        success = manager.remove_custom_mirror("test-mirror")
        assert success is True

        # Verify it's gone
        custom_mirrors = manager.custom_mirrors
        custom_names = [m.name for m in custom_mirrors]
        assert "test-mirror" not in custom_names

        # Try to remove non-existent mirror
        success = manager.remove_custom_mirror("non-existent")
        assert success is False

        # Try to remove built-in mirror
        success = manager.remove_custom_mirror("official")
        assert success is False

    def test_list_mirrors(self, mock_uv_config):
        """Test listing all mirrors."""
        manager = MirrorManager()

        # Add a custom mirror
        manager.add_custom_mirror(
            name="test-custom",
            url="https://test.example.com/simple"
        )

        # List mirrors
        mirrors_data = manager.list_mirrors()
        assert len(mirrors_data) > 0

        # Check structure
        for mirror_data in mirrors_data:
            assert "name" in mirror_data
            assert "url" in mirror_data
            assert "region" in mirror_data
            assert "builtin" in mirror_data
            assert "description" in mirror_data
            assert "current" in mirror_data

        # Set current mirror and verify it's marked
        manager.use_mirror("tsinghua")
        mirrors_data = manager.list_mirrors()

        tsinghua_data = next(
            (m for m in mirrors_data if m["name"] == "tsinghua"),
            None
        )
        assert tsinghua_data is not None
        assert tsinghua_data["current"] is True

    def test_search_mirrors(self, tmp_path):
        """Test searching mirrors."""
        from pathlib import Path
        # Mock config to avoid path issues
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
            manager = MirrorManager()

            # Search by name
            results = manager.search_mirrors("tsinghua")
            assert len(results) > 0
            assert all("tsinghua" in mirror.name.lower() for mirror in results)

            # Search by description
            results = manager.search_mirrors("清华")
            assert len(results) > 0

            # Search by region
            results = manager.search_mirrors("CN")
            assert len(results) > 0
            assert all(mirror.region == "CN" for mirror in results)

            # Search with no results
            results = manager.search_mirrors("nonexistent")
            assert len(results) == 0
        finally:
            platformdirs.PlatformDirs.user_config_path = original_user_config_path

    def test_validate_mirror_url(self):
        """Test mirror URL validation."""
        manager = MirrorManager()

        # Valid URLs
        valid_urls = [
            "https://pypi.org/simple",
            "http://mirror.example.com/simple",
            "https://custom-mirror.org/simple/",
        ]
        for url in valid_urls:
            assert manager.validate_mirror_url(url.rstrip('/')) is True

        # Invalid URLs
        invalid_urls = [
            "https://example.com/invalid",  # Missing /simple
            "ftp://example.com/simple",    # Unsupported protocol
            "not-a-url",                   # Not a URL
            "https://example.com",         # Missing path
        ]
        for url in invalid_urls:
            assert manager.validate_mirror_url(url) is False

    def test_get_mirror_statistics(self, mock_uv_config):
        """Test mirror statistics."""
        manager = MirrorManager()

        # Add some custom mirrors
        manager.add_custom_mirror("custom1", "https://custom1.com/simple")
        manager.add_custom_mirror("custom2", "https://custom2.com/simple", region="US")

        stats = manager.get_mirror_statistics()

        assert "total_mirrors" in stats
        assert "builtin_mirrors" in stats
        assert "custom_mirrors" in stats
        assert "regions" in stats
        assert "current_mirror" in stats

        assert stats["total_mirrors"] > 0
        assert stats["builtin_mirrors"] > 0
        assert stats["custom_mirrors"] >= 2
        assert "CN" in stats["regions"]
        assert "US" in stats["regions"]

    def test_export_mirrors(self):
        """Test exporting mirrors configuration."""
        manager = MirrorManager()

        # Export to TOML
        toml_output = manager.export_mirrors("toml")
        assert "official" in toml_output
        assert "builtin_mirrors" in toml_output

        # Test invalid format
        with pytest.raises(ValueError, match="Unsupported export format"):
            manager.export_mirrors("invalid")

    def test_mirror_manager_repr(self):
        """Test MirrorManager string representation."""
        manager = MirrorManager()
        repr_str = repr(manager)

        assert "MirrorManager" in repr_str
        assert "builtin=" in repr_str
        assert "custom=" in repr_str