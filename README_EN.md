# UVM - UV Mirror Manager

**English** | **[中文](README.md)**

[![PyPI version](https://badge.fury.io/py/ouvm.svg)](https://badge.fury.io/py/ouvm)
[![Python versions](https://img.shields.io/pypi/pyversions/ouvm.svg)](https://pypi.org/project/ouvm/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/zulezhe/uv-mirror-manager/blob/main/LICENSE)

UVM is a PyPI mirror source manager designed for the [uv](https://github.com/astral-sh/uv) package manager. It provides one-click switching, speed testing, and custom mirror management.

## Features

- Fast Switching - Switch between PyPI mirrors with a single command
- Speed Testing - Automatically test mirror response times and rank them
- Custom Mirrors - Add and manage your own mirror sources
- Smart Caching - Cache speed test results for better UX
- Cross-Platform - Support for Windows, macOS, and Linux
- Safe - Only modifies config files, never touches uv source code

## Installation

```bash
pip install ouvm
```

> The package name is `ouvm`, but the CLI command is `uvm`.

## Quick Start

### List all available mirrors

```bash
uvm list
# or short alias
uvm ls
```

### Switch to a specific mirror

```bash
uvm use tsinghua
# or short alias
uvm u tsinghua
```

### Test mirror speed

```bash
uvm test
# or short alias
uvm t
```

### Show current mirror

```bash
uvm current
# or short alias
uvm cur
```

### Add a custom mirror

```bash
uvm add company https://pypi.company.com/simple --description "Company internal mirror"
```

### Remove a custom mirror

```bash
uvm remove company
# or short alias
uvm rm company
```

### Reset to official source

```bash
uvm reset
# or short alias
uvm r
```

### Search mirrors

```bash
uvm search tsinghua
# or short alias
uvm s tsinghua
```

## Built-in Mirrors

| Name | URL | Region | Description |
|------|-----|--------|-------------|
| official | https://pypi.org/simple | US | Official PyPI |
| tsinghua | https://pypi.tuna.tsinghua.edu.cn/simple | CN | Tsinghua University |
| aliyun | https://mirrors.aliyun.com/pypi/simple | CN | Alibaba Cloud |
| douban | https://pypi.doubanio.com/simple | CN | Douban |
| ustc | https://mirrors.ustc.edu.cn/pypi/web/simple | CN | USTC |
| tencent | https://mirrors.cloud.tencent.com/pypi/simple | CN | Tencent Cloud |
| huawei | https://repo.huaweicloud.com/repository/pypi/simple | CN | Huawei Cloud |
| netease | https://mirrors.163.com/pypi/simple | CN | NetEase |
| sjtu | https://mirror.sjtu.edu.cn/pypi/simple | CN | Shanghai Jiao Tong University |
| zju | https://mirrors.zju.edu.cn/pypi/simple | CN | Zhejiang University |

## Command Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `uvm list` | `uvm ls` | List all mirrors |
| `uvm use <name>` | `uvm u <name>` | Switch mirror |
| `uvm test` | `uvm t` | Test speed and rank |
| `uvm current` | `uvm cur` | Show current mirror |
| `uvm reset` | `uvm r` | Reset to official source |
| `uvm add <name> <url>` | `uvm a <name> <url>` | Add custom mirror |
| `uvm remove <name>` | `uvm rm <name>` | Remove custom mirror |
| `uvm search <query>` | `uvm s <query>` | Search mirrors |
| `uvm --version` | `uvm -v` | Show version |

### test command options

```bash
uvm test [--cache/--no-cache] [--timeout <seconds>]
```

- `--cache/--no-cache` - Use cached results or not (default: use cache)
- `--timeout, -t` - Timeout in seconds (default: 5.0)

### add command options

```bash
uvm add <name> <url> [--description <text>] [--region <code>]
```

- `name` - Mirror name
- `url` - Mirror URL (must end with `/simple`)
- `--description, -d` - Mirror description
- `--region, -r` - Region code (default: CN)

## Configuration

UVM uses the following configuration files:

- **UV config**: `~/.config/uv/uv.toml` (Linux/macOS) or `%APPDATA%\uv\uv.toml` (Windows)
- **UVM config**: `~/.config/uv-mirror/config.toml` (Linux/macOS) or `%APPDATA%\uv-mirror\config.toml` (Windows)
- **Cache**: `~/.cache/uv-mirror/.uvm-cache.json`

## Development

```bash
# Clone the repository
git clone https://github.com/zulezhe/uv-mirror-manager.git
cd uv-mirror-manager

# Create virtual environment and install dev dependencies
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# Code linting
ruff check --fix .
ruff format .

# Run tests
pytest --cov=uvm --cov-report=term-missing
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

This project is licensed under the [MIT](LICENSE) License.

## Related Projects

- [uv](https://github.com/astral-sh/uv) - An extremely fast Python package installer
- [nrm](https://github.com/Pana/nrm) - NPM registry manager (inspiration for this project)
