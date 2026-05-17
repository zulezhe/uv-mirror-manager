"""Built-in mirror sources and constants."""

from typing import List

from uvm.models.mirror import Mirror

# 内置镜像源列表
BUILTIN_MIRRORS: List[Mirror] = [
    Mirror(
        name="official",
        url="https://pypi.org/simple",
        region="US",
        description="官方PyPI源",
    ),
    Mirror(
        name="tsinghua",
        url="https://pypi.tuna.tsinghua.edu.cn/simple",
        region="CN",
        description="清华大学镜像源",
    ),
    Mirror(
        name="aliyun",
        url="https://mirrors.aliyun.com/pypi/simple",
        region="CN",
        description="阿里云镜像源",
    ),
    Mirror(
        name="douban",
        url="https://pypi.doubanio.com/simple",
        region="CN",
        description="豆瓣镜像源",
    ),
    Mirror(
        name="ustc",
        url="https://mirrors.ustc.edu.cn/pypi/web/simple",
        region="CN",
        description="中科大镜像源",
    ),
    Mirror(
        name="tencent",
        url="https://mirrors.cloud.tencent.com/pypi/simple",
        region="CN",
        description="腾讯云镜像源",
    ),
    Mirror(
        name="huawei",
        url="https://repo.huaweicloud.com/repository/pypi/simple",
        region="CN",
        description="华为云镜像源",
    ),
    Mirror(
        name="netease",
        url="https://mirrors.163.com/pypi/simple",
        region="CN",
        description="网易镜像源",
    ),
    Mirror(
        name="sjtu",
        url="https://mirror.sjtu.edu.cn/pypi/simple",
        region="CN",
        description="上海交通大学镜像源",
    ),
    Mirror(
        name="zju",
        url="https://mirrors.zju.edu.cn/pypi/simple",
        region="CN",
        description="浙江大学镜像源",
    ),
]

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 5.0

# 测速下载文件大小（字节）
SPEEDTEST_SIZE = 102400  # 100KB

# 测试包名
SPEEDTEST_PACKAGE = "setuptools-68.0.0-py3-none-any.whl"

# 配置文件版本
CONFIG_VERSION = 1

# 用户配置文件名
USER_CONFIG_FILE = "config.toml"

# UV配置文件名
UV_CONFIG_FILE = "uv.toml"

# UV配置备份文件名
UV_CONFIG_BACKUP = "uv.toml.bak"

# 缓存文件名
CACHE_FILE = ".uvm-cache.json"

# 支持的Python版本
SUPPORTED_PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

# CLI退出码
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_NETWORK_ERROR = 3
EXIT_CONFIG_ERROR = 4