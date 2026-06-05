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
    font_size: int
    font_family = "Choripan"
    # font_path: Path = RESOURCE_DIR / "Choripan.otf"

    fill_color: str = "#FFFFFF"

    stroke_color: str | None = None
    stroke_width: int = 0

    shadow_color: str | None = None
    shadow_blur: int = 0
    shadow_offset: tuple[int, int] = (0, 0)

    glow_color: str | None = None
    glow_radius: int = 0


class TextRenderer:
    def render(self, text: str, style: TextStyle) -> Image.Image:
        return self.svg2img(self.str2svg(text, style))

    def svg2img(self, svg_xml: str) -> Image.Image:
        png_bytes = cairosvg.svg2png(bytestring=svg_xml.encode("utf-8"))
        if png_bytes is None:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        image = Image.open(BytesIO(png_bytes)).convert("RGBA")
        return image

    def str2svg(self, text: str, style: TextStyle) -> str:
        dwg = svgwrite.Drawing(size=(500, 200))
        dwg.add(
            dwg.text(
                text,
                insert=(20, 100),
                fill=style.fill_color,
                font_size=style.font_size,
                font_family="Choripan",
            )
        )
        svg_xml = dwg.tostring()
        return svg_xml
