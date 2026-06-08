from dataclasses import dataclass, field
from io import BytesIO
import resvg_py
from pathlib import Path
from model import Platform
from PIL import Image, ImageDraw
from model import RESOURCE_DIR, PROJECT_ROOT
import numpy as np
import time

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


@dataclass
class ResourcesLoader:
    images: dict[Path, Image.Image] = field(default_factory=dict)
    svgs: dict[tuple[Path, int | None, int | None, str], Image.Image] = field(default_factory=dict)

    def empty(self) -> Image.Image:
        return Image.new("RGBA", (1, 1))

    def load_image_or_empty(self, path: str | Path | None) -> Image.Image:
        if path is None:
            return self.empty()

        return self.load_image(path)

    def load_image(self, path: str | Path) -> Image.Image:
        path = self.resolve_path(path)

        if path not in self.images:
            self.images[path] = Image.open(path).convert("RGBA")

        return self.images[path].copy()

    def load_svg(
        self,
        path: str | Path,
        color: str = "#FFFFFF",
        height: int | None = None,
        width: int | None = None,
    ) -> Image.Image:
        path = self.resolve_path(path)
        cache_key = (path, height, width, color)

        if cache_key not in self.svgs:
            # Load and recolor SVG text
            svg_text = path.read_text(encoding="utf-8")
            svg_text = svg_text.replace('fill="white"', f'fill="{color}"')
            svg_text = svg_text.replace("fill:white", f"fill:{color}")

            # Render SVG to PNG bytes
            png_bytes = resvg_py.svg_to_bytes(
                svg_string=svg_text,
                height=height,
                width=width,
            )

            if png_bytes is None:
                raise RuntimeError(f"Could not render SVG: {path}")

            # Cache rendered image
            self.svgs[cache_key] = Image.open(BytesIO(png_bytes)).convert("RGBA")

        return self.svgs[cache_key].copy()

    def load_platform_icon(
        self,
        platform: Platform,
        color: str = "#FFFFFF",
        max_height: int | None = None,
        max_width: int | None = None,
        circle_fill_color: str | tuple[int, int, int, int] | None = None,
        circle_stroke_color: str | tuple[int, int, int, int] | None = None,
        circle_stroke_width: int = 8,
        circle_padding: int = 20
    ) -> Image.Image:
        filename_by_platform = {
            Platform.TWITCH: "TW.svg",
            Platform.YOUTUBE: "YT.svg",
        }

        if max_height is None or max_width is None:
            height = max_height
            width = max_width
        elif platform == Platform.TWITCH:
            height = max_height
            width = None
        else:
            height = None
            width = max_width

        icon = self.load_svg(
            RESOURCE_DIR / "icons" / filename_by_platform[platform],
            color=color,
            height=height,
            width=width,
        )

        if circle_fill_color is not None or circle_stroke_color is not None:
            size = max(height or 0, width or 0)
            # Create circle background
            circle_size = size + 2 * circle_padding + circle_stroke_width

            circle = Image.new("RGBA", (circle_size, circle_size))

            draw = ImageDraw.Draw(circle)

            draw.ellipse(
                (
                    circle_stroke_width // 2,
                    circle_stroke_width // 2,
                    circle_size - circle_stroke_width // 2,
                    circle_size - circle_stroke_width // 2,
                ),
                fill=circle_fill_color,
                outline=circle_stroke_color,
                width=circle_stroke_width,
            )

            # Center icon on circle
            pos = self.offset_to_center(icon, circle)

            if platform == Platform.TWITCH:
                pos = (
                    pos[0],
                    pos[1] + size//10
                )

            circle.alpha_composite(icon, pos)

            icon = circle

        return icon

    def offset_to_center_of_mass(
        self,
        source: Image.Image,
        target: Image.Image,
    ) -> tuple[int, int]:
        t_c = self.get_center_of_mass(target)
        s_c = self.get_center_of_mass(source)

        return (t_c[0] - s_c[0], t_c[1] - s_c[1])

    def offset_to_center(
        self,
        source: Image.Image,
        target: Image.Image,
    ) -> tuple[int, int]:
        t_c = self.get_center(target)
        s_c = self.get_center(source)

        return (t_c[0] - s_c[0], t_c[1] - s_c[1])

    def concat_imgs(self, imgs: list[Image.Image], spacing: int = 0) -> Image.Image:
        width = sum(img.width + spacing for img in imgs) - spacing
        height = max(img.height for img in imgs)

        result = Image.new("RGBA", (width, height))

        # Paste each one under the other
        current_x = 0
        for img in imgs:
            result.alpha_composite(img, (current_x, height//2 - img.height//2))
            current_x += img.width + spacing

        return result

    def pack_imgs(self, imgs: list[Image.Image], spacing: int = 0) -> Image.Image:
        height = sum(img.height + spacing for img in imgs) - spacing
        width = max(img.width for img in imgs)

        result = Image.new("RGBA", (width, height))

        # Paste each one under the other
        current_y = 0
        for img in imgs:
            result.alpha_composite(img, (width//2 - img.width//2, current_y))
            current_y += img.height + spacing

        return result

    def get_center(self, img: Image.Image) -> tuple[int, int]:
        bbox = img.getbbox()
        if bbox is None:
            return 0, 0

        left, top, right, bottom = bbox

        return (
            (left + right) // 2,
            (top + bottom) // 2,
        )

    
    def get_center_of_mass(self, img: Image.Image):
        alpha = np.asarray(img.getchannel("A"), dtype=np.float32)

        total = alpha.sum()

        if total == 0:
            return (0, 0)

        y, x = np.indices(alpha.shape)

        cx = (x * alpha).sum() / total
        cy = (y * alpha).sum() / total

        return round(cx), round(cy)

    def resolve_path(self, path: str | Path) -> Path:
        path = Path(path)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path
