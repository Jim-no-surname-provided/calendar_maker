from pathlib import Path

from PIL import Image

# Remove any frame pixel that overlaps a visible mask pixel
def clean_frames():
    frames_dir = Path("resources/frames")
    masks_dir = Path("resources/masks")
    output_dir = Path("resources/frames_cleaned")

    output_dir.mkdir(exist_ok=True)

    for frame_path in frames_dir.glob("*.png"):
        mask_path = masks_dir / frame_path.name

        if not mask_path.exists():
            print(f"Missing mask: {mask_path}")
            continue

        # Load images
        frame = Image.open(frame_path).convert("RGBA")
        mask = Image.open(mask_path).convert("RGBA")

        # Access pixels
        frame_pixels = frame.load()
        mask_pixels = mask.load()

        # Remove overlapping frame pixels
        for y in range(frame.height):
            for x in range(frame.width):
                if mask_pixels[x, y][3] != 0:
                    frame_pixels[x, y] = (0, 0, 0, 0)

        # Save result
        frame.save(output_dir / frame_path.name)

        print(f"Cleaned {frame_path.name}")


if __name__ == "__main__":
    clean_frames()
