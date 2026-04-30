from bs4 import BeautifulSoup
from readability import Document

from ..models import Article


class GenericExtractor:
    domains: tuple[str, ...] = ()

    def extract(self, soup: BeautifulSoup, url: str) -> Article:
        raw_html = str(soup)
        doc = Document(raw_html)
        title = doc.title() or (soup.title.string.strip() if soup.title and soup.title.string else "untitled")
        content_html = doc.summary(html_partial=True)
        content_soup = BeautifulSoup(content_html, "lxml")
        root = content_soup.body or content_soup
        return Article(url=url, title=title, content_root=root, site="generic")
