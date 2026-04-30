from pathlib import Path
from typing import Annotated

import typer

from . import config as cfg_mod
from . import pipeline

app = typer.Typer(add_completion=False, help="Convert a web article URL to Markdown.")


@app.command()
def convert(
    url: Annotated[str, typer.Argument(help="文章 URL")],
    out: Annotated[Path | None, typer.Option("-o", "--out", help="输出目录")] = None,
    name: Annotated[str | None, typer.Option("-n", "--name", help="文件名（不含 .md，默认从标题生成 slug）")] = None,
    category: Annotated[str | None, typer.Option("-c", "--category", help="覆盖默认分类")] = None,
    tags: Annotated[list[str] | None, typer.Option("-t", "--tag", help="额外标签，可多次使用")] = None,
    no_download_images: Annotated[bool, typer.Option("--no-download-images", help="不下载图片，保留原 URL")] = False,
    no_front_matter: Annotated[bool, typer.Option("--no-front-matter", help="不生成 front matter")] = False,
) -> None:
    config = cfg_mod.load()
    result = pipeline.run(
        url,
        config=config,
        out_dir=out,
        name=name,
        download_images=False if no_download_images else None,
        write_front_matter=not no_front_matter,
        extra_tags=tags,
        category=category,
    )
    typer.echo(f"site:   {result.site}")
    typer.echo(f"title:  {result.title}")
    typer.echo(f"md:     {result.md_path}")
    if result.asset_dir:
        typer.echo(f"assets: {result.asset_dir}")


if __name__ == "__main__":
    app()
