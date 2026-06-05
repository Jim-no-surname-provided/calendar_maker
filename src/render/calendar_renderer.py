import customtkinter as ctk

from PIL import Image, ImageDraw
from pathlib import Path

from model import CalendarModel, WeekDay
from render.resources_loader import ResourcesLoader, RESOURCE_DIR
from render.day_renderer import DayRenderer
from render.text_renderer import TextRenderer, TextStyle


class CalendarRenderer:
    def __init__(self, model: CalendarModel, resources: ResourcesLoader):
        self.model = model
        self.resources = resources
        self.write = TextRenderer().render
        # self.fanart_renderer =
        self.day_renderers: dict[WeekDay, DayRenderer] = {
            day: DayRenderer(self.model.days[day], resources)
            for day in WeekDay
        }

    def render(self) -> Image.Image:
        image = self.background()

        image.alpha_composite(self.header())

        for week_day in WeekDay:
            day_img = self.day_renderers[week_day].render()
            image.alpha_composite(day_img)

        return image

    # Background

    def background(self) -> Image.Image:
        return self.resources.load_image(RESOURCE_DIR / "background.png")

    # Header
    def header(self) -> Image.Image:
        # Load elements
        fanart_txt_bg, fanart_artist = self.render_fanart_artist()
        fanart_frame = self.resources.load_image(RESOURCE_DIR / "frames" / "fanart.png")

        # Make result
        fanart = Image.new("RGBA", fanart_frame.size, (0, 0, 0, 0))

        # Composite
        fanart_pos = (938-fanart_txt_bg.width, 180)
        fanart.alpha_composite(fanart_txt_bg, fanart_pos)
        fanart.alpha_composite(fanart_frame)
        fanart.alpha_composite(fanart_artist, fanart_pos)

        # Write date
        fanart.alpha_composite(self.write(
            self.model.date_range,
            TextStyle(62,
                      stroke_color="#f5789f",
                      stroke_width=13)),
            dest=(15, 45)
        )

        # TODO
        return fanart

    def render_fanart_artist(self) -> tuple[Image.Image, Image.Image]:
        font = self.resources.load_font(28)

        # Calculate text size
        bbox = font.getbbox(
            self.model.fanart_artist,
            stroke_width=4,
        )

        width = int(bbox[2] - bbox[0])
        height = int(bbox[3] - bbox[1])

        # Make background and foreground for that size
        bg = self.render_stretched(RESOURCE_DIR / "fanart text background.png", width)
        txt = self.render_stretched(RESOURCE_DIR / "fanart text foreground.png", width)

        # Draw in a draw object
        draw = ImageDraw.Draw(txt)
        pad_right = 26
        pad_bottom = 8
        draw.text(
            (
                bg.width - width - bbox[0] - pad_right,
                (bg.height - height) // 2 - bbox[1] - pad_bottom,
            ),
            self.model.fanart_artist,
            font=font,
            fill="white",
            stroke_width=4,
            stroke_fill="#d57fc2",
        )

        return bg, txt

    def render_stretched(
        self,
        path: Path,
        stretched_width: int,
        left_width: int = 73,
        right_width: int = 18,
    ) -> Image.Image:
        # Load background
        img = self.resources.load_image(path)

        # Split into fixed and stretchable regions
        left = img.crop((0, 0, left_width, img.height))

        middle = img.crop((left_width, 0, img.width-right_width, img.height))

        right = img.crop((img.width-right_width, 0, img.width, img.height))

        # Create output image
        result = Image.new(
            "RGBA",
            (img.width + stretched_width, img.height),
            (0, 0, 0, 0),
        )

        # Paste fixed part
        result.alpha_composite(left)

        # Paste stretched middle
        stretched = middle.resize(
            (middle.width + stretched_width, img.height),
            Image.Resampling.NEAREST
        )
        result.alpha_composite(stretched, (left.width, 0))

        # Paste right side
        result.alpha_composite(right, (left.width + stretched.width, 0))

        return result


def get_ctk_color(widget, option="fg_color"):
    color = widget.cget(option)

    if isinstance(color, (tuple, list)):
        return (
            color[1]
            if ctk.get_appearance_mode() == "Dark"
            else color[0]
        )

    return color
