import httpx

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def fetch(url: str, *, timeout: float = 30, user_agent: str = DEFAULT_UA) -> tuple[str, str]:
    """Return (html_text, final_url) following redirects."""
    headers = {"User-Agent": user_agent}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text, str(resp.url)
