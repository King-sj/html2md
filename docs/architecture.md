# 架构设计

> 目标：把网页（含微信、知乎、CSDN、掘金、博客园、Medium 等）一键转成可直接放进 VuePress 2 博客的 Markdown 文件。

## 1. 关于 HTML 解析：为什么不写递归下降

HTML 不是 LL/LR 友好的语法，自己写 parser 会踩进无尽的坑：

- **容错**：真实网页 90% 是 tag soup（标签不闭合、属性不引号、`<br>` vs `<br/>`），HTML5 规范专门定义了"如何容错"，自己实现等于重写浏览器
- **编码探测**：`Content-Type` / `<meta charset>` / BOM / chardet 兜底
- **实体解码**：`&nbsp;` / `&#x4e2d;` / 命名实体表
- **HTML5 quirks**：`<table>` 里的 `<tr>` 隐式补 `<tbody>`、`<p>` 里塞 `<div>` 自动闭合

**结论：用现成解析器拿 DOM tree（DOM 就是 HTML 的 AST）。**

| 库 | 实现 | 速度 | 容错 | 用途 |
|----|------|------|------|------|
| `lxml.html` | C (libxml2) | ⭐⭐⭐⭐⭐ | 中 | **主力**，处理正常网页 |
| `html5lib` | 纯 Python | ⭐ | ⭐⭐⭐⭐⭐ | 兜底，处理特别烂的 HTML |
| `BeautifulSoup4` | 包装层 | 跟随后端 | 跟随后端 | 友好 API，写适配器用 |
| `selectolax` | C (Modest/Lexbor) | ⭐⭐⭐⭐⭐⭐ | 中 | 性能党可换 |

**选型**：`BeautifulSoup4(html, "lxml")` 作为开发期 API，性能瓶颈在网络 IO。

## 2. 整体管线

```
URL
 │
 ▼
┌──────────────┐  httpx + Referer/UA + 编码探测
│   Fetcher    │  (raw_html: str, final_url: str)
└──────────────┘
 │
 ▼
┌──────────────┐  bs4(lxml) 解析 → DOM tree（即 AST）
│    Parser    │
└──────────────┘
 │
 ▼
┌──────────────┐  按域名路由 → ZhihuExtractor / CSDNExtractor / GenericExtractor
│  Extractor   │  挖出"正文子树" + 元数据
│              │  → Article(title, author, date, content_root, ...)
└──────────────┘
 │
 ▼
┌──────────────┐  规范化 DOM：去广告、修复 lazy-img、解 figure
│   Cleaner    │
└──────────────┘
 │
 ▼
┌──────────────┐  Visitor 模式：DOM 节点 → Markdown 字符串
│  Converter   │  markdownify 内部就是这个套路
└──────────────┘
 │
 ▼
┌──────────────┐  并发下载图片，重写 ![](url) 为相对路径
│ ImagePipeline│
└──────────────┘
 │
 ▼
┌──────────────┐  拼 VuePress 2 front matter + 正文
│   Renderer   │
└──────────────┘
 │
 ▼
.md + assets/<slug>/01.png ...
```

每段都是**纯函数**：输入输出明确，易测、易换、易并行。

## 3. 核心抽象

### 3.1 `Article` —— 各阶段的传递载体

```python
@dataclass
class Article:
    url: str                       # 最终 URL（处理重定向后）
    title: str
    author: str | None
    publish_date: date | None
    tags: list[str]
    content_root: Tag              # bs4 节点：正文子树根
    site: str                      # "zhihu" / "csdn" / "generic" 等
```

### 3.2 `Extractor` —— 平台适配的唯一扩展点

```python
class Extractor(Protocol):
    domains: tuple[str, ...]                          # 注册到哪些域名
    def extract(self, soup: BeautifulSoup, url: str) -> Article: ...
```

注册表（避免 if-elif 长链）：

```python
# extractors/__init__.py
_REGISTRY: list[type[Extractor]] = []

def register(cls):
    _REGISTRY.append(cls)
    return cls

def pick(url: str) -> Extractor:
    host = urlparse(url).hostname or ""
    for cls in _REGISTRY:
        if any(host.endswith(d) for d in cls.domains):
            return cls()
    return GenericExtractor()
```

新增平台：加一个文件 + `@register`，零修改既有代码。

### 3.3 `Converter` —— Visitor 模式遍历 AST

继承 `markdownify.MarkdownConverter`，扩展几个关键节点：

```python
class BlogConverter(MarkdownConverter):
    def convert_pre(self, el, text, parent_tags):
        # <pre><code class="language-python"> → ```python
        code = el.find("code")
        lang = ""
        if code and (cls := code.get("class")):
            for c in cls:
                if c.startswith(("language-", "lang-")):
                    lang = c.split("-", 1)[1]; break
        body = (code or el).get_text()
        return f"\n```{lang}\n{body.rstrip()}\n```\n\n"

    def convert_img(self, el, text, parent_tags):
        # 懒加载兼容
        src = (el.get("data-src") or el.get("data-original")
               or el.get("data-actualsrc") or el.get("src", ""))
        alt = el.get("alt", "")
        return f"![{alt}]({src})" if src else ""
```

**这就是 AST 的后序遍历 + 节点类型分派**——递归下降的对偶（递归下降构建 AST，这里消费 AST）。

### 3.4 `ImagePipeline` —— 图片本地化

```python
def localize(md: str, asset_dir: Path, base_url: str, slug: str) -> str:
    urls = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
    mapping = {}
    for i, url in enumerate(dedup(urls), 1):
        abs_url = urljoin(base_url, url)
        ext = guess_ext(abs_url)
        local = asset_dir / slug / f"{i:02d}.{ext}"
        download(abs_url, local, referer=base_url)   # 带 Referer 绕防盗链
        mapping[url] = f"./assets/{slug}/{i:02d}.{ext}"
    return replace_all(md, mapping)
```

并发用 `concurrent.futures.ThreadPoolExecutor`，10 张图基本秒出。

## 4. 目录结构

```
src/html2md/
├── __init__.py
├── cli.py                  # typer 入口
├── config.py               # tomllib 读 ~/.html2md/config.toml
├── models.py               # Article dataclass
├── fetcher.py              # httpx 抓取 + 编码探测
├── pipeline.py             # 串起整个管线（编排者）
├── slug.py                 # 中文标题 → 文件名
├── frontmatter.py          # VuePress 2 YAML 生成
├── converter.py            # BlogConverter
├── images.py               # ImagePipeline
└── extractors/
    ├── __init__.py         # register / pick
    ├── base.py             # Extractor 基类（提供通用工具）
    ├── generic.py          # readability 兜底
    ├── zhihu.py
    ├── csdn.py
    ├── juejin.py
    ├── cnblogs.py
    └── medium.py
tests/
├── fixtures/               # 离线 HTML 样本
└── test_*.py
```

## 5. 技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| HTTP | `httpx` | 现代、HTTP/2、API 干净 |
| HTML 解析 | `lxml` + `beautifulsoup4` | lxml 快，bs4 API 友好 |
| 正文兜底 | `readability-lxml` | 通用站点的 Mozilla 算法 |
| HTML→MD | `markdownify` | 最成熟可定制 |
| CLI | `typer` | 类型注解驱动 |
| 配置 | `tomllib`（内置） | Python 3.11+ 无需依赖 |
| Slug | `python-slugify` | 中文标题转文件名 |

## 6. 分阶段实施

**阶段 1：MVP**
1. `pyproject.toml` 加依赖与 cli 入口
2. `fetcher` + `generic` extractor + `converter` + `cli`
3. 图片本地化（顺序编号 `01.png`）
4. VuePress 2 front matter
5. 跑通一篇真实文章

**阶段 2：平台适配**

按使用频率：`zhihu` → `csdn` → `juejin` → `cnblogs` → `medium`，每个一份 fixture 测试。

**阶段 3：体验**
- 配置文件
- 错误处理（403 带 Referer 重试）
- rich 进度条

## 7. 关键决策

1. **图片命名**：`01.png / 02.jpg` 顺序编号，不用 hash。理由：博客里好定位、git diff 友好。
2. **文件名 slug**：`python-slugify` 中文转拼音 + 短横线。
3. **抓取后端**：先 `httpx` 同步；如遇知乎纯 JS 渲染再加 Playwright。
4. **代码块语言**：从 `<code class="language-xxx">` 提取，markdownify 默认丢失。
5. **不做的事**：付费墙、登录、版权判断。

## 8. 测试策略

- **单元测试**：每个 extractor 喂一份固定 HTML fixture，断言 `Article.title / author / 正文长度`
- **集成测试**：跑 `pipeline.run(url)`，断言生成文件存在、front matter 合法 YAML
- **不测网络**：fixture 都离线，CI 不依赖外部站点
