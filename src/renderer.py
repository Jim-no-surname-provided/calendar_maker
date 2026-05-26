from dataclasses import dataclass, field
from PIL import Image
from model import CalendarModel


@dataclass
class RenderResources:
    images: dict[str, Image.Image] = field(default_factory=dict)

    def load_image(self, path: str) -> Image.Image:
        if path not in self.images:
            self.images[path] = Image.open(path).convert("RGBA")

        return self.images[path].copy()


CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


def render_calendar(model: CalendarModel, resources: RenderResources) -> Image.Image:
    return resources.load_image(r"resources\FONDO\BG.PNG")
