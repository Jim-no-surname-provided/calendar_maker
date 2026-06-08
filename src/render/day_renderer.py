import textwrap
from PIL import Image, ImageDraw, ImageChops
from model import DayModel
from pathlib import Path
from render.thumbnail_renderer import ThumbnailRenderer
from render.resources_loader import ResourcesLoader
from render.text_renderer import TextRenderer, TextStyle

from dataclasses import dataclass
from model import WeekDay
from render.resources_loader import RESOURCE_DIR


@dataclass(frozen=True)
class DayStyle:
    frame_path: Path
    mask_path: str
    color1: str
    color2: str


DAY_STYLES = {
    WeekDay.MONDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/monday.png",
        mask_path="masks/monday.png",
        color1="#b96cae",
        color2="#ffa7c4",
    ),
    WeekDay.TUESDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/tuesday.png",
        mask_path="masks/tuesday.png",
        color1="#705ba6",
        color2="#bca7ff",
    ),
    WeekDay.WEDNESDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/wednesday.png",
        mask_path="masks/wednesday.png",
        color1="#6565b7",
        color2="#a7afff",
    ),
    WeekDay.THURSDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/thursday.png",
        mask_path="masks/thursday.png",
        color1="#b96cae",
        color2="#ffa7c4",
    ),
    WeekDay.FRIDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/friday.png",
        mask_path="masks/friday.png",
        color1="#705ba6",
        color2="#c5a7ff",
    ),
    WeekDay.SATURDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/saturday.png",
        mask_path="masks/saturday.png",
        color1="#6565b7",
        color2="#a7b1ff",
    ),
    WeekDay.SUNDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/sunday.png",
        mask_path="masks/sunday.png",
        color1="#b96cae",
        color2="#ffa7c4",
    ),
}


class DayRenderer:
    def __init__(self, day_model: DayModel, resources: ResourcesLoader):
        self.model = day_model
        self.resources = resources
        self.thumbnail_renderer = ThumbnailRenderer(day_model.thumbnail, self.resources)
        self.write = TextRenderer().render

    def render(self) -> Image.Image | None:
        style = DAY_STYLES[self.model.day]
        result = self.render_frame(style.frame_path)
        mask = self.resources.load_image(self.model.thumbnail.mask_path)

        if self.model.is_rest_day:
            return self.rest_day(style, result, mask)

        #  Add thumbnail
        result.alpha_composite(self.thumbnail_renderer.render_masked())

        texts: list[Image.Image] = []

        texts += self.render_title()
        collabs = self.collabs()
        if collabs is not None:
            texts.append(collabs)

        subtitle = self.render_subtitle()
        if subtitle is not None:
            texts.append(subtitle)

        time = self.render_time()
        if time is not None:
            texts.append(time)

        if len(texts) == 0:
            return result

        # Render texts on top of each other
        packed_texts = self.resources.pack_imgs(texts, spacing=-4)
        packed_pos = self.resources.offset_to_center_of_mass(packed_texts, mask)

        # Render icon
        icon = self.render_platform_icon()
        icon_center = self.resources.get_center(icon)
        # image top left Corner-> middle -> first text top left corner
        icon_pos = (
            packed_pos[0] + packed_texts.width//2 - texts[0].width//2 - icon_center[0] - 8,
            packed_pos[1] - icon_center[1] + 8)

        # Compose icon first, then text
        result.alpha_composite(icon, icon_pos)
        result.alpha_composite(packed_texts, packed_pos)

        return result

    def rest_day(self, day_style: DayStyle, frame: Image.Image, mask: Image.Image) -> Image.Image:
        # Add white background
        frame.alpha_composite(mask)

        # make gray overlay
        overlay = Image.new(
            "RGBA",
            frame.size,
            (64, 0, 48, 143),
        )
        overlay = ImageChops.multiply(overlay, frame)
        frame.alpha_composite(overlay)

        txt = self.write(
            "descanso",
            TextStyle(
                font_size=100,
                stroke_width=24,
                stroke_color=day_style.color1,
                glow_color=day_style.color1,
                glow_radius=32,
            )
        )

        txt.save("test.png")

        frame.alpha_composite(txt, self.resources.offset_to_center(txt, mask))

        return frame

    def render_time(self) -> Image.Image | None:
        txt = self.model.time_text
        if txt == "":
            return

        color = DAY_STYLES[self.model.day].color1
        style = TextStyle(
            font_size=24,
            fill_color="#FFFFFF",
            stroke_color=color,
            stroke_width=8
        )
        img = self.write(txt, style)

        img = self.center_in_rounded_box(img, border_color=color)

        return img

    def render_platform_icon(self) -> Image.Image:
        # Load platform icon
        icon_size = 64

        icon = self.resources.load_platform_icon(
            self.model.platform,
            color="#FFFFFF",
            max_height=icon_size,
            max_width=icon_size,
            circle_fill_color=DAY_STYLES[self.model.day].color2,
            circle_stroke_color=DAY_STYLES[self.model.day].color1,
            circle_stroke_width=12
        )

        # Rotate final icon badge
        return icon.rotate(
            30,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

    def render_subtitle(self) -> Image.Image | None:
        if self.model.subtitle == "":
            return

        # Make subtitle
        title_style = TextStyle(
            font_size=32,
            stroke_color="#FFFFFF",
            fill_color=DAY_STYLES[self.model.day].color2,
            stroke_width=12,
        )

        return self.write(self.model.subtitle, title_style)

    def collabs(self) -> Image.Image | None:
        members = self.model.collab_members
        length = len(members)
        if length == 0:
            return

        imgs = []
        for i, m in enumerate(members):
            txt = m.name + ","
            if i == length-1:
                txt = "Y " + m.name
            elif i == length-2:
                txt = m.name

            img = self.write(
                txt, TextStyle(
                    fill_color=m.color,
                    font_size=32,
                    stroke_width=12,
                    stroke_color="#FFFFFF"
                ))
            imgs.append(img)

        return self.resources.concat_imgs(imgs, spacing=2)

    def render_title(self) -> list[Image.Image]:
        result = []

        if self.model.title == "":
            return result

        # Make title
        title_style = TextStyle(
            font_size=80,
            stroke_color=DAY_STYLES[self.model.day].color1,
            stroke_width=16,
        )

        wrapped_title = self.wrap_balanced(self.model.title, 14)
        for line in wrapped_title:
            result.append(self.write(line, title_style))

        return result

    def wrap_balanced(
        self,
        text: str,
        width: int,
    ) -> list[str]:
        # Get normal wrapped lines first
        lines = textwrap.wrap(
            text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )

        if len(lines) <= 1:
            return [text]

        # If it wrapped into two lines, try to balance them better
        words = text.split()

        best_lines = lines
        best_score = float("inf")

        for split_index in range(1, len(words)):
            candidate_lines = [
                " ".join(words[:split_index]),
                " ".join(words[split_index:]),
            ]

            if any(len(line) > width for line in candidate_lines):
                continue

            score = abs(
                len(candidate_lines[0])
                - len(candidate_lines[1])
            )

            if score < best_score:
                best_score = score
                best_lines = candidate_lines

        return best_lines

    def center_in_rounded_box(
        self,
        img: Image.Image,
        padding: int = 16,
        corner_radius: int = 24,
        border_color: str | tuple[int, int, int, int] = "#FFFFFF",
        border_width: int = 8,
        background_color: str | tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> Image.Image:
        # Make result canvas
        width = img.width + 2 * padding
        height = img.height + 2 * padding
        result = Image.new("RGBA", (width, height), background_color)

        # Draw rounded border only
        draw = ImageDraw.Draw(result)
        draw.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=corner_radius,
            outline=border_color,
            width=border_width,
        )

        # Center image inside border
        x = (width - img.width) // 2
        y = (height - img.height) // 2
        result.alpha_composite(img, (x, y))

        return result

    def render_frame(self, frame_path: Path) -> Image.Image:
        return Image.open(frame_path).convert("RGBA")
