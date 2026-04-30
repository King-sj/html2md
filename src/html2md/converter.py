from bs4 import Tag
from markdownify import MarkdownConverter


class BlogConverter(MarkdownConverter):
    def convert_pre(self, el, text, parent_tags):
        code = el.find("code")
        lang = ""
        target = code if code else el
        cls = target.get("class") if isinstance(target, Tag) else None
        if cls:
            for c in cls:
                if c.startswith(("language-", "lang-")):
                    lang = c.split("-", 1)[1]
                    break
        body = (code or el).get_text()
        return f"\n```{lang}\n{body.rstrip()}\n```\n\n"

    def convert_img(self, el, text, parent_tags):
        src = (
            el.get("data-src")
            or el.get("data-original")
            or el.get("data-actualsrc")
            or el.get("src", "")
        )
        if not src:
            return ""
        alt = el.get("alt", "") or ""
        title = el.get("title")
        title_part = f' "{title}"' if title else ""
        return f"![{alt}]({src}{title_part})"


def to_markdown(root: Tag) -> str:
    conv = BlogConverter(heading_style="ATX", bullets="-", code_language="")
    return conv.convert_soup(root).strip() + "\n"
