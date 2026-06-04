import tkinter as tk
from tkinter import colorchooser, filedialog

import customtkinter as ctk
from PIL import ImageTk

from model import CalendarModel, CollabMember, DaySchedule, Platform, WeekDay, ImageAsset
from renderer import RenderResources, render_calendar, render_image_asset, get_ctk_color

from collections.abc import Callable


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


NORMAL_PLATFORM_ICON_COLOR = "#FFFFFF"
DISABLED_PLATFORM_ICON_COLOR = "#5f5f5f"

REST_ENTRY_STYLE = {
    "fg_color": "#161616",
    "text_color": "#7a7a7a",
    "placeholder_text_color": "#4f4f4f",
    "border_color": "#2a2a2a",
}

REST_BUTTON_STYLE = {
    "fg_color": "#1b1b1b",
    "hover_color": "#1b1b1b",
    "text_color": "#cfcfcf",
}

REST_RADIO_STYLE = {
    "fg_color": "#404040",
    "hover_color": "#404040",
    "border_color": "#606060",
}


class ImagePreview:
    def __init__(
        self,
        parent,
        image_asset,
        render_resources: RenderResources,
        on_change: Callable[[], None],
        width: int = 220,
        height: int = 180,
    ):
        self.image_asset: ImageAsset = image_asset
        self.render_resources = render_resources
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

        image = render_image_asset(
            self.image_asset,
            self.render_resources,
            preview_width,
            preview_height,
        )

        # Clear canvas
        self.canvas.delete("all")

        if self.image_asset.path is None:
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

        self.image_asset.path = image_path
        self.update()

    def winfo_children(self):
        return [self.frame, self.canvas, self.select_button]

    def on_crop_start(self, event):
        if self.image_asset.path is None:
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

        self.image_asset.crop_left = min(start_x, end_x) / image_width
        self.image_asset.crop_top = min(start_y, end_y) / image_height

        self.image_asset.crop_right = max(start_x, end_x) / image_width
        self.image_asset.crop_bottom = max(start_y, end_y) / image_height

        self.update()
        self.on_change()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Calendario VTuber")
        self.root.geometry("1200x800")

        self.model = CalendarModel()
        self.render_resources = RenderResources()
        self.day_collab_rows = {}
        self.preview_canvas_image = None
        self.rendered_preview_image = None
        self.preview_update_job = None
        self.platform_ctk_images = {}
        self.platform_icon_labels = {}
        self.widget_visual_defaults = {}

        self.create_layout()

    def create_layout(self):
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)

        # Make top bar
        self.make_top_bar()

        # Make resizable main area
        main_area = tk.PanedWindow(
            self.root,
            orient="horizontal",
            sashwidth=6,
            sashrelief="flat",
            bg="#1e1e1e",
            bd=0,
        )
        main_area.grid(row=1, column=0, sticky="nsew")

        # Make left panel
        self.make_left_panel(main_area)
        # Make preview frame
        self.make_preview_frame(main_area)

    def make_preview_frame(self, main_area):
        preview_frame = ctk.CTkFrame(
            main_area,
            corner_radius=0,
        )

        # Add panel to resizable area
        main_area.add(preview_frame, minsize=400)

        # Make preview canvas
        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="#1e1e1e",
            highlightthickness=0,
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=12, pady=12)

        # Redraw preview when canvas size changes
        self.preview_canvas.bind("<Configure>", lambda _: self.on_model_changed())

        # Render initial preview after layout is ready
        self.root.after_idle(self.on_model_changed)

    def make_top_bar(self):
        top_bar = ctk.CTkFrame(
            self.root,
            height=44,
            corner_radius=0,
        )
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)

        # Make file button
        file_button = ctk.CTkButton(
            top_bar,
            text="Archivo",
            width=90,
        )
        file_button.pack(side="left", padx=(12, 6), pady=8)

        # Make edit button
        edit_button = ctk.CTkButton(
            top_bar,
            text="Editar",
            width=90,
        )
        edit_button.pack(side="left", padx=6, pady=8)

    def make_left_panel(self, main_area):
        left_panel = ctk.CTkFrame(
            main_area,
        )

        # Add panel to resizable area
        main_area.add(left_panel, minsize=420, width=620)

        # Make scrollable content area
        left_content = ctk.CTkScrollableFrame(
            left_panel,
            corner_radius=0,
        )
        left_content.pack(fill="both", expand=True)

        # Make header section
        self.make_header_section(left_content)

        # Make day sections
        for day in WeekDay:
            self.make_day_section(left_content, day)

    def labeled_row(
        self,
        parent,
        label_text: str,
        variable: ctk.StringVar,
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
        )
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        return row, label, entry

    def make_header_section(self, parent):
        # Make header section frame
        header_section = ctk.CTkFrame(parent)
        header_section.pack(fill="x", padx=12, pady=(12, 8))

        # Make date range variable
        def update_range(*_):
            self.model.date_range = self.date_range_var.get()
            self.on_model_changed()

        self.date_range_var = ctk.StringVar(value=self.model.date_range)
        self.date_range_var.trace_add("write", update_range)

        # Make date range row
        self.labeled_row(
            header_section,
            "Fecha",
            self.date_range_var,
            pady=(12, 6),
        )

        # Make fanart artist variable
        def update_artist(*_):
            self.model.fanart_artist = self.fanart_artist_var.get()
            self.on_model_changed()
        self.fanart_artist_var = ctk.StringVar(value=self.model.fanart_artist)
        self.fanart_artist_var.trace_add("write", update_artist)

        # Make fanart label
        self.labeled_row(header_section, "Artista", self.fanart_artist_var)

        # Make fanart preview
        ImagePreview(header_section, self.model.fanart, self.render_resources, self.on_model_changed)

    def make_day_section(self, parent, day: WeekDay):
        day_schedule = self.get_day_schedule(day)

        # Make day section frame
        day_section = ctk.CTkFrame(parent)
        day_section.pack(fill="x", padx=12, pady=8)

        disable_list = []

        # Make day title
        self.make_day_title(day_section, day_schedule)

        # Make rest day checkbox
        self.make_rest_day_checkbox(day_section, day_schedule, disable_list)

        # Make day image selector
        image = ImagePreview(day_section, day_schedule.image, self.render_resources, self.on_model_changed)
        disable_list.append(image)

        # Make stream title row
        self.make_stream_title_row(day_section, day_schedule, disable_list)

        # Make collab row
        self.make_collab_row(day_section, day_schedule, disable_list)

        # Make subtitle row
        self.make_subtitle_row(day_section, day_schedule, disable_list)

        # Make time row
        self.make_time_row(day_section, day_schedule, disable_list)

        # Make platform selector
        self.make_platform_selector(day_section, day_schedule, disable_list)

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

    def make_rest_day_checkbox(self, parent, day_schedule: DaySchedule, disable_list):
        # Make rest day variable
        rest_day_var = ctk.BooleanVar(value=day_schedule.is_rest_day)

        # Make rest day checkbox
        rest_day_checkbox = ctk.CTkCheckBox(
            parent,
            text="Descanso",
            variable=rest_day_var,
            command=lambda: self.update_rest(day_schedule, rest_day_var, disable_list),
        )
        rest_day_checkbox.pack(anchor="w", padx=12, pady=(0, 12))

    def make_stream_title_row(self, parent, day_schedule: DaySchedule, disable_list):
        def update_title(day_schedule: DaySchedule, stream_title_var):
            day_schedule.title = stream_title_var.get()
            self.on_model_changed()

        # Make stream title variable
        stream_title_var = ctk.StringVar(value=day_schedule.title)
        stream_title_var.trace_add(
            "write",
            lambda *_: update_title(day_schedule, stream_title_var),
        )

        # Make stream title row
        stream_title_row, _, _ = self.labeled_row(
            parent,
            "Título",
            stream_title_var,
        )

        disable_list.append(stream_title_row)

    def make_subtitle_row(self, parent, day_schedule: DaySchedule, disable_list):
        def update_subtitle(day_schedule: DaySchedule, stream_subtitle_var):
            day_schedule.subtitle = stream_subtitle_var.get()
            self.on_model_changed()

        # Make stream subtitle variable
        stream_subtitle_var = ctk.StringVar(value=day_schedule.subtitle)
        stream_subtitle_var.trace_add(
            "write",
            lambda *_: update_subtitle(day_schedule, stream_subtitle_var),
        )

        # Make stream subtitle row
        stream_subtitle_row, _, _ = self.labeled_row(
            parent,
            "Subtítulo",
            stream_subtitle_var,
        )

        disable_list.append(stream_subtitle_row)

    def make_collab_row(self, parent, day_schedule: DaySchedule, disable_list):
        # Make collab section frame
        collab_section = ctk.CTkFrame(parent, fg_color="transparent")
        collab_section.pack(fill="x", padx=12, pady=(0, 12))
        disable_list.append(collab_section)

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
            command=lambda: self.on_select_collab_color(
                day_schedule,
                color_button,
                collab_member_row,
            ),
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
            lambda *_: self.update_collab(day_schedule),
        )

        self.day_collab_rows[day_schedule.day].append(
            {
                "row": collab_member_row,
                "name_var": name_var,
                "color": collab_member.color,
            }
        )

        self.update_collab(day_schedule)

    def remove_collab_member_row(self, day_schedule: DaySchedule, collab_member_row):
        rows = self.day_collab_rows[day_schedule.day]
        self.day_collab_rows[day_schedule.day] = [
            row_data for row_data in rows if row_data["row"] != collab_member_row
        ]

        collab_member_row.destroy()

        if not self.day_collab_rows[day_schedule.day]:
            collab_member_row.master.configure(height=0)
            collab_member_row.master.pack_propagate(False)

        self.update_collab(day_schedule)

    def on_select_collab_color(self, day_schedule: DaySchedule, color_button, collab_member_row):
        initial_color = color_button.cget("fg_color")

        _, selected_color = colorchooser.askcolor(
            color=initial_color,
            title="Seleccionar color de collab",
        )

        if selected_color is None:
            return

        color_button.configure(
            fg_color=selected_color,
            hover_color=selected_color,
        )

        for row_data in self.day_collab_rows[day_schedule.day]:
            if row_data["row"] == collab_member_row:
                row_data["color"] = selected_color
                break

        self.update_collab(day_schedule)

    def make_time_row(self, parent, day_schedule: DaySchedule, disable_list):
        def update_time(time_var):
            day_schedule.time_text = time_var.get()
            self.on_model_changed()

        # Make time variable
        time_var = ctk.StringVar(value=day_schedule.time_text)
        time_var.trace_add(
            "write",
            lambda *_: update_time(time_var),
        )

        # Make time row
        time_row, _, _ = self.labeled_row(
            parent,
            "Hora",
            time_var,
        )

        disable_list.append(time_row)

    def make_platform_selector(self, parent, day_schedule: DaySchedule, disable_list):
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

            def update_platform(platform_var):
                day_schedule.platform = Platform(platform_var.get())
                self.on_model_changed()

            # Make platform radio button
            radio_button = ctk.CTkRadioButton(
                option_frame,
                text="",
                width=20,
                radiobutton_width=16,
                radiobutton_height=16,
                variable=platform_var,
                value=platform.value,
                command=lambda: update_platform(platform_var),
            )
            radio_button.pack(side="left")

            # Load platform icon
            icon_image = self.render_resources.load_platform_icon(
                platform,
                28,
                28,
                NORMAL_PLATFORM_ICON_COLOR,
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
            self.platform_icon_labels[(day_schedule.day, platform)] = icon_label

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

        disable_list.append(platform_row)

    def update_rest(self, day_schedule: DaySchedule, rest_day_var, disable_list):
        day_schedule.is_rest_day = rest_day_var.get()

        state = "disabled" if day_schedule.is_rest_day else "normal"

        for widget in disable_list:
            self.configure_widget_tree_state(widget, state)
            self.configure_widget_tree_visual_state(widget, day_schedule.is_rest_day)

        self.update_platform_icons_visual_state(day_schedule)
        self.on_model_changed()

    def configure_widget_tree_state(self, widget, state: str):
        # Configure widget state if supported
        try:
            widget.configure(state=state)
        except (AttributeError, ValueError, tk.TclError):
            pass

        # Configure children recursively
        for child in widget.winfo_children():
            self.configure_widget_tree_state(child, state)

    def configure_widget_tree_visual_state(self, widget, is_rest_day: bool):
        self.store_widget_visual_defaults(widget)

        if isinstance(widget, ctk.CTkEntry):
            if is_rest_day:
                self.safe_configure(widget, **REST_ENTRY_STYLE)
            else:
                self.restore_widget_visual_defaults(widget)

        elif isinstance(widget, ctk.CTkButton):
            if is_rest_day:
                self.safe_configure(widget, **REST_BUTTON_STYLE)
            else:
                self.restore_widget_visual_defaults(widget)

        elif isinstance(widget, ctk.CTkRadioButton):
            if is_rest_day:
                self.safe_configure(widget, **REST_RADIO_STYLE)
            else:
                self.restore_widget_visual_defaults(widget)

        # Recurse
        for child in widget.winfo_children():
            self.configure_widget_tree_visual_state(child, is_rest_day)

    def store_widget_visual_defaults(self, widget):
        if widget in self.widget_visual_defaults:
            return

        defaults = {}

        for option in (
            "fg_color",
            "hover_color",
            "text_color",
            "placeholder_text_color",
            "border_color",
        ):
            try:
                defaults[option] = widget.cget(option)
            except (AttributeError, ValueError, tk.TclError):
                pass

        self.widget_visual_defaults[widget] = defaults

    def restore_widget_visual_defaults(self, widget):
        defaults = self.widget_visual_defaults.get(widget, {})

        for option, value in defaults.items():
            self.safe_configure(widget, **{option: value})

    def safe_configure(self, widget, **kwargs):
        try:
            widget.configure(**kwargs)
        except (AttributeError, ValueError, tk.TclError):
            pass

    def update_platform_icons_visual_state(self, day_schedule: DaySchedule):
        icon_color = (
            DISABLED_PLATFORM_ICON_COLOR
            if day_schedule.is_rest_day
            else NORMAL_PLATFORM_ICON_COLOR
        )

        for platform in (Platform.TWITCH, Platform.YOUTUBE):
            icon_image = self.render_resources.load_platform_icon(
                platform,
                28,
                28,
                icon_color,
            )

            icon = ctk.CTkImage(
                light_image=icon_image,
                dark_image=icon_image,
                size=(28, 28),
            )

            self.platform_ctk_images[(day_schedule.day, platform, icon_color)] = icon

            icon_label = self.platform_icon_labels[(day_schedule.day, platform)]
            icon_label.configure(image=icon, state="normal")

    def get_day_schedule(self, day: WeekDay) -> DaySchedule:
        if day not in self.model.days:
            self.model.days[day] = DaySchedule(day=day)

        return self.model.days[day]

    def update_collab(self, day_schedule: DaySchedule):
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

    def on_model_changed(self):
        self.schedule_preview_update()

    def schedule_preview_update(self):
        def render_preview():
            self.preview_update_job = None
            self.rendered_preview_image = render_calendar(self.model, self.render_resources)
            self.update_preview_canvas()

        if self.preview_update_job is not None:
            self.root.after_cancel(self.preview_update_job)

        self.preview_update_job = self.root.after(
            120,
            render_preview,
        )

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
