import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from model import CalendarModel, WeekDay


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Calendario VTuber")
        self.root.geometry("1200x800")

        self.model = CalendarModel()

        self.create_layout()

    def create_layout(self):
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)

        # Make top bar
        self.make_top_bar()

        # Make resizable main area
        self.main_area = tk.PanedWindow(
            self.root,
            orient="horizontal",
            sashwidth=6,
            sashrelief="flat",
            bg="#1e1e1e",
            bd=0,
        )
        self.main_area.grid(row=1, column=0, sticky="nsew")

        # Make left panel
        self.make_left_panel()
        # Make preview frame
        self.make_preview_frame()

    def make_preview_frame(self):
        self.preview_frame = ctk.CTkFrame(
            self.main_area,
            corner_radius=0,
        )
        # Configure preview frame grid
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        # Add panel to resizable area
        self.main_area.add(self.preview_frame, minsize=400)

        # Make preview canvas
        self.preview_canvas = tk.Canvas(
            self.preview_frame,
            bg="#1e1e1e",
            highlightthickness=0,
        )
        self.preview_canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        # Make preview text
        self.preview_canvas.create_text(
            400,
            300,
            text="Vista previa",
            fill="white",
            font=("Arial", 24),
        )

    def make_top_bar(self):
        self.top_bar = ctk.CTkFrame(
            self.root,
            height=44,
            corner_radius=0,
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        # Make file button
        self.file_button = ctk.CTkButton(
            self.top_bar,
            text="Archivo",
            width=90,
        )
        self.file_button.pack(side="left", padx=(12, 6), pady=8)

        # Make edit button
        self.edit_button = ctk.CTkButton(
            self.top_bar,
            text="Editar",
            width=90,
        )
        self.edit_button.pack(side="left", padx=6, pady=8)

    def make_left_panel(self):
        self.left_panel = ctk.CTkFrame(
            self.main_area,
        )

        # Add panel to resizable area
        self.main_area.add(self.left_panel, minsize=420, width=620)

        # Configure left panel grid
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(0, weight=1)

        # Make scrollable content area
        self.left_content = ctk.CTkScrollableFrame(
            self.left_panel,
            corner_radius=0,
        )
        self.left_content.grid(row=0, column=0, sticky="nsew")

        # Make header section
        self.make_header_section()

        # Make day sections
        for day in WeekDay:
            self.make_day_section(day)

    def make_header_section(self):
        # Make header section frame
        self.header_section = ctk.CTkFrame(self.left_content)
        self.header_section.pack(fill="x", padx=12, pady=(12, 8))

        # Make date range variable
        self.date_range_var = ctk.StringVar(value=self.model.date_range)
        self.date_range_var.trace_add("write", self.on_date_range_changed)

        # Make date range row
        self.date_range_row = ctk.CTkFrame(self.header_section, fg_color="transparent")
        self.date_range_row.pack(fill="x", padx=12, pady=(12, 6))

        # Make date range label
        self.date_range_label = ctk.CTkLabel(
            self.date_range_row,
            text="Fecha",
            width=80,
            anchor="w",
        )
        self.date_range_label.pack(side="left")

        # Make date range entry
        self.date_range_entry = ctk.CTkEntry(
            self.date_range_row,
            textvariable=self.date_range_var,
            placeholder_text="Ej. 12 mayo - 18 mayo",
        )
        self.date_range_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Make fanart label
        self.fanart_label = ctk.CTkLabel(
            self.header_section,
            text="Fanart",
            anchor="w",
        )
        self.fanart_label.pack(fill="x", padx=12, pady=(12, 6))

        # Make fanart artist variable
        self.fanart_artist_var = ctk.StringVar(value=self.model.fanart_artist)
        self.fanart_artist_var.trace_add("write", self.on_fanart_artist_changed)

        # Make fanart artist overlay
        self.fanart_artist_overlay = ctk.CTkFrame(
            self.header_section,
            fg_color="transparent",
        )

        # Make fanart preview
        self.fanart_preview = ctk.CTkFrame(
            self.header_section,
            height=160,
            corner_radius=8,
        )
        self.fanart_preview.pack(fill="x", padx=12, pady=(0, 8))
        self.fanart_preview.pack_propagate(False)

        # Make fanart artist entry
        self.fanart_artist_entry = ctk.CTkEntry(
            self.fanart_preview,
            textvariable=self.fanart_artist_var,
            placeholder_text="Nombre del artista",
            width=100,
        )
        self.fanart_artist_entry.place(
            relx=1.0,
            y=12,
            x=-12,
            anchor="ne",
        )

        # Make fanart preview image label
        self.fanart_preview_image = ctk.CTkLabel(
            self.fanart_preview,
            text="Sin imagen seleccionada",
        )
        self.fanart_preview_image.place(relx=0.5, rely=0.5, anchor="center")

        # Make fanart select button
        self.fanart_select_button = ctk.CTkButton(
            self.header_section,
            text="Seleccionar imagen",
            command=self.on_select_fanart_image,
        )
        self.fanart_select_button.pack(fill="x", padx=12, pady=(0, 12))

    def on_date_range_changed(self, *_):
        self.model.date_range = self.date_range_var.get()
        self.on_model_changed()

    def on_fanart_artist_changed(self, *_):
        self.model.fanart_artist = self.fanart_artist_var.get()
        self.on_model_changed()

    def on_select_fanart_image(self):
        image_path = filedialog.askopenfilename(
            title="Seleccionar imagen de fanart",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not image_path:
            return

        self.model.fanart_image_path = image_path
        self.update_fanart_preview(image_path)
        self.on_model_changed()

    def update_fanart_preview(self, image_path: str):
        image = Image.open(image_path)

        max_width = 220
        max_height = 130

        image.thumbnail((max_width, max_height))

        preview_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size,
        )

        self.fanart_preview_ctk_image = preview_image

        self.fanart_preview_image.configure(
            image=self.fanart_preview_ctk_image,
            text="",
        )

        self.fanart_artist_entry.lift()


    def make_day_section(self, day: WeekDay):
        pass

    def on_model_changed(self):
        pass