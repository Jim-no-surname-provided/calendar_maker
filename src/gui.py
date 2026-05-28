import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageTk

from model import CalendarModel, CollabMember, DaySchedule, Platform, WeekDay
from renderer import RenderResources, render_calendar


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Calendario VTuber")
        self.root.geometry("1200x800")

        self.model = CalendarModel()
        self.day_image_labels = {}
        self.day_widgets = {}
        self.render_resources = RenderResources()
        self.day_preview_ctk_images = {}
        self.day_collab_rows = {}
        self.preview_canvas_image = None
        self.rendered_preview_image = None
        self.preview_update_job = None
        self.platform_ctk_images = {}

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

        # Redraw preview when canvas size changes
        self.preview_canvas.bind("<Configure>", self.on_preview_canvas_resized)

        # Render initial preview after layout is ready
        self.root.after_idle(self.on_model_changed)

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

    def labeled_row(
        self,
        parent,
        label_text: str,
        variable: ctk.StringVar,
        placeholder_text: str,
        padx=12,
        pady=(0, 12),
    ):
        # Make row
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=padx, pady=pady)

        # Make label
        label = ctk.CTkLabel(
            row,
            text=label_text,
            width=80,
            anchor="w",
        )
        label.pack(side="left")

        # Make entry
        entry = ctk.CTkEntry(
            row,
            textvariable=variable,
            placeholder_text=placeholder_text,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        return row, label, entry

    def make_header_section(self):
        # Make header section frame
        self.header_section = ctk.CTkFrame(self.left_content)
        self.header_section.pack(fill="x", padx=12, pady=(12, 8))

        # Make date range variable
        self.date_range_var = ctk.StringVar(value=self.model.date_range)
        self.date_range_var.trace_add("write", self.on_date_range_changed)

        # Make date range row
        self.date_range_row, self.date_range_label, self.date_range_entry = self.labeled_row(
            self.header_section,
            "Fecha",
            self.date_range_var,
            "Ej. 12 mayo - 18 mayo",
            pady=(12, 6),
        )

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
        day_schedule = self.get_day_schedule(day)

        # Make day section frame
        day_section = ctk.CTkFrame(self.left_content)
        day_section.pack(fill="x", padx=12, pady=8)

        day_widgets = []
        self.day_widgets[day] = day_widgets

        # Make day title
        self.make_day_title(day_section, day_schedule)

        # Make rest day checkbox
        self.make_rest_day_checkbox(day_section, day_schedule, day_widgets)

        # Make day image selector
        self.make_day_image_selector(day_section, day_schedule, day_widgets)

        # Make stream title row
        self.make_stream_title_row(day_section, day_schedule, day_widgets)

        # Make collab row
        self.make_collab_row(day_section, day_schedule, day_widgets)

        # Make time row
        self.make_time_row(day_section, day_schedule, day_widgets)

        # Make platform selector
        self.make_platform_selector(day_section, day_schedule, day_widgets)

    def make_day_title(self, parent, day_schedule: DaySchedule):
        # Make day title label
        day_title = ctk.CTkLabel(
            parent,
            text=day_schedule.day.value,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        day_title.pack(fill="x", padx=12, pady=(12, 4))

        # Make day title separator
        day_separator = ctk.CTkFrame(
            parent,
            height=2,
        )
        day_separator.pack(fill="x", padx=12, pady=(0, 12))

    def make_rest_day_checkbox(self, parent, day_schedule: DaySchedule, day_widgets):
        # Make rest day variable
        rest_day_var = ctk.BooleanVar(value=day_schedule.is_rest_day)

        # Make rest day checkbox
        rest_day_checkbox = ctk.CTkCheckBox(
            parent,
            text="Descanso",
            variable=rest_day_var,
            command=lambda: self.on_rest_day_changed(day_schedule, rest_day_var, day_widgets),
        )
        rest_day_checkbox.pack(anchor="w", padx=12, pady=(0, 12))

    def make_day_image_selector(self, parent, day_schedule: DaySchedule, day_widgets):

        # Make image selector frame
        image_selector = ctk.CTkFrame(parent, fg_color="transparent")
        image_selector.pack(fill="x", padx=12, pady=(0, 12))

        # Make image preview
        image_preview = ctk.CTkFrame(
            image_selector,
            height=140,
            corner_radius=8,
            fg_color=self.fanart_preview.cget("fg_color"),
        )
        image_preview.pack(fill="x", pady=(0, 8))
        image_preview.pack_propagate(False)

        # Make image preview label
        image_label = ctk.CTkLabel(
            image_preview,
            text="Sin imagen seleccionada",
        )
        image_label.place(relx=0.5, rely=0.5, anchor="center")
        self.day_image_labels[day_schedule.day] = image_label

        # Make select image button
        select_button = ctk.CTkButton(
            image_selector,
            text="Seleccionar imagen",
            command=lambda selected_day_schedule=day_schedule: self.on_select_day_image(selected_day_schedule),
        )
        select_button.pack(fill="x")

        day_widgets.append(image_selector)

        if day_schedule.image_path is not None:
            self.update_day_image_preview(day_schedule.day, day_schedule.image_path)

    def make_stream_title_row(self, parent, day_schedule: DaySchedule, day_widgets):
        # Make stream title variable
        stream_title_var = ctk.StringVar(value=day_schedule.title)
        stream_title_var.trace_add(
            "write",
            lambda *_: self.on_stream_title_changed(day_schedule, stream_title_var),
        )

        # Make stream title row
        stream_title_row, _, _ = self.labeled_row(
            parent,
            "Título",
            stream_title_var,
            "Título del stream",
        )

        day_widgets.append(stream_title_row)

    def make_collab_row(self, parent, day_schedule: DaySchedule, day_widgets):
        # Make collab section frame
        collab_section = ctk.CTkFrame(parent, fg_color="transparent")
        collab_section.pack(fill="x", padx=12, pady=(0, 12))
        day_widgets.append(collab_section)

        # Make collab header row
        collab_header_row = ctk.CTkFrame(collab_section, fg_color="transparent")
        collab_header_row.pack(fill="x", pady=(0, 8))

        # Make collab label
        collab_label = ctk.CTkLabel(
            collab_header_row,
            text="Collab",
            anchor="w",
        )
        collab_label.pack(side="left", fill="x", expand=True)

        # Make add collab button
        add_collab_button = ctk.CTkButton(
            collab_header_row,
            text="+",
            width=36,
            command=lambda: self.add_collab_member_row(day_schedule, collab_list),
        )
        add_collab_button.pack(side="right")

        # Make collab list frame
        collab_list = ctk.CTkFrame(
            collab_section,
            fg_color="transparent",
            height=0,
        )
        collab_list.pack(fill="x")
        collab_list.pack_propagate(False)
        self.day_collab_rows[day_schedule.day] = []

        # Add existing collab members
        for collab_member in day_schedule.collab_members:
            self.add_collab_member_row(day_schedule, collab_list, collab_member)

    def add_collab_member_row(
        self,
        day_schedule: DaySchedule,
        parent,
        collab_member: CollabMember | None = None,
    ):
        if collab_member is None:
            collab_member = CollabMember()

        parent.pack_propagate(True)

        # Make collab member variable
        name_var = ctk.StringVar(value=collab_member.name)

        # Make collab member row
        collab_member_row = ctk.CTkFrame(parent, fg_color="transparent")
        collab_member_row.pack(fill="x", pady=(0, 6))

        # Make collab member entry
        collab_member_entry = ctk.CTkEntry(
            collab_member_row,
            textvariable=name_var,
            placeholder_text="Nombre",
        )
        collab_member_entry.pack(side="left", fill="x", expand=True)

        # Make collab color button
        color_button = ctk.CTkButton(
            collab_member_row,
            text="",
            width=32,
            fg_color=collab_member.color,
            hover_color=collab_member.color,
            command=lambda: self.on_select_collab_color(color_button, collab_member),
        )
        color_button.pack(side="left", padx=(8, 8))

        # Make remove collab button
        remove_button = ctk.CTkButton(
            collab_member_row,
            text="-",
            width=36,
            command=lambda: self.remove_collab_member_row(day_schedule, collab_member_row),
        )
        remove_button.pack(side="left")

        name_var.trace_add(
            "write",
            lambda *_: self.on_collab_changed(day_schedule),
        )

        self.day_collab_rows[day_schedule.day].append(
            {
                "row": collab_member_row,
                "name_var": name_var,
                "color": collab_member.color,
            }
        )

        self.on_collab_changed(day_schedule)

    def remove_collab_member_row(self, day_schedule: DaySchedule, collab_member_row):
        rows = self.day_collab_rows[day_schedule.day]
        self.day_collab_rows[day_schedule.day] = [
            row_data for row_data in rows if row_data["row"] != collab_member_row
        ]

        collab_member_row.destroy()

        if not self.day_collab_rows[day_schedule.day]:
            collab_member_row.master.configure(height=0)
            collab_member_row.master.pack_propagate(False)

        self.on_collab_changed(day_schedule)

    def on_select_collab_color(self, color_button, collab_member: CollabMember):
        # TODO: Open color picker and update collab color
        pass

    def make_time_row(self, parent, day_schedule: DaySchedule, day_widgets):
        # Make time variable
        time_var = ctk.StringVar(value=day_schedule.time_text)
        time_var.trace_add(
            "write",
            lambda *_: self.on_time_changed(day_schedule, time_var),
        )

        # Make time row
        time_row, _, _ = self.labeled_row(
            parent,
            "Hora",
            time_var,
            "Ej. 19:00 CET",
        )

        day_widgets.append(time_row)

    def make_platform_selector(self, parent, day_schedule: DaySchedule, day_widgets):
        # Make platform variable
        platform_var = ctk.StringVar(value=day_schedule.platform.value)

        # Make platform row
        platform_row = ctk.CTkFrame(parent, fg_color="transparent")
        platform_row.pack(fill="x", padx=12, pady=(0, 12))

        # Make centered container
        platform_options = ctk.CTkFrame(
            platform_row,
            fg_color="transparent",
        )
        platform_options.pack()

        def make_platform_option(platform: Platform):
            # Make platform option frame
            option_frame = ctk.CTkFrame(platform_options, fg_color="transparent")

            # Make platform radio button
            radio_button = ctk.CTkRadioButton(
                option_frame,
                text="",
                width=20,
                radiobutton_width=16,
                radiobutton_height=16,
                variable=platform_var,
                value=platform.value,
                command=lambda: self.on_platform_changed(day_schedule, platform_var),
            )
            radio_button.pack(side="left")

            # Load platform icon
            icon_image = self.render_resources.load_platform_icon(
                platform,
                28,
                28,
            )

            # Convert platform icon to CTkImage
            icon = ctk.CTkImage(
                light_image=icon_image,
                dark_image=icon_image,
                size=(28, 28),
            )
            self.platform_ctk_images[(day_schedule.day, platform)] = icon

            # Make platform icon label
            icon_label = ctk.CTkLabel(
                option_frame,
                text="",
                image=icon,
            )
            icon_label.pack(side="left", padx=(4, 0))

            return option_frame

        # Make Twitch option
        twitch_option = make_platform_option(Platform.TWITCH)
        twitch_option.pack(side="left")

        # Make fixed spacing
        platform_spacing = ctk.CTkFrame(
            platform_options,
            width=16,
            height=1,
            fg_color="transparent",
        )
        platform_spacing.pack(side="left")
        platform_spacing.pack_propagate(False)

        # Make YouTube option
        youtube_option = make_platform_option(Platform.YOUTUBE)
        youtube_option.pack(side="left")

        day_widgets.append(platform_row)

    def on_rest_day_changed(self, day_schedule: DaySchedule, rest_day_var, day_widgets):
        day_schedule.is_rest_day = rest_day_var.get()

        state = "disabled" if day_schedule.is_rest_day else "normal"

        for widget in day_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                pass

        self.on_model_changed()

    def on_select_day_image(self, day_schedule: DaySchedule):
        # TODO: Add a way to crop and rotate

        image_path = filedialog.askopenfilename(
            title=f"Seleccionar imagen para {day_schedule.day.value}",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if not image_path:
            return

        day_schedule.image_path = image_path

        self.update_day_image_preview(day_schedule.day, image_path)
        self.on_model_changed()

    def update_day_image_preview(self, day: WeekDay, image_path: str):
        image = Image.open(image_path)

        max_width = 260
        max_height = 120

        image.thumbnail((max_width, max_height))

        preview_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size,
        )

        self.day_preview_ctk_images[day] = preview_image

        self.day_image_labels[day].configure(
            image=self.day_preview_ctk_images[day],
            text="",
        )

    def get_day_schedule(self, day: WeekDay) -> DaySchedule:
        if day not in self.model.days:
            self.model.days[day] = DaySchedule(day=day)

        return self.model.days[day]

    def on_stream_title_changed(self, day_schedule: DaySchedule, stream_title_var):
        day_schedule.title = stream_title_var.get()
        self.on_model_changed()

    def on_collab_changed(self, day_schedule: DaySchedule):
        collab_members = []

        for row_data in self.day_collab_rows[day_schedule.day]:
            name = row_data["name_var"].get().strip()

            if not name:
                continue

            collab_members.append(
                CollabMember(
                    name=name,
                    color=row_data["color"],
                )
            )

        day_schedule.collab_members = collab_members
        self.on_model_changed()

    def on_time_changed(self, day_schedule: DaySchedule, time_var):
        day_schedule.time_text = time_var.get()
        self.on_model_changed()

    def on_platform_changed(self, day_schedule: DaySchedule, platform_var):
        day_schedule.platform = Platform(platform_var.get())
        self.on_model_changed()

    def on_model_changed(self):
        self.schedule_preview_update()

    def schedule_preview_update(self):
        if self.preview_update_job is not None:
            self.root.after_cancel(self.preview_update_job)

        self.preview_update_job = self.root.after(
            120,
            self.render_preview,
        )

    def render_preview(self):
        self.preview_update_job = None
        self.rendered_preview_image = render_calendar(self.model, self.render_resources)
        self.update_preview_canvas()

    def on_preview_canvas_resized(self, event=None):
        self.update_preview_canvas()

    def update_preview_canvas(self):
        # Get canvas size
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        if self.rendered_preview_image is None:
            return

        # Make preview copy
        preview_image = self.rendered_preview_image.copy()

        # Fit image inside canvas
        preview_image.thumbnail((canvas_width, canvas_height))

        # Convert image for Tkinter
        self.preview_canvas_image = ImageTk.PhotoImage(preview_image)

        # Clear previous preview
        self.preview_canvas.delete("all")

        # Calculate centered position
        x = canvas_width // 2
        y = canvas_height // 2

        # Draw preview image
        self.preview_canvas.create_image(
            x,
            y,
            image=self.preview_canvas_image,
            anchor="center",
        )
