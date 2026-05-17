"""Pytest configuration and shared fixtures."""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import tomlkit
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from uvm.constants import BUILTIN_MIRRORS
from uvm.core.config import UVConfig
from uvm.models.mirror import Mirror


@pytest.fixture(scope="session")
def temp_uv_home(tmp_path_factory) -> Path:
    """Isolate XDG_CONFIG_HOME to avoid polluting developer machine."""
    return tmp_path_factory.mktemp("uv_home")


@pytest.fixture
def mock_uv_toml(temp_uv_home) -> Path:
    """Create a mock uv.toml file."""
    toml = temp_uv_home / "uv" / "uv.toml"
    toml.parent.mkdir(exist_ok=True)
    # Create empty config file to test "no mirror set" scenario
    toml.write_text("")
    return toml


@pytest.fixture
def mock_uv_config(mock_uv_toml) -> UVConfig:
    """Create UVConfig with mocked paths."""
    import platformdirs
    original_user_config_path = platformdirs.PlatformDirs.user_config_path

    def mock_user_config_path(self) -> Path:
        return mock_uv_toml.parent

    platformdirs.PlatformDirs.user_config_path = property(mock_user_config_path)

    try:
        config = UVConfig()
        yield config
    finally:
        platformdirs.PlatformDirs.user_config_path = original_user_config_path


@pytest.fixture
async def mock_mirror_server(aiohttp_server) -> TestServer:
    """Create a mock mirror server for speed testing."""
    async def handler(request: web.Request) -> web.Response:
        # Return 100KB of dummy data for speed testing
        return web.Response(body=b"x" * 102400, headers={"Content-Type": "application/octet-stream"})

    async def not_found_handler(request: web.Request) -> web.Response:
        return web.Response(status=404, text="Not Found")

    app = web.Application()
    app.router.add_get("/simple/requests-2.31.0-py3-none-any.whl", handler)
    app.router.add_get("/simple/requests-{version}.whl", not_found_handler)
    return await aiohttp_server(app)


@pytest.fixture
def sample_mirrors() -> list[Mirror]:
    """Sample mirrors for testing."""
    return [
        Mirror(
            name="test-official",
            url="https://pypi.org/simple",
            region="US",
            description="Test official source",
        ),
        Mirror(
            name="test-tsinghua",
            url="https://pypi.tuna.tsinghua.edu.cn/simple",
            region="CN",
            description="Test Tsinghua source",
        ),
        Mirror(
            name="test-custom",
            url="https://custom.example.com/simple",
            region="CN",
            builtin=False,
            description="Test custom source",
        ),
    ]


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_cache_file(tmp_path) -> Path:
    """Create a mock cache file."""
    return tmp_path / ".uvm-cache.json"


@pytest.fixture
def mock_uvm_config(tmp_path) -> Path:
    """Create a mock UVM config file."""
    config_data = {
        "meta": {"version": 1},
        "mirrors": {
            "custom": {
                "test-custom": {
                    "url": "https://custom.example.com/simple",
                    "description": "Test custom mirror",
                }
            }
        }
    }

    config_path = tmp_path / "config.toml"
    with open(config_path, "w", encoding="utf-8") as f:
        tomlkit.dump(config_data, f)

    return config_path


@pytest.fixture
def invalid_mirror_data() -> dict:
    """Invalid mirror data for testing validation."""
    return {
        "name": "",  # Invalid empty name
        "url": "https://example.com",  # Missing /simple
        "region": "CN",
        "description": "Invalid mirror",
    }


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch, request):
    """Disable network calls for unit tests unless explicitly enabled."""
    import socket
    original_socket = socket.socket

    def mock_socket(*args, **kwargs):
        raise OSError("Network calls disabled in unit tests")

    # Apply only for tests marked with "unit"
    if hasattr(request.node, "iter_markers"):
        for marker in request.node.iter_markers():
            if marker.name == "unit":
                monkeypatch.setattr("socket.socket", mock_socket)
                break


# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: Mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: Mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: Mark test as requiring network access"
    )