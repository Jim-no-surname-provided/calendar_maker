from PIL import Image

from model import DayModel
from pathlib import Path
from render.thumbnail_renderer import ThumbnailRenderer
from render.resources_loader import ResourcesLoader

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
    def __init__(self, day_model: DayModel, resources : ResourcesLoader):
        self.model = day_model
        self.resources = resources
        self.image = ThumbnailRenderer(day_model.image, self.resources)

    def render(self) -> Image.Image:
        style = DAY_STYLES[self.model.day]
        # TODO write text from the model
        return self.render_frame(style.frame_path)

    # Frame
    def render_frame(self, frame_path: Path) -> Image.Image:
        return Image.open(frame_path).convert("RGBA")
