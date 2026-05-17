"""Async speed testing for mirror sources."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from platformdirs import PlatformDirs

from uvm.constants import (
    CACHE_FILE,
    DEFAULT_TIMEOUT,
    SPEEDTEST_PACKAGE,
    SPEEDTEST_SIZE,
)
from uvm.models.mirror import Mirror, MirrorTestResult


class SpeedTester:
    """Performs speed testing on mirror sources."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        """Initialize speed tester.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._dirs = PlatformDirs("uv-mirror", appauthor="uvm")
        self._cache_path = self._dirs.user_cache_path / CACHE_FILE

    async def _download_speed_test(
        self,
        session: aiohttp.ClientSession,
        mirror: Mirror,
    ) -> MirrorTestResult:
        """Test download speed from a mirror.

        Args:
            session: aiohttp client session.
            mirror: Mirror to test.

        Returns:
            MirrorTestResult with timing information.
        """
        test_url = str(mirror.url).rstrip('/') + '/'
        start_time = time.time()

        try:
            async with session.get(
                test_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": "uvm/0.1.0"},
            ) as response:
                if response.status != 200:
                    return MirrorTestResult(
                        mirror=mirror,
                        response_time=0.0,
                        success=False,
                        error_message=f"HTTP {response.status} - URL: {test_url}",
                        test_time=start_time,
                    )

                # Just measure response time for the index page
                end_time = time.time()
                response_time = end_time - start_time

                return MirrorTestResult(
                    mirror=mirror,
                    response_time=response_time,
                    success=True,
                    test_time=start_time,
                )

        except asyncio.TimeoutError:
            return MirrorTestResult(
                mirror=mirror,
                response_time=0.0,
                success=False,
                error_message="Timeout",
                test_time=start_time,
            )
        except aiohttp.ClientError as e:
            return MirrorTestResult(
                mirror=mirror,
                response_time=0.0,
                success=False,
                error_message=f"Network error: {e}",
                test_time=start_time,
            )
        except Exception as e:
            return MirrorTestResult(
                mirror=mirror,
                response_time=0.0,
                success=False,
                error_message=f"Unexpected error: {e}",
                test_time=start_time,
            )

    async def test_mirror(self, mirror: Mirror) -> MirrorTestResult:
        """Test a single mirror.

        Args:
            mirror: Mirror to test.

        Returns:
            MirrorTestResult with timing information.
        """
        async with aiohttp.ClientSession() as session:
            return await self._download_speed_test(session, mirror)

    async def test_mirrors(
        self,
        mirrors: list[Mirror],
        max_concurrent: int = 5,
    ) -> List[MirrorTestResult]:
        """Test multiple mirrors concurrently.

        Args:
            mirrors: List of mirrors to test.
            max_concurrent: Maximum number of concurrent tests.

        Returns:
            List of MirrorTestResult sorted by response time.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def test_with_semaphore(mirror: Mirror) -> MirrorTestResult:
            async with semaphore:
                return await self.test_mirror(mirror)

        tasks = [test_with_semaphore(mirror) for mirror in mirrors]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Sort successful results by response time
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        successful_results.sort(key=lambda x: x.response_time)

        return successful_results + failed_results

    def load_cache(self) -> Dict[str, tuple]:
        """Load speed test cache.

        Returns:
            Dictionary mapping mirror names to cached (response_time, timestamp) tuples.
        """
        if not self._cache_path.exists():
            return {}

        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Filter cache entries older than 24 hours
                current_time = time.time()
                return {
                    name: (rt, timestamp)
                    for name, (rt, timestamp) in data.items()
                    if current_time - timestamp < 86400  # 24 hours
                }
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            return {}

    def save_cache(self, results: List[MirrorTestResult]) -> None:
        """Save speed test results to cache.

        Args:
            results: Test results to cache.
        """
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        cache_data = self.load_cache()
        current_time = time.time()

        # Update cache with new results
        for result in results:
            if result.success:
                cache_data[result.mirror.name] = (result.response_time, current_time)

        # Save cache
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except OSError:
            pass  # Ignore cache save errors

    def get_cached_speed(self, mirror_name: str) -> Optional[float]:
        """Get cached speed for a mirror.

        Args:
            mirror_name: Name of the mirror.

        Returns:
            Cached response time in seconds, or None if not cached.
        """
        cache_data = self.load_cache()
        cache_entry = cache_data.get(mirror_name)
        if cache_entry and isinstance(cache_entry, (list, tuple)) and len(cache_entry) >= 1:
            return float(cache_entry[0])
        return None

    async def test_and_cache(
        self,
        mirrors: List[Mirror],
        use_cache: bool = True,
        max_concurrent: int = 5,
    ) -> List[MirrorTestResult]:
        """Test mirrors and cache results.

        Args:
            mirrors: List of mirrors to test.
            use_cache: Whether to use cached results.
            max_concurrent: Maximum number of concurrent tests.

        Returns:
            List of MirrorTestResult sorted by response time.
        """
        cache = self.load_cache() if use_cache else {}
        mirrors_to_test = []
        cached_results = []

        # Separate mirrors that need testing from cached ones
        for mirror in mirrors:
            cached_time = cache.get(mirror.name)
            if cached_time and isinstance(cached_time, (list, tuple)) and len(cached_time) >= 2:
                result = MirrorTestResult(
                    mirror=mirror,
                    response_time=cached_time[0],
                    success=True,
                    test_time=cached_time[1],
                )
                cached_results.append(result)
            else:
                mirrors_to_test.append(mirror)

        # Test mirrors that need testing
        test_results = []
        if mirrors_to_test:
            test_results = await self.test_mirrors(mirrors_to_test, max_concurrent)
            self.save_cache(test_results)

        # Combine and sort all results
        all_results = cached_results + test_results
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]

        successful_results.sort(key=lambda x: x.response_time)

        return successful_results + failed_results

    def format_results_table(self, results: List[MirrorTestResult]) -> str:
        """Format test results as a table.

        Args:
            results: Test results to format.

        Returns:
            Formatted table string.
        """
        from tabulate import tabulate

        table_data = []
        for i, result in enumerate(results, 1):
            if result.success:
                time_str = f"{result.response_time:.3f}s"
                status = "[OK]"
            else:
                time_str = "N/A"
                status = "[FAIL]"

            table_data.append([
                i,
                result.mirror.name,
                result.mirror.netloc,
                time_str,
                status,
                result.error_message if not result.success else "",
            ])

        headers = ["#", "Name", "URL", "Time", "Status", "Error"]
        return tabulate(table_data, headers=headers, tablefmt="grid")

    def get_recommendations(
        self,
        results: List[MirrorTestResult],
        top_n: int = 3,
    ) -> List[MirrorTestResult]:
        """Get top N mirror recommendations.

        Args:
            results: Test results.
            top_n: Number of recommendations to return.

        Returns:
            List of top MirrorTestResult recommendations.
        """
        successful_results = [r for r in results if r.success]
        return successful_results[:top_n]

    def __repr__(self) -> str:
        """String representation of SpeedTester."""
        return f"SpeedTester(timeout={self.timeout}, cache_path={self._cache_path})"