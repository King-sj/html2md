from datetime import date

import yaml

from .models import Article


def render(article: Article, *, default_category: str = "转载", extra_tags: list[str] | None = None) -> str:
    publish = article.publish_date or date.today()

    fm: dict = {
        "title": article.title,
        # 占位字符串，最后再替换为无引号的日期标量
        "date": "__DATE_PLACEHOLDER__",
        "category": [default_category],
    }
    tags = list(article.tags)
    if extra_tags:
        for t in extra_tags:
            if t not in tags:
                tags.append(t)
    if tags:
        fm["tag"] = tags
    if article.author:
        fm["author"] = article.author
    if article.description:
        fm["description"] = article.description
    fm["original_url"] = article.url

    body = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    body = body.replace("date: __DATE_PLACEHOLDER__", f"date: {publish.isoformat()}")
    return f"---\n{body}\n---\n\n"
