from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from . import converter, extractors, frontmatter, images
from .config import Config
from .fetcher import DEFAULT_UA, fetch
from .slug import make_slug


@dataclass
class RunResult:
    md_path: Path
    asset_dir: Path | None
    title: str
    site: str


def run(
    url: str,
    *,
    config: Config,
    out_dir: Path | None = None,
    name: str | None = None,
    download_images: bool | None = None,
    write_front_matter: bool = True,
    extra_tags: list[str] | None = None,
    category: str | None = None,
) -> RunResult:
    out = out_dir or config.output_dir
    out.mkdir(parents=True, exist_ok=True)

    ua = config.user_agent or DEFAULT_UA
    html, final_url = fetch(url, timeout=config.timeout, user_agent=ua)
    soup = BeautifulSoup(html, "lxml")

    extractor = extractors.pick(final_url)
    article = extractor.extract(soup, final_url)

    slug = name or make_slug(article.title)

    md_body = converter.to_markdown(article.content_root)

    do_download = config.download_images if download_images is None else download_images
    asset_dir: Path | None = None
    if do_download:
        asset_root = out / config.image_dir
        md_body = images.localize(
            md_body,
            asset_root=asset_root,
            slug=slug,
            base_url=final_url,
            rel_prefix=f"./{config.image_dir}",
            user_agent=ua,
            timeout=config.timeout,
        )
        asset_dir = asset_root / slug

    if write_front_matter:
        head = frontmatter.render(
            article,
            default_category=category or config.default_category,
            extra_tags=extra_tags,
        )
        md_body = head + md_body

    md_path = out / f"{slug}.md"
    md_path.write_text(md_body, encoding="utf-8")

    return RunResult(md_path=md_path, asset_dir=asset_dir, title=article.title, site=article.site)
