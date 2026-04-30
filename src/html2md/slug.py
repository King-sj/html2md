from slugify import slugify


def make_slug(title: str, max_length: int = 60) -> str:
    s = slugify(title, max_length=max_length, word_boundary=True, separator="-")
    return s or "untitled"
