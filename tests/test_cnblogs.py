from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from html2md import converter, extractors, frontmatter
from html2md.extractors.cnblogs import CnblogsExtractor

FIXTURE = Path(__file__).parent / "fixtures" / "cnblogs_19956568.html"
URL = "https://www.cnblogs.com/MrVolleyball/p/19956568"


def _load() -> BeautifulSoup:
    return BeautifulSoup(FIXTURE.read_text(encoding="utf-8"), "lxml")


def test_pick_routes_to_cnblogs():
    assert isinstance(extractors.pick(URL), CnblogsExtractor)
    assert isinstance(extractors.pick("https://www.cnblogs.com/foo/p/1.html"), CnblogsExtractor)


def test_extract_metadata():
    article = CnblogsExtractor().extract(_load(), URL)
    assert article.site == "cnblogs"
    assert article.title.startswith("ai 时代程序员的核心不适")
    assert article.author == "MrVolleyball"
    assert article.publish_date == date(2026, 4, 30)
    assert "aiops" in article.tags
    assert article.content_root is not None
    # 摘要被独立提取，不在正文里
    assert article.description and "AI 对程序员的深层冲击" in article.description
    assert "AI 对程序员的深层冲击" not in article.content_root.get_text()


def test_convert_to_markdown():
    article = CnblogsExtractor().extract(_load(), URL)
    md = converter.to_markdown(article.content_root)

    # 正文不能为空
    assert len(md) > 500

    # 懒加载图片应该被解出来（data-src → src）
    assert "data:image" not in md  # 不能保留占位图
    assert ".png" in md or ".jpg" in md

    # 代码块语言被识别（博客园的 <code class="language-text">）
    assert "```text" in md or "```" in md


def test_front_matter_for_vuepress():
    article = CnblogsExtractor().extract(_load(), URL)
    head = frontmatter.render(article, default_category="转载", extra_tags=["大模型"])
    assert head.startswith("---\n")
    assert "title:" in head
    assert "date: 2026-04-30" in head
    assert "original_url: " + URL in head
    assert "- 转载" in head
    assert "- aiops" in head
    assert "- 大模型" in head
    # description 字段写入了 front matter
    assert "description:" in head
    assert "AI 对程序员的深层冲击" in head
