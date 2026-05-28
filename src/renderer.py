from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

from model import CalendarModel, Platform


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


@dataclass
class RenderResources:
    images: dict[Path, Image.Image] = field(default_factory=dict)
    svgs: dict[tuple[Path, int, int], Image.Image] = field(default_factory=dict)

    def load_image(self, path: str | Path) -> Image.Image:
        path = self.resolve_path(path)

        if path not in self.images:
            self.images[path] = Image.open(path).convert("RGBA")

        return self.images[path].copy()

    def load_svg(self, path: str | Path, width: int, height: int) -> Image.Image:
        path = self.resolve_path(path)
        cache_key = (path, width, height)

        if cache_key not in self.svgs:
            png_bytes = cairosvg.svg2png(
                url=str(path),
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
    ) -> Image.Image:
        filename_by_platform = {
            Platform.TWITCH: "TW.svg",
            Platform.YOUTUBE: "YT.svg",
        }

        return self.load_svg(
            RESOURCE_DIR / "platform" / filename_by_platform[platform],
            width,
            height,
        )

    def resolve_path(self, path: str | Path) -> Path:
        path = Path(path)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path


def render_calendar(model: CalendarModel, resources: RenderResources) -> Image.Image:
    # TODO: Make this function
    return resources.load_image(RESOURCE_DIR / "FONDO" / "BG.PNG")
