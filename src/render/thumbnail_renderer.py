from PIL import Image

from model import ThumbnailModel
from render.resources_loader import ResourcesLoader


class ThumbnailRenderer():
    def __init__(self, image_model: ThumbnailModel, resources: ResourcesLoader) -> None:
        self.model: ThumbnailModel = image_model
        self.resources = resources

    def get_cropped_image(self) -> Image.Image:
        img = self.resources.load_image_or_empty(self.model.path)
        return img.crop(self.crop_box())

    def crop_box(self) -> tuple[int, int, int, int]:
        img = self.resources.load_image_or_empty(self.model.path)

        crop_left = self.model.crop_left * img.width
        crop_top = self.model.crop_top * img.height
        crop_right = self.model.crop_right * img.width
        crop_bottom = self.model.crop_bottom * img.height

        return (
            round(crop_left),
            round(crop_top),
            round(crop_right),
            round(crop_bottom),
        )

    def render_preview(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """
        Render a preview of the thumbnail with the selected crop area highlighted.

        The image is scaled to fit within the given dimensions. Areas outside
        the selected crop rectangle are darkened with a translucent overlay.
        """
        # load
        result = self.resources.load_image_or_empty(self.model.path)

        # make gray overlay
        overlay = Image.new(
            "RGBA",
            result.size,
            (0, 0, 0, 200),
        )

        # carve out crop area
        overlay.paste(
            (0, 0, 0, 0),
            self.crop_box(),
        )

        # paste and resize
        result.alpha_composite(overlay)
        result.thumbnail((width, height))

        return result
