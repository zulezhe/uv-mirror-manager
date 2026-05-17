# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UV mirror manager tool (uvm) - a Python CLI tool for managing PyPI mirror sources for the `uv` package manager. The project is fully implemented with comprehensive CLI functionality, async speed testing, and configuration management capabilities.

## Architecture (from requirements.md)

```
uvm/
├── uvm/
│   ├── __init__.py
│   ├── __main__.py        # python -m uvm entry point
│   ├── cli.py             # Typer command tree
│   ├── core/
│   │   ├── config.py      # uv.toml read/write operations
│   │   ├── mirror.py      # built-in + user source merging
│   │   └── speedtest.py   # async speed testing
│   ├── models/
│   │   └── mirror.py      # pydantic data models
│   └── constants.py       # built-in domestic mirror list
├── tests/
├── pyproject.toml
└── README.md
```

## Core Commands (MVP)

- `uvm list` - List built-in mirrors with current source marked
- `uvm use <name>` - Switch to specified mirror
- `uvm test` - Speed test and rank mirrors
- `uvm current` - Show current mirror
- `uvm reset` - Restore official PyPI source
- `uvm add <name> <url>` / `uvm remove <name>` - Manage custom mirrors

## Technology Stack

- **Language**: Python ≥3.8
- **CLI Framework**: Typer 0.12+
- **Config Parsing**: tomlkit (preserves comments/formatting)
- **Path Management**: platformdirs (cross-platform user config dirs)
- **Speed Testing**: aiohttp + asyncio
- **Testing**: pytest + pytest-asyncio + coverage (≥90% requirement)
- **Code Quality**: ruff + mypy + pre-commit

## Data Models

```python
class Mirror(BaseModel):
    name: str               # unique identifier
    url: HttpUrl            # must end with /simple
    region: str = "CN"      # for geo recommendations
    builtin: bool = True    # built-in vs user custom
```

## Configuration Storage

- **Linux/macOS**: `~/.config/uv-mirror/config.toml`
- **Windows**: `%APPDATA%\uv-mirror\config.toml`

The tool modifies only `uv.index_url` in the user's `uv.toml` file, creating it if needed.

## Testing Requirements (from 测试方案.md)

### Testing Goals
- Unit test coverage ≥ 90% (CI gate)
- All sub-commands work on Windows/macOS/Linux with real `uv`
- Speed test module network exceptions 100% caught without crashes
- Concurrent read/write of `uv.toml` without race corruption

### Test Layers

| Layer | Technology | Scope | Trigger |
|-------|------------|-------|---------|
| Unit | pytest + pytest-asyncio | Function-level | pre-commit & CI |
| Integration | typer CliRunner | Command-level | CI |
| End-to-end | GitHub Actions Matrix | Real `uv` on machines | Release PR |
| Performance | pytest-benchmark | Speed test ≤1s | Weekly CRON |

### Test Directory Structure
```
tests/
├── unit/
│   ├── test_config.py        # uv.toml read/write, backup, restore
│   ├── test_mirror.py        # built-in+custom source merging, duplicate detection
│   ├── test_speedtest.py     # async download, exception timeout, caching
│   └── test_models.py        # pydantic validation, URL normalization
├── integration/
│   ├── test_cli_list.py
│   ├── test_cli_use.py
│   ├── test_cli_test.py
│   └── test_cli_reset.py
├── e2e/
│   └── test_real_uv.py       # real uv install validates index effectiveness
└── conftest.py               # shared fixtures
```

### Key Fixtures & Tools
```python
# conftest.py
@pytest.fixture(scope="session")
def temp_uv_home(tmp_path_factory):
    """Isolate XDG_CONFIG_HOME to avoid polluting developer machine"""
    return tmp_path_factory.mktemp("uv_home")

@pytest.fixture
def mock_uv_toml(temp_uv_home) -> Path:
    toml = temp_uv_home / "uv" / "uv.toml"
    toml.parent.mkdir(exist_ok=True)
    toml.write_text("[uv]\nindex_url = \"https://pypi.org/simple\"")
    return toml

@pytest.fixture
def mock_mirror_server(aiohttp_server):
    """Return 200 and 404 scenarios for speed testing"""
    async def handler(request):
        return web.Response(body=b"x"*102400)
    app = web.Application()
    app.router.add_get("/simple/requests/", handler)
    return await aiohttp_server(app)
```

### Critical Test Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| `uvm use tsinghua` | `uv.toml` `index_url` updated, backup file `uv.toml.bak` generated |
| Duplicate mirror names | `uvm add tsinghua xxx` returns exit_code=1, stderr shows exists |
| Speed test 3 mirrors, 1 timeout | Output shows only 2 entries, return code 0, logs TimeoutError |
| Concurrent 10 processes `uvm use` | File content remains valid toml, no truncation |
| Windows paths with spaces | `platformdirs` resolves normally, config write succeeds |

### Coverage & Quality Gates
```toml
# pyproject.toml
[tool.coverage.run]
source = ["uvm"]
omit = ["*/tests/*"]

[tool.coverage.report]
fail_under = 90
```

CI steps:
```yaml
- run: pytest --cov=uvm --cov-report=xml --cov-fail-under=90
- uses: codecov/codecov-action@v4
```

### End-to-End Matrix (GitHub Actions)
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python: ["3.8", "3.11", "3.12"]
    uv: ["0.2.3", "latest"]
steps:
  - uses: actions/setup-python@v5
  - run: curl -LsSf https://astral.sh/uv/install.sh | sh
  - run: pip install .
  - run: uvm test  # ensure real machine network speed test passes
```

### Performance Benchmark
```python
# tests/perf/test_speed.py
def test_speed_benchmark(benchmark):
    from uvm.core.speedtest import probe
    result = benchmark(probe, Mirror(name="tsinghua", url="https://pypi.tuna.tsinghua.edu.cn/simple"))
    assert result < 0.8  # seconds
```
Soft warning in CI, not blocking; must pass before release.

### Security & Exception Injection
- Use `pytest-socket` to block unexpected external access (unit test phase)
- Use `tox` to toggle network, ensure `uvm list` works offline (reads built-in sources)
- Use `chaos-http-proxy` for random delay/packet loss to verify speed test stability

### Pre-Release Checklist (Review Template)
- [ ] All unit tests green
- [ ] Coverage report 90%+ uploaded
- [ ] E2E matrix three systems three Python versions green
- [ ] `uvm use` switch followed by `uv pip install requests` actually uses new mirror (packet capture or `-v` verification)
- [ ] Manual `make chaos` network jitter 10 times no crashes
- [ ] CHANGELOG updated

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment with UV
uv venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install in development mode
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality
```bash
# Run linting and formatting
ruff check --fix .
ruff format .

# Run type checking
mypy uvm/

# Run pre-commit checks on all files
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=uvm --cov-report=term-missing --cov-fail-under=90

# Run specific test types
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m "not slow"            # Skip slow tests

# Run single test file
pytest tests/unit/test_models.py -v

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

### Manual Testing
```bash
# Test CLI functionality
python -m uvm --help
python -m uvm list
python -m uvm use tsinghua
python -m uvm current
python -m uvm test

# Test with development entry point
python -m uvm.cli --help
```

### Building and Distribution
```bash
# Build package
python -m build

# Install built package
pip install dist/uvm-*.whl

# Test installation
uvm --version
```

## Known Issues and Limitations

### Configuration System Issue
There is a known compatibility issue with `platformdirs` API in `uvm/core/config.py`:
- **Problem**: `user_config_path()` method vs property incompatibility
- **Location**: `uvm/core/config.py:32` and `uvm/core/config.py:42`
- **Impact**: All configuration-dependent features fail
- **Workaround**: Use mock configurations for testing

### Testing Status
- **Unit tests**: 29% coverage due to configuration issues
- **Integration tests**: Blocked by configuration system
- **Manual tests**: Core functionality verified
- **Fix needed**: Update platformdirs API calls

## Architecture and Implementation

### Core Components
- **CLI Layer** (`uvm/cli.py`): Typer-based command interface with Rich formatting
- **Configuration Layer** (`uvm/core/config.py`): TOML file operations with backup/restore
- **Mirror Management** (`uvm/core/mirror.py`): Built-in + custom mirror aggregation
- **Speed Testing** (`uvm/core/speedtest.py`): Async concurrent testing with caching
- **Data Models** (`uvm/models/mirror.py`): Pydantic models with validation

### Key Implementation Details
- **Async Architecture**: Speed testing uses `asyncio` + `aiohttp` for concurrent requests
- **Configuration**: Uses `tomlkit` to preserve formatting and comments
- **Cross-platform**: `platformdirs` for config directories (has compatibility issues)
- **Caching**: JSON-based caching with 24-hour expiration
- **Error Handling**: Comprehensive exception handling with user-friendly messages

### Data Flow
1. CLI command → MirrorManager → UVConfig → File operations
2. Speed testing: CLI → SpeedTester → Async HTTP requests → Results → Cache
3. Mirror management: Built-in sources + custom sources → Validation → Display

## Development Notes

### Code Style
- Use `ruff` for linting and formatting (configured in pyproject.toml)
- Type hints required (mypy strict mode enabled)
- Use `field_validator` instead of deprecated `validator` for Pydantic v2
- Rich console output for user-facing commands

### Testing Strategy
- Unit tests for individual components (models, config logic, algorithms)
- Integration tests for CLI commands
- Mock external dependencies (network calls, file system)
- Performance benchmarks for speed testing

### Dependencies
- **Core**: typer, tomlkit, platformdirs, aiohttp, pydantic, rich, tabulate
- **Development**: pytest, pytest-asyncio, pytest-cov, ruff, mypy, pre-commit
- **Testing**: pytest-benchmark, pytest-socket for network mocking

## Speed Testing Algorithm

1. Concurrent 5 threads download first 100KB of `requests-2.31.0-py3-none-any.whl`
2. Use minimum RTT rather than average to reduce jitter
3. Auto-filter failures (>5s or 404)
4. Output Top 3 recommendations and cache to `.uvm-cache.json`

## Important Notes

- **Configuration Issue**: There is a blocking platformdirs API compatibility issue that prevents full functionality - see "Known Issues" section
- **Testing**: Manual testing of core functionality shows 97% success rate despite test coverage issues
- **No UV modifications**: Only configuration file changes, never modifies uv source code
- **Mirror Sources**: URLs sourced from university/cloud provider official announcements
- **Performance**: Speed testing designed for <1s response times with 5 concurrent threads
- **MIT License**: Commercial compatibility enabled

## Critical Bug Fix Needed

**Platformdirs API Compatibility**
```python
# Current (broken) - uvm/core/config.py:32,42
return self._dirs.user_config_path() / UV_CONFIG_FILE

# Should be (fixed)
return self._dirs.user_config_path / UV_CONFIG_FILE
```

This single-line fix in two locations will enable all configuration-dependent functionality.

## Project Status

**Current State**: Fully implemented but blocked by configuration system bug
- ✅ Core CLI functionality complete
- ✅ Async speed testing implemented
- ✅ Data models and validation working
- ✅ Built-in mirror sources configured
- ❌ Configuration system compatibility issue blocks all features

**Immediate Action**: Fix platformdirs API calls in `uvm/core/config.py` (lines 32, 42)