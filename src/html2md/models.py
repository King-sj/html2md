from dataclasses import dataclass, field
from datetime import date

from bs4 import Tag


@dataclass
class Article:
    url: str
    title: str
    content_root: Tag
    site: str = "generic"
    author: str | None = None
    publish_date: date | None = None
    tags: list[str] = field(default_factory=list)
