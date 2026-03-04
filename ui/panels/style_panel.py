import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, font as tkfont, simpledialog
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family
from core.presets import PresetManager


class StylePanel(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.preset_manager = PresetManager()

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

        # --- Preset Section ---
        preset_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        preset_frame.grid(row=1, column=0, columnspan=2, sticky="ew",
                          padx=SPACING["lg"], pady=(0, SPACING["md"]))
        preset_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            preset_frame, text="Style Preset:",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            text_color=COLORS["text_primary"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"])

        preset_names = self.preset_manager.get_all_names()
        self.preset_var = ctk.StringVar(value="")
        self.preset_dropdown = ctk.CTkComboBox(
            preset_frame, values=preset_names if preset_names else ["(none)"],
            variable=self.preset_var,
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["sm"], height=30,
            command=self._apply_preset,
        )
        self.preset_dropdown.grid(row=0, column=1, sticky="ew", padx=SPACING["sm"], pady=SPACING["md"])

        self.save_preset_btn = ctk.CTkButton(
            preset_frame, text="Save as Preset",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["button_secondary"],
            hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            height=30, width=110,
            command=self._save_preset,
            cursor="hand2",
        )
        self.save_preset_btn.grid(row=0, column=2, padx=SPACING["xs"], pady=SPACING["md"])

        self.delete_preset_btn = ctk.CTkButton(
            preset_frame, text="Delete",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["error"],
            hover_color=("#DC2626", "#DC2626"),
            text_color=COLORS["button_text"],
            height=30, width=70,
            command=self._delete_preset,
            cursor="hand2",
        )
        self.delete_preset_btn.grid(row=0, column=3, padx=(0, SPACING["lg"]), pady=SPACING["md"])

        # --- Animation Style card (full width) ---
        self._mode_map = {"Normal": "off", "Word-by-Word": "word_by_word", "Classic": "classic", "Pop-up": "popup"}
        self._mode_reverse = {v: k for k, v in self._mode_map.items()}
        self._entry_anim_map = {"None": "none", "Fade": "fade", "Pop": "pop", "Slide Up": "slide_up", "Typewriter": "typewriter"}
        self._entry_anim_reverse = {v: k for k, v in self._entry_anim_map.items()}
        self._mode_descriptions = {
            "Normal": "Standard subtitle display",
            "Word-by-Word": "Words appear one by one, building the full sentence",
            "Classic": "All words shown \u2014 spoken words highlighted progressively",
            "Pop-up": "Each word appears alone, large and centered",
        }

        anim_card = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        self._anim_card = anim_card
        anim_card.grid(row=2, column=0, columnspan=2, sticky="ew",
                       padx=SPACING["lg"], pady=(0, SPACING["md"]))
        anim_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            anim_card, text="Animation Style",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        current_mode = self._mode_reverse.get(state.karaoke_mode, "Normal")
        self.anim_var = ctk.StringVar(value=current_mode)
        self.anim_selector = ctk.CTkSegmentedButton(
            anim_card,
            values=["Normal", "Word-by-Word", "Classic", "Pop-up"],
            variable=self.anim_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_animation_change,
        )
        self.anim_selector.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["lg"]), pady=(SPACING["md"], SPACING["sm"]))

        self.anim_desc_label = ctk.CTkLabel(
            anim_card, text=self._mode_descriptions[current_mode],
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.anim_desc_label.grid(row=1, column=0, columnspan=2, sticky="w",
                                  padx=SPACING["lg"], pady=(0, SPACING["xs"]))

        # mode_settings_frame — row=2 in anim_card, swaps sub-frames per mode
        self.mode_settings_frame = ctk.CTkFrame(anim_card, fg_color="transparent")
        self.mode_settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew",
                                       padx=0, pady=(0, SPACING["md"]))
        self.mode_settings_frame.grid_columnconfigure(0, weight=1)

        # ── Normal settings ──────────────────────────────────────────────
        self.normal_settings = ctk.CTkFrame(self.mode_settings_frame, fg_color="transparent")
        self.normal_settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.normal_settings, text="Transition:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(SPACING["lg"], SPACING["md"]))

        self.entry_anim_var = ctk.StringVar(value=self._entry_anim_reverse.get(state.animation_style, "None"))
        self.entry_anim_selector = ctk.CTkSegmentedButton(
            self.normal_settings,
            values=["None", "Fade", "Pop", "Slide Up", "Typewriter"],
            variable=self.entry_anim_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_entry_anim_change,
        )
        self.entry_anim_selector.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["lg"]))

        self.duration_row = ctk.CTkFrame(self.normal_settings, fg_color="transparent")
        self.duration_row.grid(row=1, column=0, columnspan=2, sticky="ew",
                               padx=SPACING["lg"], pady=(SPACING["xs"], 0))
        self.duration_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.duration_row, text="Duration:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.duration_slider = ctk.CTkSlider(
            self.duration_row, from_=0.05, to=1.0, number_of_steps=19,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_duration_change, height=14,
        )
        self.duration_slider.set(getattr(state, 'transition_duration', 0.30))
        self.duration_slider.grid(row=0, column=1, sticky="ew")

        self.duration_val_label = ctk.CTkLabel(
            self.duration_row,
            text=f"{int(getattr(state, 'transition_duration', 0.30) * 1000)}ms",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=50,
        )
        self.duration_val_label.grid(row=0, column=2, padx=(SPACING["xs"], 0))

        # Hide duration row on init if animation is "none"
        if state.animation_style == "none":
            self.duration_row.grid_remove()

        # ── Classic settings ──────────────────────────────────────────────
        self.classic_settings = ctk.CTkFrame(self.mode_settings_frame, fg_color="transparent")
        self.classic_settings.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            self.classic_settings, text="Highlight:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(SPACING["lg"], SPACING["sm"]))

        import tkinter as _tk
        self._highlight_swatch = _tk.Canvas(
            self.classic_settings, width=22, height=22,
            highlightthickness=0, cursor="hand2",
        )
        self._highlight_swatch.grid(row=0, column=1, padx=(0, SPACING["xs"]))
        self._draw_highlight_swatch(state.karaoke_highlight_color)
        self._highlight_swatch.bind("<Button-1>", lambda e: self._pick_highlight_color())

        self._highlight_hex_label = ctk.CTkLabel(
            self.classic_settings,
            text=state.karaoke_highlight_color,
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"],
        )
        self._highlight_hex_label.grid(row=0, column=2, sticky="w")

        ctk.CTkLabel(
            self.classic_settings, text="Dimmed:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=1, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], 0))

        self.dimmed_slider = ctk.CTkSlider(
            self.classic_settings, from_=0.1, to=0.9, number_of_steps=16,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_dimmed_change, height=14,
        )
        self.dimmed_slider.set(getattr(state, 'classic_dimmed_opacity', 0.5))
        self.dimmed_slider.grid(row=1, column=1, columnspan=1, sticky="ew",
                                padx=(0, SPACING["xs"]), pady=(SPACING["xs"], 0))

        self.dimmed_val_label = ctk.CTkLabel(
            self.classic_settings,
            text=f"{int(getattr(state, 'classic_dimmed_opacity', 0.5) * 100)}%",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=40,
        )
        self.dimmed_val_label.grid(row=1, column=2, sticky="w", pady=(SPACING["xs"], 0))

        ctk.CTkLabel(
            self.classic_settings, text="Active:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], SPACING["xs"]))

        self.active_marker_var = ctk.StringVar(value={
            "color": "Color", "box": "Box", "color_box": "Color+Box",
        }.get(getattr(state, 'classic_active_marker', 'color'), "Color"))
        ctk.CTkSegmentedButton(
            self.classic_settings,
            values=["Color", "Box", "Color+Box"],
            variable=self.active_marker_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_active_marker_change,
        ).grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, SPACING["lg"]), pady=(SPACING["xs"], SPACING["xs"]))

        ctk.CTkLabel(
            self.classic_settings, text="History:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=3, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], SPACING["xs"]))

        self.history_on_switch = ctk.CTkSwitch(
            self.classic_settings, text="Keep history",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=self._on_history_on_change,
        )
        if getattr(state, 'classic_history_on', False):
            self.history_on_switch.select()
        self.history_on_switch.grid(row=3, column=1, columnspan=2, sticky="w",
                                    padx=(0, SPACING["lg"]), pady=(SPACING["xs"], SPACING["xs"]))

        # ── Pop-up settings ───────────────────────────────────────────────
        self.popup_settings = ctk.CTkFrame(self.mode_settings_frame, fg_color="transparent")
        self.popup_settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.popup_settings, text="Word Scale:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(SPACING["lg"], SPACING["md"]))

        self.popup_scale_slider = ctk.CTkSlider(
            self.popup_settings, from_=1.0, to=2.5, number_of_steps=15,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_popup_scale_change, height=14,
        )
        self.popup_scale_slider.set(getattr(state, 'popup_scale', 1.5))
        self.popup_scale_slider.grid(row=0, column=1, sticky="ew")

        self.popup_scale_val = ctk.CTkLabel(
            self.popup_settings,
            text=f"{getattr(state, 'popup_scale', 1.5):.1f}x",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=40,
        )
        self.popup_scale_val.grid(row=0, column=2, padx=(SPACING["xs"], SPACING["lg"]))

        ctk.CTkLabel(
            self.popup_settings, text="Trail Words:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=1, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], 0))

        self.popup_trail_slider = ctk.CTkSlider(
            self.popup_settings, from_=0, to=5, number_of_steps=5,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_popup_trail_change, height=14,
        )
        self.popup_trail_slider.set(getattr(state, 'popup_trail_count', 3))
        self.popup_trail_slider.grid(row=1, column=1, sticky="ew", pady=(SPACING["xs"], 0))

        self.popup_trail_val = ctk.CTkLabel(
            self.popup_settings,
            text=str(getattr(state, 'popup_trail_count', 3)),
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=40,
        )
        self.popup_trail_val.grid(row=1, column=2, padx=(SPACING["xs"], SPACING["lg"]),
                                  pady=(SPACING["xs"], 0))

        # ── Word-by-Word settings ─────────────────────────────────────────
        self.wordbyw_settings = ctk.CTkFrame(self.mode_settings_frame, fg_color="transparent")
        self.wordbyw_settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.wordbyw_settings, text="Entry Style:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(SPACING["lg"], SPACING["md"]))

        self.wordbyw_entry_var = ctk.StringVar(
            value={"instant": "Instant", "fade": "Fade", "pop": "Pop"}.get(
                getattr(state, 'wordbyw_entry_style', 'instant'), "Instant"
            )
        )
        ctk.CTkSegmentedButton(
            self.wordbyw_settings,
            values=["Instant", "Fade", "Pop"],
            variable=self.wordbyw_entry_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_wordbyw_entry_change,
        ).grid(row=0, column=1, sticky="ew", padx=(0, SPACING["lg"]))

        ctk.CTkLabel(
            self.wordbyw_settings, text="History:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=1, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], SPACING["xs"]))

        self.wordbyw_history_var = ctk.StringVar(
            value={"full": "Full", "dimmed": "Dimmed"}.get(
                getattr(state, 'wordbyw_history_style', 'full'), "Full"
            )
        )
        ctk.CTkSegmentedButton(
            self.wordbyw_settings,
            values=["Full", "Dimmed"],
            variable=self.wordbyw_history_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_wordbyw_history_change,
        ).grid(row=1, column=1, sticky="ew", padx=(0, SPACING["lg"]),
               pady=(SPACING["xs"], SPACING["xs"]))

        # Show the correct sub-frame for the initial mode
        self._show_mode_settings(current_mode)

        # --- Appearance Area ---
        self.style_container = ctk.CTkFrame(self, fg_color="transparent")
        self.style_container.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=SPACING["lg"])
        self.style_container.grid_columnconfigure(0, weight=1)
        self.style_container.grid_columnconfigure(1, weight=1)

        # Main appearance section title
        self.appearance_main_title = ctk.CTkLabel(
            self.style_container, text="Appearance Settings",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        )
        self.appearance_main_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, SPACING["xs"]))

        # Horizontal separator
        self.title_sep = ctk.CTkFrame(self.style_container, height=2, fg_color=COLORS["accent_muted"])
        self.title_sep.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["sm"]))

        # Scope toggle (Global vs This Line)
        scope_row = ctk.CTkFrame(self.style_container, fg_color="transparent")
        scope_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, SPACING["sm"]))
        ctk.CTkLabel(
            scope_row, text="Editing:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, SPACING["sm"]))
        self.scope_var = ctk.StringVar(value="Global")
        self.scope_btn = ctk.CTkSegmentedButton(
            scope_row,
            values=["Global", "This Line"],
            variable=self.scope_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_scope_change,
        )
        self.scope_btn.pack(side="left")

        # Primary Header (Full Width initially, or shared)
        self.appearance_header = ctk.CTkLabel(
            self.style_container, text="Primary (Original)",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            text_color=COLORS["accent"], anchor="w",
        )
        # grid() called in _update_secondary_visibility

        # Secondary header (only shown when bilingual)
        self.secondary_header = ctk.CTkLabel(
            self.style_container, text="Secondary (Translation)",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            text_color=COLORS["warning"], anchor="w",
        )
        # grid() called in _update_secondary_visibility

        self.primary_controls = StyleColumn(self.style_container, state, "primary", "")
        self.primary_controls.grid(row=4, column=0, sticky="nsew", padx=(0, SPACING["sm"]))

        self.secondary_controls = StyleColumn(self.style_container, state, "secondary", "")
        self.secondary_controls.grid(row=4, column=1, sticky="nsew", padx=(SPACING["sm"], 0))

        # --- Bilingual Layout Tools ---
        self.layout_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        self.layout_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
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

        # --- Per-Speaker Styles Section (Feature 4) ---
        self.speaker_styles_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        self.speaker_styles_frame.grid(row=5, column=0, columnspan=2, sticky="ew",
                                        padx=SPACING["lg"], pady=(0, SPACING["md"]))
        self.speaker_styles_frame.grid_columnconfigure(0, weight=1)
        self.speaker_styles_frame.grid_remove()  # Hidden until speakers detected

        ctk.CTkLabel(
            self.speaker_styles_frame, text="Per-Speaker Styles",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        self.speaker_widgets_frame = ctk.CTkFrame(self.speaker_styles_frame, fg_color="transparent")
        self.speaker_widgets_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        self.speaker_widgets_frame.grid_columnconfigure(1, weight=1)

        # Listen for state changes
        self.state.add_listener(self._on_state_change)
        self._update_secondary_visibility()

    def _apply_preset(self, name):
        preset_style = self.preset_manager.get_preset(name)
        if preset_style:
            self.state.update_primary_style(**preset_style.to_dict())
            self.primary_controls.refresh_from_style()

    def _save_preset(self):
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if name and name.strip():
            name = name.strip()
            self.preset_manager.save_user_preset(name, self.state.primary_style)
            self._refresh_preset_dropdown()
            self.preset_var.set(name)

    def _delete_preset(self):
        name = self.preset_var.get()
        if not name:
            return
        if not self.preset_manager.is_user_preset(name):
            return  # Can't delete built-in presets
        self.preset_manager.delete_user_preset(name)
        self._refresh_preset_dropdown()
        self.preset_var.set("")

    def _refresh_preset_dropdown(self):
        names = self.preset_manager.get_all_names()
        self.preset_dropdown.configure(values=names if names else ["(none)"])

    def _show_mode_settings(self, mode_label: str):
        for f in (self.normal_settings, self.classic_settings,
                  self.popup_settings, self.wordbyw_settings):
            f.grid_remove()
        m = {"Normal": self.normal_settings, "Classic": self.classic_settings,
             "Pop-up": self.popup_settings, "Word-by-Word": self.wordbyw_settings}
        if mode_label in m:
            m[mode_label].grid(row=0, column=0, sticky="ew")

    def _on_animation_change(self, value):
        self.state.set_karaoke_mode(self._mode_map.get(value, "off"))
        self.anim_desc_label.configure(text=self._mode_descriptions.get(value, ""))
        self._show_mode_settings(value)

    def _on_entry_anim_change(self, value):
        self.state.set_animation_style(self._entry_anim_map.get(value, "none"))
        if value == "None":
            self.duration_row.grid_remove()
        else:
            self.duration_row.grid()

    def _on_duration_change(self, value):
        self.duration_val_label.configure(text=f"{int(float(value) * 1000)}ms")
        self.state.set_transition_duration(float(value))

    def _on_dimmed_change(self, value):
        self.dimmed_val_label.configure(text=f"{int(float(value) * 100)}%")
        self.state.set_classic_dimmed_opacity(float(value))

    def _on_popup_scale_change(self, value):
        self.popup_scale_val.configure(text=f"{float(value):.1f}x")
        self.state.set_popup_scale(float(value))

    def _on_popup_trail_change(self, value):
        count = int(round(float(value)))
        self.popup_trail_val.configure(text=str(count))
        self.state.set_popup_trail_count(count)

    def _on_wordbyw_entry_change(self, value):
        self.state.set_wordbyw_entry_style(value.lower())

    def _on_wordbyw_history_change(self, value):
        self.state.set_wordbyw_history_style(value.lower())

    def _on_active_marker_change(self, value):
        mapping = {"Color": "color", "Box": "box", "Color+Box": "color_box"}
        self.state.set_classic_active_marker(mapping.get(value, "color"))

    def _on_history_on_change(self):
        self.state.set_classic_history_on(self.history_on_switch.get() == 1)

    def _on_state_change(self, field):
        if field == "bilingual":
            self._update_secondary_visibility()
        elif field == "speakers":
            self._update_speaker_styles()
        elif field == "karaoke_mode":
            display = self._mode_reverse.get(self.state.karaoke_mode, "Normal")
            self.anim_var.set(display)
            self.anim_desc_label.configure(text=self._mode_descriptions.get(display, ""))
            self._show_mode_settings(display)
        elif field == "animation_style":
            self.entry_anim_var.set(self._entry_anim_reverse.get(self.state.animation_style, "None"))
            if self.state.animation_style == "none":
                self.duration_row.grid_remove()
            else:
                self.duration_row.grid()
        elif field == "classic_active_marker":
            mapping = {"color": "Color", "box": "Box", "color_box": "Color+Box"}
            self.active_marker_var.set(mapping.get(self.state.classic_active_marker, "Color"))
        elif field == "classic_history_on":
            if self.state.classic_history_on:
                self.history_on_switch.select()
            else:
                self.history_on_switch.deselect()
        elif field == "karaoke_highlight_color":
            self._draw_highlight_swatch(self.state.karaoke_highlight_color)
            self._highlight_hex_label.configure(text=self.state.karaoke_highlight_color)
        elif field == "transition_duration":
            self.duration_slider.set(self.state.transition_duration)
            self.duration_val_label.configure(text=f"{int(self.state.transition_duration * 1000)}ms")
        elif field == "classic_dimmed_opacity":
            self.dimmed_slider.set(self.state.classic_dimmed_opacity)
            self.dimmed_val_label.configure(text=f"{int(self.state.classic_dimmed_opacity * 100)}%")
        elif field == "popup_scale":
            self.popup_scale_slider.set(self.state.popup_scale)
            self.popup_scale_val.configure(text=f"{self.state.popup_scale:.1f}x")
        elif field == "popup_trail_count":
            self.popup_trail_slider.set(self.state.popup_trail_count)
            self.popup_trail_val.configure(text=str(self.state.popup_trail_count))
        elif field == "wordbyw_entry_style":
            self.wordbyw_entry_var.set(self.state.wordbyw_entry_style.capitalize())
        elif field == "wordbyw_history_style":
            self.wordbyw_history_var.set(self.state.wordbyw_history_style.capitalize())
        elif field == "selected_subtitle":
            if self.scope_var.get() == "This Line":
                self._refresh_scope_display()
        elif field == "style":
            if self.scope_var.get() == "Global":
                self.primary_controls.refresh_from_style()

    def _on_scope_change(self, value):
        if value == "This Line":
            if self.state.selected_subtitle_index < 0:
                self.scope_var.set("Global")
                return
            self._refresh_scope_display()
        else:
            self.primary_controls.set_scope("global", self.state.primary_style)

    def _refresh_scope_display(self):
        idx = self.state.selected_subtitle_index
        if idx < 0:
            self.scope_var.set("Global")
            self.primary_controls.set_scope("global", self.state.primary_style)
            return
        sub = self.state.subtitles[idx]
        style = sub.style_override if sub.style_override is not None else self.state.primary_style
        self.primary_controls.set_scope("line", style)

    def _draw_highlight_swatch(self, color):
        self._highlight_swatch.delete("all")
        self._highlight_swatch.create_oval(2, 2, 20, 20, fill=color, outline=color, width=1)
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        border = COLORS["border"][1] if is_dark else COLORS["border"][0]
        self._highlight_swatch.create_oval(2, 2, 20, 20, outline=border, width=1)
        bg = COLORS["bg_secondary"][1] if is_dark else COLORS["bg_secondary"][0]
        self._highlight_swatch.configure(bg=bg)

    def _pick_highlight_color(self):
        result = colorchooser.askcolor(
            color=self.state.karaoke_highlight_color, title="Choose Highlight Color"
        )
        if result[1]:
            self.state.set_karaoke_highlight_color(result[1])

    def _update_secondary_visibility(self):
        if self.state.bilingual:
            self.appearance_main_title.configure(text="Appearance Shared Preview")
            self.appearance_header.grid(row=3, column=0, sticky="w", pady=(SPACING["sm"], 0))
            self.secondary_header.grid(row=3, column=1, sticky="w", padx=(SPACING["sm"], 0), pady=(SPACING["sm"], 0))
            self.secondary_controls.grid()
        else:
            self.appearance_main_title.configure(text="Appearance Settings")
            self.appearance_header.grid_remove()
            self.secondary_header.grid_remove()
            self.secondary_controls.grid_remove()

    def _update_speaker_styles(self):
        ff = get_font_family()
        speakers = getattr(self.state, 'speakers', {})
        if not speakers:
            self.speaker_styles_frame.grid_remove()
            return

        self.speaker_styles_frame.grid()

        # Clear existing widgets
        for w in self.speaker_widgets_frame.winfo_children():
            w.destroy()

        for i, (spk_id, spk_info) in enumerate(speakers.items()):
            row_frame = ctk.CTkFrame(self.speaker_widgets_frame, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=SPACING["xs"])
            row_frame.grid_columnconfigure(1, weight=1)

            # Color indicator
            color = "#FFFFFF"
            if spk_info.style:
                color = spk_info.style.primary_color

            color_canvas = tk.Canvas(row_frame, width=20, height=20, highlightthickness=0)
            color_canvas.create_oval(2, 2, 18, 18, fill=color, outline=color)
            color_canvas.grid(row=0, column=0, padx=(0, SPACING["sm"]))

            # Speaker name entry
            name_entry = ctk.CTkEntry(
                row_frame,
                font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
                fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
                height=28,
            )
            name_entry.insert(0, spk_info.display_name or spk_id)
            name_entry.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])
            name_entry.bind("<FocusOut>", lambda e, sid=spk_id, entry=name_entry: self._on_speaker_name_change(sid, entry.get()))

            # Color picker button
            color_btn = ctk.CTkButton(
                row_frame, text="Color",
                font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
                fg_color=COLORS["button_secondary"],
                hover_color=COLORS["accent"],
                text_color=COLORS["text_primary"],
                height=26, width=50,
                command=lambda sid=spk_id: self._pick_speaker_color(sid),
                cursor="hand2",
            )
            color_btn.grid(row=0, column=2, padx=SPACING["xs"])

    def _on_speaker_name_change(self, speaker_id, name):
        self.state.update_speaker(speaker_id, display_name=name)

    def _pick_speaker_color(self, speaker_id):
        speakers = getattr(self.state, 'speakers', {})
        spk = speakers.get(speaker_id)
        if not spk:
            return
        current = spk.style.primary_color if spk.style else "#FFFFFF"
        result = colorchooser.askcolor(color=current, title=f"Choose color for {spk.display_name or speaker_id}")
        if result[1]:
            self.state.update_speaker(speaker_id, color=result[1])
            self._update_speaker_styles()


class StyleColumn(ctk.CTkFrame):
    def __init__(self, parent, state, style_key, title, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"], **kwargs)
        self.state = state
        self.style_key = style_key
        self._scope = "global"  # "global" or "line"

        style = self.state.primary_style if style_key == "primary" else self.state.secondary_style
        ff = get_font_family()

        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Section title (only show if title provided)
        if title:
            ctk.CTkLabel(
                self, text=title,
                font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
                text_color=COLORS["text_heading"],
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))
            row += 1
        else:
            # Add top padding if no title
            ctk.CTkFrame(self, height=SPACING["md"], fg_color="transparent").grid(row=row, column=0)
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
                                padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        row += 1

        # Position Offset slider
        offset_frame = ctk.CTkFrame(self, fg_color="transparent")
        offset_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        offset_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            offset_frame, text="Offset:",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
        ).grid(row=0, column=0, padx=(0, SPACING["xs"]))
        self.pos_offset_slider = ctk.CTkSlider(
            offset_frame, from_=-50, to=50, number_of_steps=100,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_pos_offset_change, height=14,
        )
        self.pos_offset_slider.set(getattr(style, 'position_offset', 0))
        self.pos_offset_slider.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])
        self.pos_offset_label = ctk.CTkLabel(
            offset_frame,
            text=f"{getattr(style, 'position_offset', 0):+d}%",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=40,
        )
        self.pos_offset_label.grid(row=0, column=2)
        row += 1

        # Separator
        row = self._add_separator(row)

        # Shadow
        row = self._add_label(row, "Shadow", ff)
        shadow_frame = ctk.CTkFrame(self, fg_color="transparent")
        shadow_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        shadow_frame.grid_columnconfigure(2, weight=1)

        self.shadow_switch = ctk.CTkSwitch(
            shadow_frame, text="Enable",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=lambda: self._update_style(shadow_enabled=bool(self.shadow_switch.get())),
        )
        self.shadow_switch.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        if getattr(style, 'shadow_enabled', False):
            self.shadow_switch.select()

        self.shadow_swatch = tk.Canvas(
            shadow_frame, width=22, height=22, highlightthickness=0, cursor="hand2",
        )
        self.shadow_swatch.grid(row=0, column=1, padx=(0, SPACING["xs"]))
        self._draw_swatch(self.shadow_swatch, getattr(style, 'shadow_color', '#000000'))
        self.shadow_swatch.bind("<Button-1>", lambda e: self._pick_color("shadow_color", self.shadow_swatch, self.shadow_color_label))

        self.shadow_color_label = ctk.CTkLabel(
            shadow_frame, text=getattr(style, 'shadow_color', '#000000'),
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=60,
        )
        self.shadow_color_label.grid(row=0, column=2, sticky="w")
        row += 1

        # Shadow offsets + blur
        shadow_sliders = ctk.CTkFrame(self, fg_color="transparent")
        shadow_sliders.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        shadow_sliders.grid_columnconfigure(1, weight=1)
        shadow_sliders.grid_columnconfigure(3, weight=1)
        shadow_sliders.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(shadow_sliders, text="X:", font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
                     text_color=COLORS["text_muted"]).grid(row=0, column=0, padx=(0, 2))
        self.shadow_x_slider = ctk.CTkSlider(
            shadow_sliders, from_=0, to=20, number_of_steps=20,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=lambda v: self._update_style(shadow_offset_x=int(v)), height=12,
        )
        self.shadow_x_slider.set(getattr(style, 'shadow_offset_x', 2))
        self.shadow_x_slider.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["sm"]))

        ctk.CTkLabel(shadow_sliders, text="Y:", font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
                     text_color=COLORS["text_muted"]).grid(row=0, column=2, padx=(0, 2))
        self.shadow_y_slider = ctk.CTkSlider(
            shadow_sliders, from_=0, to=20, number_of_steps=20,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=lambda v: self._update_style(shadow_offset_y=int(v)), height=12,
        )
        self.shadow_y_slider.set(getattr(style, 'shadow_offset_y', 2))
        self.shadow_y_slider.grid(row=0, column=3, sticky="ew", padx=(0, SPACING["sm"]))

        ctk.CTkLabel(shadow_sliders, text="Blur:", font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
                     text_color=COLORS["text_muted"]).grid(row=0, column=4, padx=(0, 2))
        self.shadow_blur_slider = ctk.CTkSlider(
            shadow_sliders, from_=0, to=20, number_of_steps=20,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=lambda v: self._update_style(shadow_blur=int(v)), height=12,
        )
        self.shadow_blur_slider.set(getattr(style, 'shadow_blur', 0))
        self.shadow_blur_slider.grid(row=0, column=5, sticky="ew")
        row += 1

        # Separator
        row = self._add_separator(row)

        # Glow
        row = self._add_label(row, "Glow", ff)
        glow_frame = ctk.CTkFrame(self, fg_color="transparent")
        glow_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        glow_frame.grid_columnconfigure(2, weight=1)

        self.glow_switch = ctk.CTkSwitch(
            glow_frame, text="Enable",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=lambda: self._update_style(glow_enabled=bool(self.glow_switch.get())),
        )
        self.glow_switch.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        if getattr(style, 'glow_enabled', False):
            self.glow_switch.select()

        self.glow_swatch = tk.Canvas(
            glow_frame, width=22, height=22, highlightthickness=0, cursor="hand2",
        )
        self.glow_swatch.grid(row=0, column=1, padx=(0, SPACING["xs"]))
        self._draw_swatch(self.glow_swatch, getattr(style, 'glow_color', '#FFFFFF'))
        self.glow_swatch.bind("<Button-1>", lambda e: self._pick_color("glow_color", self.glow_swatch, self.glow_color_label))

        self.glow_color_label = ctk.CTkLabel(
            glow_frame, text=getattr(style, 'glow_color', '#FFFFFF'),
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=60,
        )
        self.glow_color_label.grid(row=0, column=2, sticky="w")
        row += 1

        glow_radius_frame = ctk.CTkFrame(self, fg_color="transparent")
        glow_radius_frame.grid(row=row, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))
        glow_radius_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(glow_radius_frame, text="Radius:",
                     font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
                     text_color=COLORS["text_muted"]).grid(row=0, column=0, padx=(0, SPACING["xs"]))
        self.glow_radius_slider = ctk.CTkSlider(
            glow_radius_frame, from_=1, to=30, number_of_steps=29,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_glow_radius_change, height=12,
        )
        self.glow_radius_slider.set(getattr(style, 'glow_radius', 5))
        self.glow_radius_slider.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])
        self.glow_radius_label = ctk.CTkLabel(
            glow_radius_frame,
            text=str(getattr(style, 'glow_radius', 5)),
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=30,
        )
        self.glow_radius_label.grid(row=0, column=2)

    def _get_current_style(self):
        """Return the style object this column should read/write, based on current scope."""
        if self._scope == "line":
            idx = self.state.selected_subtitle_index
            if 0 <= idx < len(self.state.subtitles):
                sub = self.state.subtitles[idx]
                return sub.style_override if sub.style_override is not None else self.state.primary_style
        return self.state.primary_style if self.style_key == "primary" else self.state.secondary_style

    def set_scope(self, scope: str, style=None):
        """Switch between 'global' and 'line' scope and optionally refresh widgets."""
        self._scope = scope
        self.refresh_from_style(style)

    def refresh_from_style(self, style=None):
        """Sync all UI controls to match the given style (or current scope style if None)."""
        if style is None:
            style = self._get_current_style()
        self.font_var.set(style.font_family)
        self.size_slider.set(style.font_size)
        self.size_label.configure(text=str(style.font_size))
        self._draw_swatch(self.color_swatch, style.primary_color)
        self.color_hex_label.configure(text=style.primary_color)
        self._draw_swatch(self.outline_swatch, style.outline_color)
        self.outline_hex_label.configure(text=style.outline_color)
        self.outline_slider.set(style.outline_thickness)
        if style.bold:
            self.bold_switch.select()
        else:
            self.bold_switch.deselect()
        if style.italic:
            self.italic_switch.select()
        else:
            self.italic_switch.deselect()
        if style.background_enabled:
            self.bg_switch.select()
        else:
            self.bg_switch.deselect()
        self.bg_opacity_slider.set(style.background_opacity)
        self.position_var.set(style.position.capitalize())
        offset = getattr(style, 'position_offset', 0)
        self.pos_offset_slider.set(offset)
        self.pos_offset_label.configure(text=f"{offset:+d}%")
        self._draw_swatch(self.shadow_swatch, getattr(style, 'shadow_color', '#000000'))
        self.shadow_color_label.configure(text=getattr(style, 'shadow_color', '#000000'))
        self.shadow_x_slider.set(getattr(style, 'shadow_offset_x', 2))
        self.shadow_y_slider.set(getattr(style, 'shadow_offset_y', 2))
        self.shadow_blur_slider.set(getattr(style, 'shadow_blur', 0))
        if getattr(style, 'shadow_enabled', False):
            self.shadow_switch.select()
        else:
            self.shadow_switch.deselect()
        self._draw_swatch(self.glow_swatch, getattr(style, 'glow_color', '#FFFFFF'))
        self.glow_color_label.configure(text=getattr(style, 'glow_color', '#FFFFFF'))
        self.glow_radius_slider.set(getattr(style, 'glow_radius', 5))
        self.glow_radius_label.configure(text=str(getattr(style, 'glow_radius', 5)))
        if getattr(style, 'glow_enabled', False):
            self.glow_switch.select()
        else:
            self.glow_switch.deselect()

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
        canvas.create_oval(2, 2, 22, 22, fill=color, outline=color, width=1)
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        border = COLORS["border"][1] if is_dark else COLORS["border"][0]
        canvas.create_oval(2, 2, 22, 22, outline=border, width=1)
        bg = COLORS["bg_secondary"][1] if is_dark else COLORS["bg_secondary"][0]
        canvas.configure(bg=bg)

    def _on_size_change(self, value):
        size = int(value)
        self.size_label.configure(text=str(size))
        self._update_style(font_size=size)

    def _on_outline_change(self, value):
        self._update_style(outline_thickness=int(value))

    def _on_pos_offset_change(self, value):
        v = int(round(float(value)))
        self.pos_offset_label.configure(text=f"{v:+d}%")
        self._update_style(position_offset=v)

    def _on_glow_radius_change(self, value):
        v = int(value)
        self.glow_radius_label.configure(text=str(v))
        self._update_style(glow_radius=v)

    def _pick_color(self, attr, swatch_canvas, hex_label):
        style = self._get_current_style()
        current = getattr(style, attr)
        result = colorchooser.askcolor(color=current, title=f"Choose {attr.replace('_', ' ').title()}")
        if result[1]:
            hex_color = result[1]
            self._draw_swatch(swatch_canvas, hex_color)
            hex_label.configure(text=hex_color)
            self._update_style(**{attr: hex_color})

    def _update_style(self, **kwargs):
        if self._scope == "line":
            import copy
            idx = self.state.selected_subtitle_index
            if 0 <= idx < len(self.state.subtitles):
                sub = self.state.subtitles[idx]
                if sub.style_override is None:
                    sub.style_override = copy.deepcopy(self.state.primary_style)
                for k, v in kwargs.items():
                    if hasattr(sub.style_override, k):
                        setattr(sub.style_override, k, v)
                self.state.notify("subtitles_edited")
                self.state.notify("style")
        elif self.style_key == "primary":
            self.state.update_primary_style(**kwargs)
        else:
            self.state.update_secondary_style(**kwargs)
