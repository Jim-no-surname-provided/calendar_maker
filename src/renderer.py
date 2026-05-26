from PIL import Image, ImageDraw

from model import CalendarModel


CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


def render_calendar(model: CalendarModel) -> Image.Image:
    image = Image.open(r"resources\FONDO\BG.PNG")
    return image