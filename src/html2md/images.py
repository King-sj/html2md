import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx

from .fetcher import DEFAULT_UA

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_EXT_FALLBACK = ".png"


def _guess_ext(url: str, content_type: str | None) -> str:
    path = urlparse(url).path
    suffix = Path(unquote(path)).suffix.lower()
    if suffix and len(suffix) <= 5:
        return suffix
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    return _EXT_FALLBACK


def localize(
    md: str,
    *,
    asset_root: Path,
    slug: str,
    base_url: str,
    rel_prefix: str = "./assets",
    user_agent: str = DEFAULT_UA,
    max_workers: int = 8,
    timeout: float = 30,
) -> str:
    """Download all images referenced in `md`, rewrite to local relative paths."""
    matches = _IMG_RE.findall(md)
    if not matches:
        return md

    seen: dict[str, str] = {}
    ordered: list[str] = []
    for _, raw_url in matches:
        if raw_url in seen:
            continue
        seen[raw_url] = ""
        ordered.append(raw_url)

    target_dir = asset_root / slug
    target_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": user_agent, "Referer": base_url}

    def _download(idx: int, raw_url: str) -> tuple[str, str | None]:
        abs_url = urljoin(base_url, raw_url)
        try:
            with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
                resp = client.get(abs_url)
                resp.raise_for_status()
                ext = _guess_ext(abs_url, resp.headers.get("content-type"))
                fname = f"{idx:02d}{ext}"
                (target_dir / fname).write_bytes(resp.content)
                return raw_url, fname
        except Exception as exc:  # noqa: BLE001
            print(f"  ! image download failed: {abs_url} ({exc})")
            return raw_url, None

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_download, i, u) for i, u in enumerate(ordered, 1)]
        for fut in as_completed(futures):
            raw_url, fname = fut.result()
            if fname:
                seen[raw_url] = f"{rel_prefix}/{slug}/{fname}"

    def _replace(m: re.Match) -> str:
        alt, raw_url = m.group(1), m.group(2)
        new = seen.get(raw_url) or raw_url
        return f"![{alt}]({new})"

    return _IMG_RE.sub(_replace, md)
