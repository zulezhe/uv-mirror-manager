"""Test models module."""

import pytest

from uvm.models.mirror import Mirror, MirrorTestResult


@pytest.mark.unit
class TestMirror:
    """Test Mirror model."""

    def test_valid_mirror_creation(self):
        """Test creating a valid mirror."""
        mirror = Mirror(
            name="test",
            url="https://example.com/simple",
            region="CN",
            description="Test mirror"
        )

        assert mirror.name == "test"
        assert str(mirror.url) == "https://example.com/simple"
        assert mirror.region == "CN"
        assert mirror.description == "Test mirror"
        assert mirror.builtin is True

    def test_invalid_url_not_simple(self):
        """Test mirror creation with invalid URL (not ending with /simple)."""
        with pytest.raises(ValueError, match="镜像源URL必须以/simple结尾"):
            Mirror(name="test", url="https://example.com/pypi")

    def test_invalid_empty_name(self):
        """Test mirror creation with empty name."""
        with pytest.raises(ValueError, match="镜像源名称不能为空"):
            Mirror(name="", url="https://example.com/simple")

    def test_invalid_name_characters(self):
        """Test mirror creation with invalid name characters."""
        with pytest.raises(ValueError, match="镜像源名称只能包含字母、数字、连字符和下划线"):
            Mirror(name="test@mirror", url="https://example.com/simple")

    def test_name_validation(self):
        """Test name validation edge cases."""
        # Valid names
        valid_names = ["test", "test-mirror", "test_mirror", "mirror123"]
        for name in valid_names:
            mirror = Mirror(name=name, url="https://example.com/simple")
            assert mirror.name == name

        # Names with whitespace should be stripped
        mirror = Mirror(name="  test  ", url="https://example.com/simple")
        assert mirror.name == "test"

    def test_mirror_equality(self):
        """Test mirror equality based on name."""
        mirror1 = Mirror(name="Test", url="https://example1.com/simple")
        mirror2 = Mirror(name="test", url="https://example2.com/simple")
        mirror3 = Mirror(name="other", url="https://example1.com/simple")

        assert mirror1 == mirror2  # Case insensitive
        assert mirror1 != mirror3
        assert mirror1 != "not a mirror"

    def test_mirror_hash(self):
        """Test mirror hashing for use in sets."""
        mirror1 = Mirror(name="Test", url="https://example.com/simple")
        mirror2 = Mirror(name="test", url="https://example2.com/simple")
        mirror3 = Mirror(name="other", url="https://example.com/simple")

        assert hash(mirror1) == hash(mirror2)  # Case insensitive
        assert hash(mirror1) != hash(mirror3)

        # Test in set
        mirror_set = {mirror1, mirror2, mirror3}
        assert len(mirror_set) == 2  # mirror1 and mirror2 are considered the same

    def test_mirror_properties(self):
        """Test mirror helper properties."""
        official_mirror = Mirror(name="official", url="https://pypi.org/simple")
        custom_mirror = Mirror(name="custom", url="https://custom.com/simple")

        assert official_mirror.is_official is True
        assert custom_mirror.is_official is False

        assert official_mirror.netloc == "pypi.org"
        assert custom_mirror.netloc == "custom.com"

    def test_mirror_string_representation(self):
        """Test mirror string representations."""
        mirror = Mirror(
            name="test",
            url="https://example.com/simple",
            region="CN",
            description="Test mirror"
        )

        str_repr = str(mirror)
        assert "test" in str_repr
        assert "https://example.com/simple" in str_repr

        repr_str = repr(mirror)
        assert "test" in repr_str
        assert "CN" in repr_str

    def test_to_dict(self):
        """Test mirror to_dict conversion."""
        mirror = Mirror(
            name="test",
            url="https://example.com/simple",
            region="US",
            builtin=False,
            description="Test mirror"
        )

        expected = {
            "name": "test",
            "url": "https://example.com/simple",
            "region": "US",
            "builtin": False,
            "description": "Test mirror",
        }

        assert mirror.to_dict() == expected


@pytest.mark.unit
class TestMirrorTestResult:
    """Test MirrorTestResult model."""

    def test_successful_result(self):
        """Test successful test result."""
        mirror = Mirror(name="test", url="https://example.com/simple")
        result = MirrorTestResult(
            mirror=mirror,
            response_time=0.5,
            success=True,
            test_time=1234567890.0
        )

        assert result.mirror == mirror
        assert result.response_time == 0.5
        assert result.success is True
        assert result.error_message == ""
        assert result.test_time == 1234567890.0

    def test_failed_result(self):
        """Test failed test result."""
        mirror = Mirror(name="test", url="https://example.com/simple")
        result = MirrorTestResult(
            mirror=mirror,
            response_time=0.0,
            success=False,
            error_message="Connection timeout",
            test_time=1234567890.0
        )

        assert result.success is False
        assert result.error_message == "Connection timeout"

    def test_result_string_representation(self):
        """Test result string representation."""
        mirror = Mirror(name="test", url="https://example.com/simple")

        success_result = MirrorTestResult(
            mirror=mirror,
            response_time=0.123,
            success=True,
            test_time=1234567890.0
        )
        assert "test: 0.123s" in str(success_result)

        failed_result = MirrorTestResult(
            mirror=mirror,
            response_time=0.0,
            success=False,
            error_message="Timeout error",
            test_time=1234567890.0
        )
        assert "test: FAILED" in str(failed_result)
        assert "Timeout error" in str(failed_result)