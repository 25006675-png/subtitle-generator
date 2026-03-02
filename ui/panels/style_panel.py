import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, font as tkfont
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family


class StylePanel(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ff = get_font_family()

        # Title
        ctk.CTkLabel(
            self, text="Subtitle Style",
            font=ctk.CTkFont(family=ff, size=FONTS["display"][1], weight="bold"),
            text_color=COLORS["text_heading"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w",
               padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # Primary style column
        self.primary_controls = StyleColumn(self, state, "primary", "Primary (Original)")
        self.primary_controls.grid(row=1, column=0, sticky="nsew", padx=(SPACING["lg"], SPACING["sm"]))

        self.secondary_controls = StyleColumn(self, state, "secondary", "Secondary (Translation)")
        self.secondary_controls.grid(row=1, column=1, sticky="nsew", padx=(SPACING["sm"], SPACING["lg"]))

        # --- Bilingual Layout Tools ---
        self.layout_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        self.layout_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        self.layout_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.layout_frame, text="Bilingual Order:",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            text_color=COLORS["text_primary"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"])

        self.swap_btn = ctk.CTkButton(
            self.layout_frame,
            text="Swap Primary/Secondary Order",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            fg_color=COLORS["button_secondary"],
            hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            command=self.state.toggle_secondary_on_top,
            height=32,
        )
        self.swap_btn.grid(row=0, column=1, sticky="w", padx=(0, SPACING["lg"]), pady=SPACING["md"])

        # Listen for bilingual changes
        self.state.add_listener(self._on_state_change)
        self._update_secondary_visibility()

    def _on_state_change(self, field):
        if field == "bilingual":
            self._update_secondary_visibility()

    def _update_secondary_visibility(self):
        if self.state.bilingual:
            self.secondary_controls.grid()
        else:
            self.secondary_controls.grid_remove()


class StyleColumn(ctk.CTkFrame):
    def __init__(self, parent, state, style_key, title, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"], **kwargs)
        self.state = state
        self.style_key = style_key

        style = self.state.primary_style if style_key == "primary" else self.state.secondary_style
        ff = get_font_family()

        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Section title
        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))
        row += 1

        # Font family
        row = self._add_label(row, "Font Family", ff)
        available_fonts = sorted(set(tkfont.families()))
        self.font_var = ctk.StringVar(value=style.font_family)
        self.font_dropdown = ctk.CTkComboBox(
            self, values=available_fonts, variable=self.font_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["sm"], height=30,
            command=lambda v: self._update_style(font_family=v),
        )
        self.font_dropdown.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        row += 1

        # Separator
        row = self._add_separator(row)

        # Font size with min/max labels
        row = self._add_label(row, "Font Size", ff)
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["xxs"]))
        size_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            size_frame, text="16",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"], width=20,
        ).grid(row=0, column=0)

        self.size_slider = ctk.CTkSlider(
            size_frame, from_=16, to=120, number_of_steps=104,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_size_change, height=14,
        )
        self.size_slider.set(style.font_size)
        self.size_slider.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])

        self.size_label = ctk.CTkLabel(
            size_frame, text=str(style.font_size),
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=35,
        )
        self.size_label.grid(row=0, column=2)

        ctk.CTkLabel(
            size_frame, text="120",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"], width=24,
        ).grid(row=0, column=3)
        row += 1

        # Separator
        row = self._add_separator(row)

        # Text color with canvas swatch
        row = self._add_label(row, "Text Color", ff)
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.grid(row=row, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        self.color_swatch = tk.Canvas(
            color_frame, width=24, height=24,
            highlightthickness=0, cursor="hand2",
        )
        self.color_swatch.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        self._draw_swatch(self.color_swatch, style.primary_color)
        self.color_swatch.bind("<Button-1>", lambda e: self._pick_color("primary_color", self.color_swatch, self.color_hex_label))

        self.color_hex_label = ctk.CTkLabel(
            color_frame, text=style.primary_color,
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"],
        )
        self.color_hex_label.grid(row=0, column=1)
        row += 1

        # Separator
        row = self._add_separator(row)

        # Outline color + thickness
        row = self._add_label(row, "Outline", ff)
        outline_frame = ctk.CTkFrame(self, fg_color="transparent")
        outline_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        outline_frame.grid_columnconfigure(2, weight=1)

        self.outline_swatch = tk.Canvas(
            outline_frame, width=24, height=24,
            highlightthickness=0, cursor="hand2",
        )
        self.outline_swatch.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        self._draw_swatch(self.outline_swatch, style.outline_color)
        self.outline_swatch.bind("<Button-1>", lambda e: self._pick_color("outline_color", self.outline_swatch, self.outline_hex_label))

        self.outline_hex_label = ctk.CTkLabel(
            outline_frame, text=style.outline_color,
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"],
            width=60,
        )
        self.outline_hex_label.grid(row=0, column=1, padx=(0, SPACING["sm"]))

        self.outline_slider = ctk.CTkSlider(
            outline_frame, from_=0, to=8, number_of_steps=8,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_outline_change, height=14,
        )
        self.outline_slider.set(style.outline_thickness)
        self.outline_slider.grid(row=0, column=2, sticky="ew")
        row += 1

        # Separator
        row = self._add_separator(row)

        # Bold / Italic toggles
        row = self._add_label(row, "Style", ff)
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.grid(row=row, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        self.bold_switch = ctk.CTkSwitch(
            toggle_frame, text="Bold",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=lambda: self._update_style(bold=bool(self.bold_switch.get())),
        )
        self.bold_switch.grid(row=0, column=0, padx=(0, SPACING["lg"]))
        if style.bold:
            self.bold_switch.select()

        self.italic_switch = ctk.CTkSwitch(
            toggle_frame, text="Italic",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=lambda: self._update_style(italic=bool(self.italic_switch.get())),
        )
        self.italic_switch.grid(row=0, column=1)
        if style.italic:
            self.italic_switch.select()
        row += 1

        # Separator
        row = self._add_separator(row)

        # Background box
        row = self._add_label(row, "Background Box", ff)
        bg_frame = ctk.CTkFrame(self, fg_color="transparent")
        bg_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        bg_frame.grid_columnconfigure(1, weight=1)

        self.bg_switch = ctk.CTkSwitch(
            bg_frame, text="Enable",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=lambda: self._update_style(background_enabled=bool(self.bg_switch.get())),
        )
        self.bg_switch.grid(row=0, column=0, padx=(0, SPACING["md"]))
        if style.background_enabled:
            self.bg_switch.select()

        self.bg_opacity_slider = ctk.CTkSlider(
            bg_frame, from_=0.0, to=1.0, number_of_steps=20,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=lambda v: self._update_style(background_opacity=round(v, 2)),
            height=14,
        )
        self.bg_opacity_slider.set(style.background_opacity)
        self.bg_opacity_slider.grid(row=0, column=1, sticky="ew")
        row += 1

        # Separator
        row = self._add_separator(row)

        # Position
        row = self._add_label(row, "Position", ff)
        self.position_var = ctk.StringVar(value=style.position.capitalize())
        self.position_seg = ctk.CTkSegmentedButton(
            self, values=["Top", "Center", "Bottom"],
            variable=self.position_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=lambda v: self._update_style(position=v.lower()),
        )
        self.position_seg.grid(row=row, column=0, sticky="ew",
                                padx=SPACING["lg"], pady=(0, SPACING["lg"]))

    def _add_label(self, row, text, ff=None):
        if ff is None:
            ff = get_font_family()
        ctk.CTkLabel(
            self, text=text,
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1], weight="bold"),
            text_color=COLORS["text_muted"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["xxs"]))
        return row + 1

    def _add_separator(self, row):
        ctk.CTkFrame(
            self, fg_color=COLORS["border_subtle"], height=1,
        ).grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["xs"])
        return row + 1

    def _draw_swatch(self, canvas, color):
        canvas.delete("all")
        # Draw a filled circle swatch
        canvas.create_oval(2, 2, 22, 22, fill=color, outline=color, width=1)
        # Subtle border
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        border = COLORS["border"][1] if is_dark else COLORS["border"][0]
        canvas.create_oval(2, 2, 22, 22, outline=border, width=1)
        # Update canvas bg to match parent
        bg = COLORS["bg_secondary"][1] if is_dark else COLORS["bg_secondary"][0]
        canvas.configure(bg=bg)

    def _on_size_change(self, value):
        size = int(value)
        self.size_label.configure(text=str(size))
        self._update_style(font_size=size)

    def _on_outline_change(self, value):
        self._update_style(outline_thickness=int(value))

    def _pick_color(self, attr, swatch_canvas, hex_label):
        style = self.state.primary_style if self.style_key == "primary" else self.state.secondary_style
        current = getattr(style, attr)
        result = colorchooser.askcolor(color=current, title=f"Choose {attr.replace('_', ' ').title()}")
        if result[1]:
            hex_color = result[1]
            self._draw_swatch(swatch_canvas, hex_color)
            hex_label.configure(text=hex_color)
            self._update_style(**{attr: hex_color})

    def _update_style(self, **kwargs):
        if self.style_key == "primary":
            self.state.update_primary_style(**kwargs)
        else:
            self.state.update_secondary_style(**kwargs)
