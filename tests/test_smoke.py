"""Offline smoke: feed a tiny HTML to extractor + converter + frontmatter + slug."""
from bs4 import BeautifulSoup

from html2md import converter, extractors, frontmatter
from html2md.slug import make_slug

SAMPLE = """
<html><head><title>测试文章</title></head><body>
<article>
  <h1>测试文章</h1>
  <p>这是第一段，包含 <strong>加粗</strong> 与 <a href="https://example.com">链接</a>。
  正文需要足够长，readability 才会认为这是真正的文章内容而保留全部子节点，
  否则它会把短小的列表当作页面装饰过滤掉，从而影响后续转换结果。</p>
  <p>这是第二段，继续补充内容，让正文密度足够高，避免 readability 误判，
  以便我们可以验证整个 HTML 到 Markdown 的转换链路在端到端时的行为表现。</p>
  <h2>代码示例</h2>
  <pre><code class="language-python">def hello():
    print("hi")</code></pre>
  <h2>列表</h2>
  <ul><li>第一项条目，多写一点字以免被裁剪</li><li>第二项条目，同样多写一点字以免被裁剪</li></ul>
  <h2>图片</h2>
  <p><img data-src="https://example.com/a.png" alt="懒加载图"></p>
</article>
</body></html>
"""


def test_pipeline_offline():
    soup = BeautifulSoup(SAMPLE, "lxml")
    extractor = extractors.pick("https://example.com/post/1")
    article = extractor.extract(soup, "https://example.com/post/1")

    assert article.title.strip() == "测试文章"
    assert article.site == "generic"

    md = converter.to_markdown(article.content_root)

    assert "```python" in md
    assert "def hello():" in md
    assert "**加粗**" in md
    assert "[链接](https://example.com)" in md
    assert "![懒加载图](https://example.com/a.png)" in md
    assert "- 第一项条目" in md and "- 第二项条目" in md

    head = frontmatter.render(article, default_category="转载", extra_tags=["python"])
    assert head.startswith("---\n")
    assert "title: 测试文章" in head
    assert "original_url: https://example.com/post/1" in head
    assert "- 转载" in head
    assert "- python" in head

    slug = make_slug(article.title)
    assert slug, "slug should not be empty"
