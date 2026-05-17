'''
Author: oliver
Date: 2025-10-16 23:10:04
LastEditors: oliver
LastEditTime: 2025-11-24 23:36:47
Description: 
'''
"""UV镜像源管理工具 - 一键管理uv的PyPI镜像源"""

__version__ = "0.1.1"
__author__ = "UVM Contributors"
__email__ = "contributors@uvm.dev"

from uvm.models.mirror import Mirror  # noqa: E402

__all__ = ["Mirror", "__version__"]
