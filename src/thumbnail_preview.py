from tkinter import filedialog

from model import ThumbnailModel
import customtkinter as ctk
import tkinter as tk

from PIL import ImageTk, Image

from render.calendar_renderer import ResourcesLoader, get_ctk_color
from render.thumbnail_renderer import ThumbnailRenderer

from collections.abc import Callable


class ThumbnailPreview:
    def __init__(
        self,
        parent,
        image_model: ThumbnailModel,
        render_resources: ResourcesLoader,
        on_change: Callable[[], None],
        width: int = 220,
        height: int = 180,
    ):
        self.model: ThumbnailModel = image_model
        self.render_resources = render_resources
        self.renderer: ThumbnailRenderer = ThumbnailRenderer(self.model, self.render_resources)
        self.width = width
        self.height = height
        self.preview_image = None
        self.on_change = on_change
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.selection_rectangle = None

        # Make preview frame
        self.frame = ctk.CTkFrame(
            parent,
            height=height,
            corner_radius=8,
        )
        self.frame.pack(fill="x", padx=12, pady=(0, 8), ipadx=16, ipady=16)
        self.frame.pack_propagate(False)

        # Make preview canvas
        self.canvas = tk.Canvas(
            self.frame,
            highlightthickness=0,
            bg=get_ctk_color(self.frame),
        )

        # make canvas smaller than frame so frame color is visible as a border
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        # redraw on resize so centering stays correct
        # debounce resize updates
        self._resize_job = None

        def on_resize(event):
            if self._resize_job is not None:
                self.canvas.after_cancel(self._resize_job)
            self._resize_job = self.canvas.after(50, self.update)
        self.canvas.bind("<Configure>", on_resize)

        self.canvas.configure(cursor="hand2")
        self.canvas.bind("<Button-1>", self.on_crop_start)
        self.canvas.bind("<ButtonRelease-1>", self.on_crop_end)
        self.canvas.bind("<B1-Motion>", self.on_crop_drag)

        # Make select button
        self.select_button = ctk.CTkButton(
            parent,
            text="Seleccionar imagen",
            command=self.on_select,
        )
        self.select_button.pack(fill="x", padx=12, pady=(0, 8))

        self.update()

    def update(self):
        # Ensure canvas has real size
        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Fallback before layout is ready
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.width
            canvas_height = self.height

        MARGIN = 16

        preview_width = canvas_width - 2 * MARGIN
        preview_height = canvas_height - 2 * MARGIN

        image: Image.Image = self.renderer.render_preview(
            preview_width,
            preview_height,
        )

        # Clear canvas
        self.canvas.delete("all")

        if self.model.path is None:
            self.canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="Sin imagen seleccionada",
                fill="#aaaaaa",
                font=ctk.CTkFont(size=22),
                anchor="center",
            )
            return

        # Draw image centered using real canvas size
        self.canvas_image = ImageTk.PhotoImage(image)

        x = canvas_width // 2
        y = canvas_height // 2

        # Store image bounds
        self.image_left = x - image.width // 2
        self.image_top = y - image.height // 2

        self.image_right = self.image_left + image.width
        self.image_bottom = self.image_top + image.height

        self.canvas.create_image(
            x,
            y,
            image=self.canvas_image,
            anchor="center",
        )

    def clamp_to_image(self, x, y):
        x = max(self.image_left, min(x, self.image_right))
        y = max(self.image_top, min(y, self.image_bottom))

        return x, y

    def on_select(self):
        image_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not image_path:
            return

        self.canvas.configure(cursor="crosshair")

        self.model.path = image_path
        self.update()

    def winfo_children(self):
        return [self.frame, self.canvas, self.select_button]

    def on_crop_start(self, event):
        if self.model.path is None:
            self.on_select()
            return

        # Start crop
        self.crop_start_x = event.x
        self.crop_start_y = event.y

        # Reset previous rectangle
        if self.selection_rectangle is not None:
            self.canvas.delete(self.selection_rectangle)

        # Create new rectangle
        self.selection_rectangle = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="red",
            width=2,
        )

    def on_crop_drag(self, event):
        if self.selection_rectangle is None:
            return

        self.canvas.coords(
            self.selection_rectangle,
            self.crop_start_x,
            self.crop_start_y,
            event.x,
            event.y,
        )

    def on_crop_end(self, event):
        if self.selection_rectangle is None:
            return

        # Clamp start/end to image
        start_x, start_y = self.clamp_to_image(
            self.crop_start_x,
            self.crop_start_y,
        )

        end_x, end_y = self.clamp_to_image(
            event.x,
            event.y,
        )

        # Convert to image coordinates
        start_x -= self.image_left
        start_y -= self.image_top

        end_x -= self.image_left
        end_y -= self.image_top

        # Normalize
        image_width = self.image_right - self.image_left
        image_height = self.image_bottom - self.image_top

        # If invalid, select all
        if start_x == end_x or start_y == end_y:
            self.model.crop_left = 0.0
            self.model.crop_top = 0.0
            self.model.crop_right = 1.0
            self.model.crop_bottom = 1.0

        else:
            self.model.crop_left = min(start_x, end_x) / image_width
            self.model.crop_top = min(start_y, end_y) / image_height

            self.model.crop_right = max(start_x, end_x) / image_width
            self.model.crop_bottom = max(start_y, end_y) / image_height

        self.update()
        self.on_change()
