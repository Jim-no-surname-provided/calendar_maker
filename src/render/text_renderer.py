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

    glow_color: str | None = None
    glow_radius: int = 0

    upper_case: bool = True


class TextRenderer:
    def render(self, text: str, style: TextStyle) -> Image.Image:
        if text == "":
            return Image.new("RGBA", (1, 1))

        return self.svg2img(self.str2svg(text, style), style)

    def str2svg(self, text: str, style: TextStyle) -> Drawing:
        if style.upper_case:
            text = text.upper()

        font_family: str = Path(style.font_path).stem
        dwg = Drawing()

        insert = (
            style.stroke_width + style.glow_radius * 3,
            style.font_size + style.glow_radius * 3,
        )

        self.add_glow(dwg, text, insert, style, font_family)
        self.add_stroke(dwg, text, insert, style, font_family)

        return dwg

    def add_stroke(
        self,
        dwg: Drawing,
        text: str,
        insert: tuple[int, int],
        style: TextStyle,
        font_family: str
    ) -> None:
        if style.stroke_color is not None and style.stroke_width > 0:
            dwg.add(
                dwg.text(
                    text,
                    insert=insert,
                    fill="none",
                    stroke=style.stroke_color,
                    stroke_width=style.stroke_width,
                    font_size=style.font_size,
                    font_family=font_family,
                )
            )

        # Draw fill on top
        dwg.add(
            dwg.text(
                text,
                insert=insert,
                fill=style.fill_color,
                font_size=style.font_size,
                font_family=font_family,
            )
        )

    def add_glow(
        self,
        dwg: Drawing,
        text: str,
        insert: tuple[int, int],
        style: TextStyle,
        font_family: str
    ) -> None:
        if style.glow_color is None or style.glow_radius <= 0:
            return

        # Define glow filter
        glow_filter = dwg.defs.add(
            dwg.filter(
                id="glow",
                x="-100%",
                y="-100%",
                width="300%",
                height="300%",
            )
        )

        glow_filter.feGaussianBlur(
            in_="SourceAlpha",
            stdDeviation=style.glow_radius,
            result="blur",
        )

        glow_filter.feComponentTransfer(
            in_="blur",
            result="strong_blur",
        ).feFuncA(
            type_="linear",
            slope=3,
        )

        glow_filter.feFlood(
            flood_color=style.glow_color,
            result="glow_color",
        )

        glow_filter.feComposite(
            in_="glow_color",
            in2="strong_blur",
            operator="in",
            result="glow",
        )

        glow_filter.feMerge(
            ["glow"]
        )

        # Draw glow layer behind stroke and fill
        glow_text = dwg.text(
            text,
            insert=insert,
            fill=style.fill_color,
            font_size=style.font_size,
            font_family=font_family,
        )

        glow_text.attribs["filter"] = "url(#glow)"
        dwg.add(glow_text)

    def svg2img(self, svg: Drawing, style: TextStyle) -> Image.Image:
        # Rasterize SVG
        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg.tostring(),
            font_files=[str(style.font_path)]
        )

        # If None, empty
        if png_bytes is None:
            return Image.new("RGBA", (1, 1))

        img = Image.open(BytesIO(png_bytes)).convert("RGBA")

        # Define new size
        width = img.width + style.stroke_width * 2 + style.glow_radius * 3
        height = img.height + style.stroke_width * 2 + style.glow_radius * 3
        svg.viewbox(width=width, height=height)

        # Render with the correct size
        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg.tostring(),
            font_files=[str(style.font_path)]
        )

        # Convert PNG bytes to Pillow image
        img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        return img.crop(img.getbbox())
