from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from svgwrite import Drawing
import resvg_py
from io import BytesIO
from model import RESOURCE_DIR


@dataclass
class TextStyle:
    font_size: int
    font_path: str | Path = RESOURCE_DIR / "Choripan.otf"
    fill_color: str = "#FFFFFF"

    stroke_color: str | None = None
    stroke_width: int = 0

    shadow_color: str | None = None
    shadow_blur: int = 0
    shadow_offset: tuple[int, int] = (0, 0)

    glow_color: str | None = None
    glow_radius: int = 0

    upper_case: bool = True


class TextRenderer:
    def render(self, text: str, style: TextStyle) -> Image.Image:
        if text == "":
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        return self.svg2img(self.str2svg(text, style), style)

    def str2svg(self, text: str, style: TextStyle) -> Drawing:
        if style.upper_case:
            text = text.upper()

        font_family: str = Path(style.font_path).stem
        dwg = Drawing()

        # Draw stroke behind the fill
        if style.stroke_color is not None and style.stroke_width > 0:
            dwg.add(
                dwg.text(
                    text,
                    insert=(style.stroke_width, style.font_size),
                    fill="none",
                    stroke=style.stroke_color,
                    stroke_width=style.stroke_width,
                    font_size=style.font_size,
                    font_family=font_family,
                )
            )

        # # Draw fill on top
        dwg.add(
            dwg.text(
                text,
                insert=(style.stroke_width, style.font_size),
                fill=style.fill_color,
                font_size=style.font_size,
                font_family=font_family,
            )
        )

        return dwg

    def svg2img(self, svg: Drawing, style: TextStyle) -> Image.Image:
        # Rasterize SVG
        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg.tostring(),
            font_files=[str(style.font_path)]
        )

        # If None, empty
        if png_bytes is None:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        img = Image.open(BytesIO(png_bytes)).convert("RGBA")

        # Define new size
        width = img.width + style.stroke_width
        height = img.height
        svg.viewbox(width=width, height=height)

        # Render with the correct size
        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg.tostring(),
            font_files=[str(style.font_path)]
        )

        # Convert PNG bytes to Pillow image
        img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        return img.crop(img.getbbox())