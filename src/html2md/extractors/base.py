from typing import Protocol

from bs4 import BeautifulSoup

from ..models import Article


class Extractor(Protocol):
    domains: tuple[str, ...]

    def extract(self, soup: BeautifulSoup, url: str) -> Article: ...
