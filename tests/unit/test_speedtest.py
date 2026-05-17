"""Test speedtest module."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from uvm.core.speedtest import SpeedTester
from uvm.models.mirror import Mirror, MirrorTestResult


@pytest.mark.unit
class TestSpeedTester:
    """Test SpeedTester class."""

    def test_speedtester_init(self):
        """Test SpeedTester initialization."""
        tester = SpeedTester(timeout=3.0)
        assert tester.timeout == 3.0
        assert tester._cache_path.name == ".uvm-cache.json"

    def test_speedtester_init_default(self):
        """Test SpeedTester initialization with default timeout."""
        tester = SpeedTester()
        from uvm.constants import DEFAULT_TIMEOUT
        assert tester.timeout == DEFAULT_TIMEOUT

    @pytest.mark.asyncio
    async def test_download_speed_test_success(self, mock_mirror_server):
        """Test successful speed test."""
        tester = SpeedTester(timeout=5.0)
        mirror = Mirror(name="test", url=str(mock_mirror_server.make_url("/simple/")))

        import aiohttp
        async with aiohttp.ClientSession() as session:
            result = await tester._download_speed_test(session, mirror)

        assert result.success is True
        assert result.response_time > 0
        assert result.mirror == mirror
        assert result.error_message == ""

    @pytest.mark.asyncio
    async def test_download_speed_test_http_error(self):
        """Test speed test with HTTP error."""
        tester = SpeedTester(timeout=5.0)
        mirror = Mirror(name="test", url="https://httpbin.org/status/404")

        import aiohttp
        async with aiohttp.ClientSession() as session:
            result = await tester._download_speed_test(session, mirror)

        assert result.success is False
        assert result.response_time == 0.0
        assert "404" in result.error_message

    @pytest.mark.asyncio
    async def test_download_speed_test_timeout(self):
        """Test speed test with timeout."""
        tester = SpeedTester(timeout=0.001)  # Very short timeout
        mirror = Mirror(name="test", url="https://httpbin.org/delay/1")

        import aiohttp
        async with aiohttp.ClientSession() as session:
            result = await tester._download_speed_test(session, mirror)

        assert result.success is False
        assert result.response_time == 0.0
        assert "Timeout" in result.error_message

    @pytest.mark.asyncio
    async def test_test_mirror_success(self, mock_mirror_server):
        """Test testing a single mirror."""
        tester = SpeedTester()
        mirror = Mirror(name="test", url=str(mock_mirror_server.make_url("/simple/")))

        result = await tester.test_mirror(mirror)

        assert isinstance(result, MirrorTestResult)
        assert result.mirror == mirror

    @pytest.mark.asyncio
    async def test_test_mirrors_concurrent(self, mock_mirror_server):
        """Test testing multiple mirrors concurrently."""
        tester = SpeedTester(max_concurrent=2)
        mirrors = [
            Mirror(name="test1", url=str(mock_mirror_server.make_url("/simple/"))),
            Mirror(name="test2", url=str(mock_mirror_server.make_url("/simple/"))),
            Mirror(name="test3", url="https://nonexistent.invalid/simple"),
        ]

        results = await tester.test_mirrors(mirrors)

        assert len(results) == 3
        assert all(isinstance(r, MirrorTestResult) for r in results)

        # Results should be sorted by response time (successful first)
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Successful results should come first
        if successful_results and failed_results:
            assert all(r.success for r in results[:len(successful_results)])
            assert all(not r.success for r in results[len(successful_results):])

            # Successful results should be sorted by time
            for i in range(1, len(successful_results)):
                assert successful_results[i-1].response_time <= successful_results[i].response_time

    def test_load_cache_empty(self, tmp_path):
        """Test loading cache when file doesn't exist."""
        cache_path = tmp_path / ".uvm-cache.json"
        tester = SpeedTester()
        tester._cache_path = cache_path

        cache = tester.load_cache()
        assert cache == {}

    def test_load_cache_invalid_json(self, tmp_path):
        """Test loading cache with invalid JSON."""
        cache_path = tmp_path / ".uvm-cache.json"
        cache_path.write_text("invalid json content")

        tester = SpeedTester()
        tester._cache_path = cache_path

        cache = tester.load_cache()
        assert cache == {}

    def test_load_cache_expired(self, tmp_path, freezer):
        """Test loading cache with expired entries."""
        freezer.move_to("2024-01-01 00:00:00")

        # Create cache with old timestamp
        cache_data = {
            "test-mirror": (0.5, 1640995200.0),  # 2022-01-01 timestamp
        }
        cache_path = tmp_path / ".uvm-cache.json"
        cache_path.write_text(json.dumps(cache_data))

        tester = SpeedTester()
        tester._cache_path = cache_path

        # Move time forward to make cache entry expired
        freezer.move_to("2024-01-02 00:00:00")
        cache = tester.load_cache()
        assert cache == {}  # Should be empty due to expiration

    def test_load_cache_valid(self, tmp_path, freezer):
        """Test loading cache with valid entries."""
        freezer.move_to("2024-01-01 00:00:00")

        current_time = 1640995200.0  # 2022-01-01 timestamp
        cache_data = {
            "test-mirror": (0.5, current_time),
        }
        cache_path = tmp_path / ".uvm-cache.json"
        cache_path.write_text(json.dumps(cache_data))

        tester = SpeedTester()
        tester._cache_path = cache_path

        cache = tester.load_cache()
        assert cache == {"test-mirror": (0.5, current_time)}

    def test_save_cache(self, tmp_path):
        """Test saving cache."""
        cache_path = tmp_path / ".uvm-cache.json"
        tester = SpeedTester()
        tester._cache_path = cache_path

        mirror = Mirror(name="test", url="https://test.com/simple")
        results = [
            MirrorTestResult(
                mirror=mirror,
                response_time=0.5,
                success=True,
                test_time=1640995200.0
            ),
            MirrorTestResult(
                mirror=Mirror(name="test2", url="https://test2.com/simple"),
                response_time=0.0,
                success=False,
                error_message="Failed",
                test_time=1640995200.0
            ),
        ]

        tester.save_cache(results)

        assert cache_path.exists()
        saved_data = json.loads(cache_path.read_text())
        assert "test" in saved_data
        # Only successful results should be cached
        assert len(saved_data) == 1

    def test_get_cached_speed(self, tmp_path):
        """Test getting cached speed for a mirror."""
        cache_path = tmp_path / ".uvm-cache.json"
        tester = SpeedTester()
        tester._cache_path = cache_path

        # Test with empty cache
        speed = tester.get_cached_speed("nonexistent")
        assert speed is None

        # Test with cache data (use current timestamp)
        import time
        current_time = time.time()
        cache_data = {"test-mirror": (0.5, current_time)}
        cache_path.write_text(json.dumps(cache_data))
        
        speed = tester.get_cached_speed("test-mirror")
        assert speed == 0.5

    def test_get_cached_speed_expired(self, tmp_path, freezer):
        """Test getting cached speed for expired entry."""
        freezer.move_to("2024-01-01 00:00:00")

        # Create old cache entry
        cache_data = {"test-mirror": (0.5, 1640995200.0)}  # 2022 timestamp
        cache_path = tmp_path / ".uvm-cache.json"
        cache_path.write_text(json.dumps(cache_data))

        tester = SpeedTester()
        tester._cache_path = cache_path

        # Move time forward to make entry expired
        freezer.move_to("2024-01-02 00:00:00")

        speed = tester.get_cached_speed("test-mirror")
        assert speed is None

    @pytest.mark.asyncio
    async def test_test_and_cache_with_cache(self, tmp_path):
        """Test testing mirrors with cache usage."""
        cache_path = tmp_path / ".uvm-cache.json"
        tester = SpeedTester()
        tester._cache_path = cache_path

        # Pre-populate cache
        mirror1 = Mirror(name="test1", url="https://test1.com/simple")
        mirror2 = Mirror(name="test2", url="https://test2.com/simple")
        mirror3 = Mirror(name="test3", url="https://test3.com/simple")

        cache_data = {"test1": (0.3, 1640995200.0)}  # Cached result for test1
        cache_path.write_text(json.dumps(cache_data))

        # Mock the test_mirrors method to avoid actual network calls
        async def mock_test_mirrors(mirrors, max_concurrent=5):
            # Only return results for uncached mirrors
            uncached = [m for m in mirrors if m.name != "test1"]
            return [
                MirrorTestResult(
                    mirror=m,
                    response_time=0.5,
                    success=True,
                    test_time=1640995200.0
                ) for m in uncached
            ]

        with patch.object(tester, 'test_mirrors', side_effect=mock_test_mirrors):
            results = await tester.test_and_cache([mirror1, mirror2, mirror3], use_cache=True)

        assert len(results) == 3
        # Results should be sorted by response time
        assert results[0].mirror.name == "test1"  # Cached fastest
        assert results[0].response_time == 0.3
        assert results[1].response_time == 0.5
        assert results[2].response_time == 0.5

    @pytest.mark.asyncio
    async def test_test_and_cache_no_cache(self):
        """Test testing mirrors without cache."""
        tester = SpeedTester()

        mirror = Mirror(name="test", url="https://httpbin.org/status/200")

        # Mock test_mirrors to avoid actual network calls
        mock_result = MirrorTestResult(
            mirror=mirror,
            response_time=0.5,
            success=True,
            test_time=1640995200.0
        )

        with patch.object(tester, 'test_mirrors', return_value=[mock_result]):
            results = await tester.test_and_cache([mirror], use_cache=False)

        assert len(results) == 1
        assert results[0] == mock_result

    def test_format_results_table(self):
        """Test formatting results as table."""
        tester = SpeedTester()

        mirror1 = Mirror(name="test1", url="https://test1.com/simple")
        mirror2 = Mirror(name="test2", url="https://test2.com/simple")

        results = [
            MirrorTestResult(
                mirror=mirror1,
                response_time=0.123,
                success=True,
                test_time=1640995200.0
            ),
            MirrorTestResult(
                mirror=mirror2,
                response_time=0.0,
                success=False,
                error_message="Connection failed",
                test_time=1640995200.0
            ),
        ]

        table_str = tester.format_results_table(results)

        assert "test1" in table_str
        assert "test2" in table_str
        assert "0.123s" in table_str
        assert "Connection failed" in table_str
        assert "[OK]" in table_str
        assert "[FAIL]" in table_str

    def test_get_recommendations(self):
        """Test getting top mirror recommendations."""
        tester = SpeedTester()

        mirrors = [
            Mirror(name=f"test{i}", url=f"https://test{i}.com/simple")
            for i in range(5)
        ]

        # Create results with varying response times
        results = [
            MirrorTestResult(
                mirror=mirrors[i],
                response_time=0.1 * (i + 1),
                success=True,
                test_time=1640995200.0
            )
            for i in range(3)
        ]

        # Add some failed results
        results.append(
            MirrorTestResult(
                mirror=mirrors[3],
                response_time=0.0,
                success=False,
                error_message="Failed",
                test_time=1640995200.0
            )
        )
        results.append(
            MirrorTestResult(
                mirror=mirrors[4],
                response_time=0.0,
                success=False,
                error_message="Failed",
                test_time=1640995200.0
            )
        )

        # Get top 3 recommendations
        recommendations = tester.get_recommendations(results, top_n=3)

        assert len(recommendations) == 3
        # Should only include successful results
        assert all(r.success for r in recommendations)
        # Should be sorted by response time
        for i in range(1, len(recommendations)):
            assert recommendations[i-1].response_time <= recommendations[i].response_time

    def test_speedtester_repr(self):
        """Test SpeedTester string representation."""
        tester = SpeedTester(timeout=3.0)
        repr_str = repr(tester)

        assert "SpeedTester" in repr_str
        assert "timeout=3.0" in repr_str
        assert "cache_path" in repr_str