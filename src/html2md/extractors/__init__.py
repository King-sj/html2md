from urllib.parse import urlparse

from .base import Extractor
from .generic import GenericExtractor

_REGISTRY: list[type[Extractor]] = []


def register(cls: type[Extractor]) -> type[Extractor]:
    _REGISTRY.append(cls)
    return cls


def pick(url: str) -> Extractor:
    host = (urlparse(url).hostname or "").lower()
    for cls in _REGISTRY:
        if any(host == d or host.endswith("." + d) for d in cls.domains):
            return cls()
    return GenericExtractor()


# 触发 @register 副作用 —— 必须放在 register 定义之后
from . import cnblogs  # noqa: E402,F401

__all__ = ["Extractor", "GenericExtractor", "register", "pick"]
