from dataclasses import dataclass
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"


@dataclass
class TextStyle:
    font_size: int
    font_path: Path = RESOURCE_DIR / "Choripan.otf"

    fill_color: str = "#FFFFFF"

    stroke_color: str | None = None
    stroke_width: int = 0

    shadow_color: str | None = None
    shadow_blur: int = 0
    shadow_offset: tuple[int, int] = (0, 0)

    glow_color: str | None = None
    glow_radius: int = 0


class TextRenderer:
    def render(
        self,
        text: str,
        style: TextStyle,
    ) -> Image.Image:
        raise NotImplementedError