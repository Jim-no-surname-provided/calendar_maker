from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

from model import CalendarModel, ImageAsset, Platform

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


@dataclass
class RenderResources:
    images: dict[Path, Image.Image] = field(default_factory=dict)
    svgs: dict[tuple[Path, int, int, str], Image.Image] = field(default_factory=dict)

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
            RESOURCE_DIR / "platform" / filename_by_platform[platform],
            width,
            height,
            color,
        )

    def resolve_path(self, path: str | Path) -> Path:
        path = Path(path)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path


def render_calendar(model: CalendarModel, resources: RenderResources) -> Image.Image:
    # TODO: Make this function
    return resources.load_image(RESOURCE_DIR / "FONDO" / "BG.PNG")

def render_image_asset(
    image_asset: ImageAsset,
    resources: RenderResources,
    width: int,
    height: int,
) -> Image.Image:
    # Empty image
    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    if image_asset.path is None:
        return result
    
    # Load actual image
    image = resources.load_image(image_asset.path)
    image.thumbnail((width, height))

    # Center
    x = (width - image.width) // 2
    y = (height - image.height) // 2

    # Paste
    result.alpha_composite(image, (x, y))

    crop_left = image_asset.crop_left * image.width
    crop_top = image_asset.crop_top * image.height
    crop_right = image_asset.crop_right * image.width
    crop_bottom = image_asset.crop_bottom * image.height

    # Gray out image area
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 200))

    crop_box = (
        round(crop_left),
        round(crop_top),
        round(crop_right),
        round(crop_bottom),
    )

    # Paste selected crop area transparent
    overlay.paste((0, 0, 0, 0), crop_box)

    result.alpha_composite(overlay, (x, y))

    return result