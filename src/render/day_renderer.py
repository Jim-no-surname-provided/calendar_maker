import textwrap
from PIL import Image
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
    text_color: str


DAY_STYLES = {
    WeekDay.MONDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/monday.png",
        mask_path="masks/monday.png",
        text_color="#b96cae",
    ),
    WeekDay.TUESDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/tuesday.png",
        mask_path="masks/tuesday.png",
        text_color="#705ba6",
    ),
    WeekDay.WEDNESDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/wednesday.png",
        mask_path="masks/wednesday.png",
        text_color="#6565b7",
    ),
    WeekDay.THURSDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/thursday.png",
        mask_path="masks/thursday.png",
        text_color="#b96cae",
    ),
    WeekDay.FRIDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/friday.png",
        mask_path="masks/friday.png",
        text_color="#705ba6",
    ),
    WeekDay.SATURDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/saturday.png",
        mask_path="masks/saturday.png",
        text_color="#6565b7",
    ),
    WeekDay.SUNDAY: DayStyle(
        frame_path=RESOURCE_DIR / "frames/sunday.png",
        mask_path="masks/sunday.png",
        text_color="#b96cae",
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
        mask_center = self.get_center(mask)

        #  Add thumbnail
        result.alpha_composite(self.thumbnail_renderer.render_masked())

        texts: list[Image.Image] = []

        texts += self.render_title()
        collabs = self.collabs()
        if collabs is not None:
            texts.append(collabs)
        # TODO other texts

        if len(texts) == 0:
            return result

        texts[0].save("test.png")
        packed_texts = self.pack_imgs(texts, spacing=-8)
        center = self.get_center(packed_texts)

        result.alpha_composite(packed_texts, self.minus(mask_center, center))

        return result

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
                    font_size=48,
                    stroke_width=12,
                    stroke_color="#FFFFFF"
                ))
            imgs.append(img)

        return self.concat_imgs(imgs, spacing=8)

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

    def render_title(self) -> list[Image.Image]:
        result = []

        if self.model.title == "":
            return result

        # Make title
        title_style = TextStyle(
            font_size=80,
            stroke_color=DAY_STYLES[self.model.day].text_color,
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

    def minus(self, tuple1: tuple[int, int], tuple2: tuple[int, int]) -> tuple[int, int]:
        return (tuple1[0]-tuple2[0], tuple1[1]-tuple2[1])

    def get_center(self, img: Image.Image) -> tuple[int, int]:
        bbox = img.getbbox()
        if bbox is None:
            return 0, 0

        left, top, right, bottom = bbox

        return (
            (left + right) // 2,
            (top + bottom) // 2,
        )

    # Frame
    def render_frame(self, frame_path: Path) -> Image.Image:
        return Image.open(frame_path).convert("RGBA")
