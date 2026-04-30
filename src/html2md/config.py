import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".html2md" / "config.toml"


@dataclass
class Config:
    output_dir: Path = field(default_factory=lambda: Path.cwd())
    image_dir: str = "assets"
    download_images: bool = True
    default_category: str = "转载"
    user_agent: str | None = None
    timeout: float = 30.0


def load(path: Path = CONFIG_PATH) -> Config:
    cfg = Config()
    if not path.exists():
        return cfg
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if "output_dir" in data:
        cfg.output_dir = Path(data["output_dir"]).expanduser()
    for key in ("image_dir", "download_images", "default_category", "user_agent", "timeout"):
        if key in data:
            setattr(cfg, key, data[key])
    return cfg
