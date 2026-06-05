from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import svgwrite
import cairosvg
from io import BytesIO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCE_DIR = PROJECT_ROOT / "resources"


@dataclass
class TextStyle:
    height: int
    font_family: str = "Choripan"
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
        return self.svg2img(self.str2svg(text, style), style.height)

    # def svg2img(self, svg_xml: str) -> Image.Image:
    #     png_bytes = cairosvg.svg2png(bytestring=svg_xml.encode("utf-8"))
    #     if png_bytes is None:
    #         return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    #     image = Image.open(BytesIO(png_bytes)).convert("RGBA")
    #     return image

    def str2svg(self, text: str, style: TextStyle) -> str:
        if style.upper_case:
            text = text.upper()

        dwg = svgwrite.Drawing()
        dwg.add(
            dwg.text(
                text,
                insert=(20, 100),
                fill=style.fill_color,
                # Cannonical size, mostly irrelevant
                font_size=100,
                font_family="Choripan",
            )
        )
        svg_xml = dwg.tostring()
        return svg_xml

    def svg2img(self, svg_xml: str, height: int) -> Image.Image:
        # Rasterize SVG at the requested height
        png_bytes = cairosvg.svg2png(
            bytestring=svg_xml.encode("utf-8"),
            output_height=height,
        )

        # If None, empty
        if png_bytes is None:
            return Image.new("RGBA",(1, 1),(0, 0, 0, 0))

        # Convert PNG bytes to Pillow image
        return Image.open(BytesIO(png_bytes)).convert("RGBA")