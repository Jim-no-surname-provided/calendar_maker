import customtkinter as ctk

from PIL import Image
from pathlib import Path

from model import CalendarModel, WeekDay
from render.resources_loader import ResourcesLoader, RESOURCE_DIR, Platform
from render.day_renderer import DayRenderer
from render.thumbnail_renderer import ThumbnailRenderer
from render.text_renderer import TextRenderer, TextStyle


class CalendarRenderer:
    def __init__(self, model: CalendarModel, resources: ResourcesLoader):
        self.model = model
        self.resources = resources
        self.write = TextRenderer().render
        self.fanart_renderer = ThumbnailRenderer(self.model.fanart, self.resources)

        self.day_renderers: dict[WeekDay, DayRenderer] = {
            day: DayRenderer(self.model.days[day], resources)
            for day in WeekDay
        }

    def render(self) -> Image.Image:
        image = self.background()
        image.alpha_composite(self.header())

        for week_day in WeekDay:
            day_img = self.day_renderers[week_day].render()
            if day_img is not None:
                image.alpha_composite(day_img)

        footer = self.footer()
        y_margin = 30
        x = image.width//2 - footer.width//2
        y = image.height-footer.height - y_margin
        image.alpha_composite(footer, (x, y))

        stickers = self.resources.load_image(RESOURCE_DIR / "stickers.png")
        image.alpha_composite(stickers)

        return image

    def footer(self) -> Image.Image:
        icon_size = 48
        style = TextStyle(
            font_size=58,
            stroke_color="#f5789f",
            stroke_width=16,
        )

        tw = self.resources.load_platform_icon(
            Platform.TWITCH,
            color="#a7afff",
            max_height=icon_size,
            max_width=icon_size,
            circle_fill_color="#FFFFFF",
            circle_padding=10,
        )

        tw_txt = self.write("twitch.tv/pinklingvt", style)

        yt = self.resources.load_platform_icon(
            Platform.YOUTUBE,
            color="#f5789f",
            max_height=icon_size,
            max_width=icon_size,
            circle_fill_color="#FFFFFF",
            circle_padding=10,
        )

        yt_txt = self.write("youtube.com/@pinklingvt", style)

        return self.resources.concat_imgs([tw, tw_txt, yt, yt_txt], spacing=16)

    def background(self) -> Image.Image:
        return self.resources.load_image(RESOURCE_DIR / "background.png")

    def header(self) -> Image.Image:
        # Load layers
        fanart_frame = self.resources.load_image(RESOURCE_DIR / "frames" / "fanart.png")

        artist_text = self.write(
            self.model.fanart_artist,
            TextStyle(
                font_size=32,
                stroke_color="#d57fc2",
                stroke_width=4,
            ),
        )

        artist_bg = self.render_stretched(
            RESOURCE_DIR / "fanart text background.png",
            artist_text.width,
        )

        artist_fg = self.render_stretched(
            RESOURCE_DIR / "fanart text foreground.png",
            artist_text.width,
        )

        # Create result
        fanart = Image.new(
            "RGBA",
            fanart_frame.size,
        )

        # Composite artist label
        x_corner, y_corner = 938, 187
        xpad, ypad = 30, 7
        artist_frame_pos = (x_corner - artist_bg.width, y_corner)
        artist_txt_pos = (x_corner - artist_text.width - xpad, y_corner + ypad)
        fanart.alpha_composite(fanart_frame)
        fanart.alpha_composite(self.fanart_renderer.render_masked())
        fanart.alpha_composite(artist_bg, artist_frame_pos)
        fanart.alpha_composite(artist_text, artist_txt_pos)
        fanart.alpha_composite(artist_fg, artist_frame_pos,)

        # Write date
        date_text = self.write(
            self.model.date_range,
            TextStyle(
                font_size=80,
                stroke_color="#f5789f",
                stroke_width=24,
            ),
        )

        fanart.alpha_composite(
            date_text,
            dest=(15, 45),
        )

        return fanart

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
