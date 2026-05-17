# UVM - UV 镜像源管理工具

**[English](README_EN.md)** | **中文**

[![PyPI version](https://badge.fury.io/py/ouvm.svg)](https://badge.fury.io/py/ouvm)
[![Python versions](https://img.shields.io/pypi/pyversions/ouvm.svg)](https://pypi.org/project/ouvm/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/zulezhe/uv-mirror-manager/blob/main/LICENSE)

UVM 是一个专为 [uv](https://github.com/astral-sh/uv) 包管理器设计的 PyPI 镜像源管理工具，提供一键切换、测速推荐、自定义镜像源等功能。

## 功能特性

- 快速切换 - 一键切换国内外 PyPI 镜像源
- 速度测试 - 自动测试镜像源响应时间并排序推荐
- 自定义源 - 支持添加和管理自定义镜像源
- 智能缓存 - 缓存测速结果，提高后续使用体验
- 跨平台 - 支持 Windows、macOS、Linux
- 安全可靠 - 仅修改配置文件，不侵入 uv 源码

## 安装

```bash
pip install ouvm
```

> 包名为 `ouvm`，安装后命令名为 `uvm`。

## 快速开始

### 列出所有可用镜像源

```bash
uvm list
# 或短命令
uvm ls
```

### 切换到指定镜像源

```bash
uvm use tsinghua
# 或短命令
uvm u tsinghua
```

### 测试镜像源速度

```bash
uvm test
# 或短命令
uvm t
```

### 查看当前镜像源

```bash
uvm current
# 或短命令
uvm cur
```

### 添加自定义镜像源

```bash
uvm add company https://pypi.company.com/simple --description "公司内部镜像源"
```

### 删除自定义镜像源

```bash
uvm remove company
# 或短命令
uvm rm company
```

### 恢复官方源

```bash
uvm reset
# 或短命令
uvm r
```

### 搜索镜像源

```bash
uvm search tsinghua
# 或短命令
uvm s tsinghua
```

## 内置镜像源

| 名称 | URL | 地区 | 描述 |
|------|-----|------|------|
| official | https://pypi.org/simple | US | 官方 PyPI 源 |
| tsinghua | https://pypi.tuna.tsinghua.edu.cn/simple | CN | 清华大学镜像源 |
| aliyun | https://mirrors.aliyun.com/pypi/simple | CN | 阿里云镜像源 |
| douban | https://pypi.doubanio.com/simple | CN | 豆瓣镜像源 |
| ustc | https://mirrors.ustc.edu.cn/pypi/web/simple | CN | 中科大镜像源 |
| tencent | https://mirrors.cloud.tencent.com/pypi/simple | CN | 腾讯云镜像源 |
| huawei | https://repo.huaweicloud.com/repository/pypi/simple | CN | 华为云镜像源 |
| netease | https://mirrors.163.com/pypi/simple | CN | 网易镜像源 |
| sjtu | https://mirror.sjtu.edu.cn/pypi/simple | CN | 上海交通大学镜像源 |
| zju | https://mirrors.zju.edu.cn/pypi/simple | CN | 浙江大学镜像源 |

## 命令参考

| 命令 | 短命令 | 说明 |
|------|--------|------|
| `uvm list` | `uvm ls` | 列出所有镜像源 |
| `uvm use <name>` | `uvm u <name>` | 切换镜像源 |
| `uvm test` | `uvm t` | 测速并排序 |
| `uvm current` | `uvm cur` | 显示当前镜像源 |
| `uvm reset` | `uvm r` | 恢复官方源 |
| `uvm add <name> <url>` | `uvm a <name> <url>` | 添加自定义镜像源 |
| `uvm remove <name>` | `uvm rm <name>` | 删除自定义镜像源 |
| `uvm search <query>` | `uvm s <query>` | 搜索镜像源 |
| `uvm --version` | `uvm -v` | 显示版本号 |

### test 命令选项

```bash
uvm test [--cache/--no-cache] [--timeout <seconds>]
```

- `--cache/--no-cache` - 是否使用缓存结果（默认：使用缓存）
- `--timeout, -t` - 超时时间，单位秒（默认：5.0）

### add 命令选项

```bash
uvm add <name> <url> [--description <text>] [--region <code>]
```

- `name` - 镜像源名称
- `url` - 镜像源 URL（必须以 `/simple` 结尾）
- `--description, -d` - 镜像源描述
- `--region, -r` - 地区代码（默认：CN）

## 配置文件

UVM 使用以下配置文件：

- **UV 配置**: `~/.config/uv/uv.toml` (Linux/macOS) 或 `%APPDATA%\uv\uv.toml` (Windows)
- **UVM 配置**: `~/.config/uv-mirror/config.toml` (Linux/macOS) 或 `%APPDATA%\uv-mirror\config.toml` (Windows)
- **缓存文件**: `~/.cache/uv-mirror/.uvm-cache.json`

## 开发

```bash
# 克隆仓库
git clone https://github.com/zulezhe/uv-mirror-manager.git
cd uv-mirror-manager

# 创建虚拟环境并安装开发依赖
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# 代码检查
ruff check --fix .
ruff format .

# 运行测试
pytest --cov=uvm --cov-report=term-missing
```

## 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 相关项目

- [uv](https://github.com/astral-sh/uv) - 极速的 Python 包安装器
- [nrm](https://github.com/Pana/nrm) - NPM 镜像源管理工具（灵感来源）
