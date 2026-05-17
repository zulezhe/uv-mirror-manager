"""Mirror data models."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Mirror(BaseModel):
    """PyPI mirror source configuration."""

    name: str = Field(..., description="唯一标识符")
    url: HttpUrl = Field(..., description="镜像源URL，必须以/simple结尾")
    region: str = Field(default="CN", description="地区代码，用于地理推荐")
    builtin: bool = Field(default=True, description="是否为内置镜像源")
    description: str = Field(default="", description="镜像源描述")

    @field_validator('url')
    @classmethod
    def validate_simple_url(cls, v: HttpUrl) -> HttpUrl:
        """验证URL是否以/simple结尾."""
        if not str(v).endswith('/simple'):
            raise ValueError('镜像源URL必须以/simple结尾')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证镜像源名称."""
        if not v or not v.strip():
            raise ValueError('镜像源名称不能为空')
        stripped = v.strip()
        if not stripped.replace('-', '').replace('_', '').isalnum():
            raise ValueError('镜像源名称只能包含字母、数字、连字符和下划线')
        return stripped

    def __str__(self) -> str:
        """返回镜像源的字符串表示."""
        return f"{self.name} ({self.url})"

    def __repr__(self) -> str:
        """返回镜像源的详细表示."""
        return f"Mirror(name='{self.name}', url='{self.url}', region='{self.region}')"

    def __hash__(self) -> int:
        """支持集合操作."""
        return hash(self.name.lower())

    def __eq__(self, other: Any) -> bool:
        """基于名称比较镜像源."""
        if not isinstance(other, Mirror):
            return False
        return self.name.lower() == other.name.lower()

    @property
    def is_official(self) -> bool:
        """判断是否为官方PyPI源."""
        return 'pypi.org' in str(self.url)

    @property
    def netloc(self) -> str:
        """获取网络位置部分."""
        return urlparse(str(self.url)).netloc

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式."""
        return {
            'name': self.name,
            'url': str(self.url),
            'region': self.region,
            'builtin': self.builtin,
            'description': self.description,
        }


class MirrorTestResult(BaseModel):
    """镜像源测速结果."""

    mirror: Mirror = Field(..., description="测试的镜像源")
    response_time: float = Field(..., description="响应时间（秒）")
    success: bool = Field(default=True, description="测试是否成功")
    error_message: str = Field(default="", description="错误信息")
    test_time: float = Field(description="测试时间戳")

    def __str__(self) -> str:
        """返回测速结果的字符串表示."""
        if self.success:
            return f"{self.mirror.name}: {self.response_time:.3f}s"
        return f"{self.mirror.name}: FAILED ({self.error_message})"