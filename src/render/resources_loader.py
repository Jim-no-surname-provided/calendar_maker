from dataclasses import dataclass, field
from io import BytesIO
import cairosvg
from pathlib import Path
from model import Platform
from PIL import Image, ImageFont
from PIL.ImageFont import FreeTypeFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


@dataclass
class ResourcesLoader:
    images: dict[Path, Image.Image] = field(default_factory=dict)
    svgs: dict[tuple[Path, int, int, str], Image.Image] = field(default_factory=dict)

    def load_image_or_empty(self, path: str | Path | None) -> Image.Image:
        if path is None:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        return self.load_image(path)

    def load_image(self, path: str | Path) -> Image.Image:
        path = self.resolve_path(path)

        if path not in self.images:
            self.images[path] = Image.open(path).convert("RGBA")

        return self.images[path].copy()

    def load_svg(
        self,
        path: str | Path,
        width: int,
        height: int,
        color: str = "#FFFFFF",
    ) -> Image.Image:
        path = self.resolve_path(path)
        cache_key = (path, width, height, color)

        if cache_key not in self.svgs:
            svg_text = path.read_text(encoding="utf-8")
            svg_text = svg_text.replace('fill="white"', f'fill="{color}"')
            svg_text = svg_text.replace("fill:white", f"fill:{color}")

            png_bytes = cairosvg.svg2png(
                bytestring=svg_text.encode("utf-8"),
                output_width=width,
                output_height=height,
            )

            if png_bytes is None:
                raise RuntimeError(f"Could not render SVG: {path}")

            self.svgs[cache_key] = Image.open(BytesIO(png_bytes)).convert("RGBA")

        return self.svgs[cache_key].copy()

    def load_platform_icon(
        self,
        platform: Platform,
        width: int,
        height: int,
        color: str = "#FFFFFF",
    ) -> Image.Image:
        filename_by_platform = {
            Platform.TWITCH: "TW.svg",
            Platform.YOUTUBE: "YT.svg",
        }

        return self.load_svg(
            RESOURCE_DIR / "icons" / filename_by_platform[platform],
            width,
            height,
            color,
        )

    def resolve_path(self, path: str | Path) -> Path:
        path = Path(path)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path
