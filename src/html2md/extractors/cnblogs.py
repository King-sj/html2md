import re
from datetime import date, datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from ..models import Article
from . import register

_DATE_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def _parse_date(text: str | None) -> date | None:
    if not text:
        return None
    m = _DATE_RE.search(text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


@register
class CnblogsExtractor:
    domains: tuple[str, ...] = ("cnblogs.com",)

    def extract(self, soup: BeautifulSoup, url: str) -> Article:
        title_el = soup.select_one("#cb_post_title_url, a.postTitle2, .postTitle a, h1.postTitle")
        title = title_el.get_text(strip=True) if title_el else (
            (soup.title.string or "").strip() if soup.title and soup.title.string else "untitled"
        )

        body = soup.select_one("#cnblogs_post_body, #post-body, .postBody, .blogpost-body")
        if not body:
            raise ValueError("cnblogs: 找不到正文容器（#cnblogs_post_body）")

        author = self._author(soup, url)
        publish_date = _parse_date(soup.select_one("#post-date") and soup.select_one("#post-date").get_text())
        if publish_date is None:
            desc = soup.select_one(".postDesc")
            publish_date = _parse_date(desc.get_text() if desc else None)

        tags = self._tags(soup)

        return Article(
            url=url,
            title=title,
            author=author,
            publish_date=publish_date,
            tags=tags,
            content_root=body,
            site="cnblogs",
        )

    @staticmethod
    def _author(soup: BeautifulSoup, url: str) -> str | None:
        meta_author = _meta(soup, "author")
        if meta_author:
            return meta_author
        # URL 路径首段就是用户名：https://www.cnblogs.com/<user>/p/<id>.html
        parts = [p for p in urlparse(url).path.split("/") if p]
        if parts:
            return parts[0]
        return None

    @staticmethod
    def _tags(soup: BeautifulSoup) -> list[str]:
        # 博客园主页面的 tag/category 多数通过 ajax 注入，meta keywords 是最稳来源
        kw = _meta(soup, "keywords") or ""
        raw = [t.strip() for t in re.split(r"[,，;；]", kw) if t.strip()]
        # 过滤博客园通用噪音关键字
        ignore = {"博客园", "cnblogs", "首页"}
        return [t for t in raw if t.lower() not in ignore]
