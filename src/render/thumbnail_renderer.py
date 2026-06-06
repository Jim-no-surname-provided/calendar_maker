from PIL import Image, ImageChops

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

    def scale_to_cover(
        self,
        img: Image.Image,
        width: int,
        height: int,
    ) -> Image.Image:

        # Compute scale that fully covers target area
        scale = max(
            width / img.width,
            height / img.height,
        )

        new_width = round(img.width * scale)
        new_height = round(img.height * scale)

        # Resize image
        return img.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS,
        )

    def render_masked(self) -> Image.Image:
        # Load image and mask
        img = self.get_cropped_image()
        mask = self.resources.load_image(self.model.mask_path)

        # Get visible mask area
        mask_box = mask.getbbox()

        if mask_box is None:
            return Image.new("RGBA", mask.size, (0, 0, 0, 0))

        mask_left, mask_top, mask_right, mask_bottom = mask_box
        mask_width = mask_right - mask_left
        mask_height = mask_bottom - mask_top

        # Scale image to cover mask area
        img = self.scale_to_cover(
            img,
            mask_width,
            mask_height,
        )

        # Center image inside mask area
        img_x = mask_left + (mask_width - img.width) // 2
        img_y = mask_top + (mask_height - img.height) // 2

        # Place image in full-size transparent result
        result = Image.new("RGBA", mask.size, (0, 0, 0, 0))

        result.alpha_composite(
            img,
            (img_x, img_y),
        )

        # Multiply image alpha by mask alpha
        image_alpha = result.getchannel("A")
        mask_alpha = mask.getchannel("A")

        combined_alpha = ImageChops.multiply(
            image_alpha,
            mask_alpha,
        )


        result.putalpha(combined_alpha)

        return result