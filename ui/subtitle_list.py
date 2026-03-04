import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family
from core.subtitle_model import remap_word_timestamps, SubtitleStyle


class SubtitleList(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=0, **kwargs)
        self.state = state
        self.rows = []
        self._active_editor = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ff = get_font_family()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["md"], SPACING["sm"]))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Subtitles",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.count_label = ctk.CTkLabel(
            header, text="0 lines",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
        )
        self.count_label.grid(row=0, column=1, sticky="e")

        # Column headers with background bar
        self.col_header = ctk.CTkFrame(self, fg_color=COLORS["bg_tertiary"], height=28,
                                   corner_radius=RADIUS["xs"])
        self.col_header.grid(row=1, column=0, sticky="ew", padx=SPACING["md"])
        self.col_header.grid_columnconfigure(2, weight=1)
        self.col_header.grid_columnconfigure(3, weight=1)

        self._build_column_headers()

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            scrollbar_button_color=COLORS["scrollbar"],
            scrollbar_button_hover_color=COLORS["scrollbar_hover"],
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["sm"], pady=(SPACING["xs"], SPACING["sm"]))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Listen to state
        self.state.add_listener(self._on_state_change)

    def _build_column_headers(self):
        ff = get_font_family()
        for w in self.col_header.winfo_children():
            w.destroy()

        has_speakers = bool(getattr(self.state, 'speakers', {}))
        has_translation = self.state.bilingual and any(s.translated_text for s in self.state.subtitles)
        
        columns = [("#", 30), ("TIME", 90)]
        if has_speakers:
            columns.append(("SPEAKER", 70))
        
        columns.append(("ORIGINAL", 100))
        if has_translation:
            columns.append(("TRANSLATION", 100))

        for col, (text, w) in enumerate(columns):
            ctk.CTkLabel(
                self.col_header, text=text,
                font=ctk.CTkFont(family=ff, size=FONTS["caption"][1], weight="bold"),
                text_color=COLORS["text_muted"],
                width=w,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=(SPACING["sm"] if col == 0 else 0, SPACING["sm"]))

    def _on_state_change(self, field):
        if field in ("subtitles", "speakers"):
            self._build_column_headers()
            self._rebuild_list()
        elif field == "selected_subtitle":
            self._update_selection()
        elif field == "bilingual":
            self._build_column_headers()
            self._rebuild_list()
        elif field == "subtitles_edited":
            self._rebuild_list()

    def _rebuild_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.rows = []

        ff = get_font_family()
        subs = self.state.subtitles
        self.count_label.configure(text=f"{len(subs)} lines")

        has_speakers = bool(getattr(self.state, 'speakers', {}))
        speakers = getattr(self.state, 'speakers', {})
        has_translation = self.state.bilingual and any(s.translated_text for s in subs)

        for i, sub in enumerate(subs):
            row_color = COLORS["row_even"] if i % 2 == 0 else COLORS["row_odd"]
            row_bg = self._resolve_color(row_color)

            # Outer row frame
            row = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=row_color,
                corner_radius=0,
                height=24,
                cursor="hand2",
            )
            row.grid(row=i, column=0, sticky="ew", pady=0)
            row.grid_propagate(False) # Force the height to exactly 24px

            col_idx = 0
            # Configure column weights based on presence of speakers and translation
            if has_speakers:
                row.grid_columnconfigure(1, minsize=30)
                row.grid_columnconfigure(2, minsize=110)
                row.grid_columnconfigure(3, minsize=60)
                if has_translation:
                    row.grid_columnconfigure(4, weight=1)
                    row.grid_columnconfigure(5, weight=1)
                else:
                    row.grid_columnconfigure(4, weight=2)
            else:
                row.grid_columnconfigure(1, minsize=30)
                row.grid_columnconfigure(2, minsize=110)
                if has_translation:
                    row.grid_columnconfigure(3, weight=1)
                    row.grid_columnconfigure(4, weight=1)
                else:
                    row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(0, minsize=2)
            row.grid_rowconfigure(0, weight=1)

            # Selection accent strip (always in grid, colour toggled)
            accent_strip = ctk.CTkFrame(row, fg_color="transparent", width=2, corner_radius=0)
            accent_strip.grid(row=0, column=col_idx, sticky="ns", rowspan=1)
            col_idx += 1

            # Index
            index_label = tk.Label(
                row,
                text=str(sub.index),
                font=(FONTS["mono_small"][0], 9),
                fg=self._resolve_color(COLORS["text_secondary"]),
                bg=row_bg,
                anchor="center",
                padx=0,
                pady=0,
            )
            index_label.grid(row=0, column=col_idx, padx=(2, 2), sticky="nsew")
            col_idx += 1

            # Time
            time_str = f"{self._fmt(sub.start)}-{self._fmt(sub.end)}"
            time_label = tk.Label(
                row,
                text=time_str,
                font=(FONTS["mono_small"][0], 9),
                fg=self._resolve_color(COLORS["text_primary"]),
                bg=row_bg,
                anchor="w",
                padx=0,
                pady=0,
            )
            time_label.grid(row=0, column=col_idx, padx=(2, 2), sticky="nsew")
            col_idx += 1

            text_widgets = [index_label, time_label]

            # Speaker column (Feature 4)
            if has_speakers:
                spk_name = sub.speaker_id
                spk_color = COLORS["text_muted"]
                if sub.speaker_id and sub.speaker_id in speakers:
                    spk_info = speakers[sub.speaker_id]
                    spk_name = spk_info.display_name or sub.speaker_id
                    if spk_info.style:
                        spk_color = spk_info.style.primary_color

                speaker_fg = spk_color if isinstance(spk_color, str) else self._resolve_color(spk_color)
                speaker_label = tk.Label(
                    row,
                    text=spk_name or "-",
                    font=(ff, 9, "bold"),
                    fg=speaker_fg,
                    bg=row_bg,
                    anchor="w",
                    padx=0,
                    pady=0,
                )
                speaker_label.grid(row=0, column=col_idx, padx=(2, 2), sticky="nsew")
                text_widgets.append(speaker_label)
                col_idx += 1

            # Original text (visible + editable via double-click)
            original_display = sub.original_text.strip() if sub.original_text else ""
            if not original_display and getattr(sub, "words", None):
                original_display = " ".join((w.word or "").strip() for w in sub.words).strip()
            if not original_display:
                original_display = "…"

            orig_label = tk.Label(
                row,
                font=(ff, 10),
                fg=self._resolve_color(COLORS["text_primary"]),
                bg=row_bg,
                text=original_display,
                anchor="w",
                justify="left",
                padx=0,
                pady=0,
            )
            orig_label.grid(row=0, column=col_idx, sticky="nsew", padx=(2, 2))
            orig_label.bind("<Double-Button-1>", lambda e, idx=i: self._start_inline_edit(e.widget, idx, "original"))
            text_widgets.append(orig_label)
            col_idx += 1

            # Translation text
            if has_translation:
                trans_label = tk.Label(
                    row,
                    font=(ff, 10),
                    fg=self._resolve_color(COLORS["text_secondary"]),
                    bg=row_bg,
                    text=(sub.translated_text or "").strip() or "…",
                    anchor="w",
                    justify="left",
                    padx=0,
                    pady=0,
                )
                trans_label.grid(row=0, column=col_idx, sticky="nsew", padx=(2, 2))
                trans_label.bind("<Double-Button-1>", lambda e, idx=i: self._start_inline_edit(e.widget, idx, "translated"))
                text_widgets.append(trans_label)

            # Override style indicator dot (shown if line has style_override)
            has_override = getattr(sub, 'style_override', None) is not None
            override_dot = tk.Label(
                row,
                text="●" if has_override else "○",
                font=(ff, 8),
                fg=self._resolve_color(COLORS["accent"]) if has_override else self._resolve_color(COLORS["text_muted"]),
                bg=row_bg,
                anchor="center",
                cursor="hand2",
                padx=0, pady=0,
                width=2,
            )
            override_dot.grid(row=0, column=col_idx, padx=(0, 2), sticky="nsew")
            text_widgets.append(override_dot)

            # Row click + hover bindings on all children
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, idx=i: self._on_row_click(idx))
                child.bind("<Enter>", lambda e, idx=i: self._on_row_hover(idx, True))
                child.bind("<Leave>", lambda e, idx=i: self._on_row_hover(idx, False))
                child.bind("<Button-3>", lambda e, idx=i: self._on_row_right_click(e, idx))

            row.bind("<Button-1>", lambda e, idx=i: self._on_row_click(idx))
            row.bind("<Enter>", lambda e, idx=i: self._on_row_hover(idx, True))
            row.bind("<Leave>", lambda e, idx=i: self._on_row_hover(idx, False))
            row.bind("<Button-3>", lambda e, idx=i: self._on_row_right_click(e, idx))

            self.rows.append((row, accent_strip, text_widgets))

        self._update_selection()

    def _on_row_click(self, index):
        self.state.set_selected_subtitle(index)

    def _on_row_hover(self, index, entering):
        if index >= len(self.rows):
            return
        row, _, widgets = self.rows[index]
        if index == self.state.selected_subtitle_index:
            return
        if entering:
            row.configure(fg_color=COLORS["row_hover"])
            self._set_widget_row_bg(widgets, self._resolve_color(COLORS["row_hover"]))
        else:
            color = COLORS["row_even"] if index % 2 == 0 else COLORS["row_odd"]
            row.configure(fg_color=color)
            self._set_widget_row_bg(widgets, self._resolve_color(color))

    def _start_inline_edit(self, label_widget, index, field):
        if index >= len(self.state.subtitles):
            return

        if self._active_editor is not None:
            self._commit_inline_edit()

        sub = self.state.subtitles[index]
        if field == "original":
            current = sub.original_text or ""
        else:
            current = sub.translated_text or ""

        label_widget.update_idletasks()
        row = label_widget.master
        row.update_idletasks()

        x = label_widget.winfo_x()
        y = label_widget.winfo_y()
        w = max(80, label_widget.winfo_width())
        h = max(22, label_widget.winfo_height())

        entry = tk.Entry(
            row,
            font=label_widget.cget("font"),
            fg=label_widget.cget("fg"),
            bg=self._resolve_color(COLORS["entry_bg"]),
            insertbackground=self._resolve_color(COLORS["text_primary"]),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self._resolve_color(COLORS["border_subtle"]),
            highlightcolor=self._resolve_color(COLORS["accent"]),
        )
        entry.insert(0, current)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()
        entry.selection_range(0, tk.END)

        entry.bind("<Return>", lambda e: self._commit_inline_edit())
        entry.bind("<KP_Enter>", lambda e: self._commit_inline_edit())
        entry.bind("<Escape>", lambda e: self._cancel_inline_edit())
        entry.bind("<FocusOut>", lambda e: self._commit_inline_edit())

        self._active_editor = {
            "entry": entry,
            "index": index,
            "field": field,
            "label": label_widget,
        }

    def _commit_inline_edit(self):
        if self._active_editor is None:
            return

        editor = self._active_editor
        entry = editor["entry"]
        index = editor["index"]
        field = editor["field"]
        label_widget = editor["label"]

        try:
            new_text = entry.get()
        except Exception:
            self._active_editor = None
            return

        if 0 <= index < len(self.state.subtitles):
            sub = self.state.subtitles[index]
            if field == "original":
                if sub.words and new_text.strip():
                    sub.words = remap_word_timestamps(
                        sub.words, new_text.strip(), sub.start, sub.end
                    )
                elif not new_text.strip():
                    sub.words = []
                sub.original_text = new_text
                display = new_text.strip() or "…"
                label_widget.configure(text=display)
            else:
                sub.translated_text = new_text
                display = new_text.strip() or "…"
                label_widget.configure(text=display)
            self.state.notify("subtitles_edited")

        try:
            entry.destroy()
        except Exception:
            pass
        self._active_editor = None

    def _cancel_inline_edit(self):
        if self._active_editor is None:
            return
        entry = self._active_editor.get("entry")
        try:
            entry.destroy()
        except Exception:
            pass
        self._active_editor = None

    def _update_selection(self):
        sel = self.state.selected_subtitle_index
        for i, (row, accent_strip, widgets) in enumerate(self.rows):
            if i == sel:
                row.configure(fg_color=COLORS["row_selected"])
                accent_strip.configure(fg_color=COLORS["accent"])
                self._set_widget_row_bg(widgets, self._resolve_color(COLORS["row_selected"]))
            else:
                color = COLORS["row_even"] if i % 2 == 0 else COLORS["row_odd"]
                row.configure(fg_color=color)
                accent_strip.configure(fg_color="transparent")
                self._set_widget_row_bg(widgets, self._resolve_color(color))

    def _set_widget_row_bg(self, widgets, bg_color: str):
        for widget in widgets:
            try:
                if isinstance(widget, tk.Label):
                    widget.configure(bg=bg_color)
                else:
                    widget.configure(fg_color=bg_color)
            except Exception:
                pass

    @staticmethod
    def _resolve_color(color) -> str:
        if isinstance(color, (tuple, list)) and len(color) >= 2:
            is_dark = ctk.get_appearance_mode().lower() == "dark"
            return color[1] if is_dark else color[0]
        return color

    def _on_row_right_click(self, event, index):
        self.state.set_selected_subtitle(index)
        menu = tk.Menu(self, tearoff=0)
        has_override = getattr(self.state.subtitles[index], 'style_override', None) is not None
        menu.add_command(label="Set line style…", command=lambda: self._open_line_style_dialog(index))
        if has_override:
            menu.add_command(label="Clear line style", command=lambda: self._clear_line_style(index))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _open_line_style_dialog(self, index):
        if index >= len(self.state.subtitles):
            return
        sub = self.state.subtitles[index]
        base_style = self.state.get_style_for_subtitle(sub)
        # If no override yet, clone the current effective style
        current = sub.style_override if sub.style_override is not None else SubtitleStyle(**base_style.to_dict())
        dialog = LineStyleDialog(self, self.state, index, current)
        dialog.grab_set()

    def _clear_line_style(self, index):
        if index < len(self.state.subtitles):
            self.state.subtitles[index].style_override = None
            self.state.notify("subtitles_edited")
            self._rebuild_list()

    @staticmethod
    def _fmt(seconds: float) -> str:
        total = max(0.0, float(seconds))
        h = int(total // 3600)
        m = int((total % 3600) // 60)
        s = total % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:06.3f}"
        return f"{m:02d}:{s:06.3f}"


class LineStyleDialog(ctk.CTkToplevel):
    """Compact dialog for setting a per-line style override on a subtitle entry."""

    def __init__(self, parent, state, subtitle_index: int, current_style: SubtitleStyle):
        super().__init__(parent)
        self.state = state
        self.subtitle_index = subtitle_index
        self.style = SubtitleStyle(**current_style.to_dict())  # working copy

        ff = get_font_family()
        self.title("Line Style Override")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"] if isinstance(COLORS["bg_primary"], str)
                       else COLORS["bg_primary"][1])

        self.grid_columnconfigure(0, weight=1)

        row = 0
        ctk.CTkLabel(
            self, text="Override style for this line",
            font=ctk.CTkFont(family=ff, size=13, weight="bold"),
            text_color=COLORS["text_heading"],
        ).grid(row=row, column=0, columnspan=2, padx=16, pady=(14, 8), sticky="w")
        row += 1

        # Text color
        row = self._add_color_row(row, ff, "Text Color", "primary_color")
        # Outline color
        row = self._add_color_row(row, ff, "Outline Color", "outline_color")

        # Font size
        ctk.CTkLabel(self, text="Font Size:", font=ctk.CTkFont(family=ff, size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=16, pady=(4, 0))
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.grid(row=row, column=1, sticky="ew", padx=16, pady=(4, 0))
        size_frame.grid_columnconfigure(0, weight=1)
        self.size_slider = ctk.CTkSlider(
            size_frame, from_=16, to=120, number_of_steps=104,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_size_change, height=14,
        )
        self.size_slider.set(self.style.font_size)
        self.size_slider.grid(row=0, column=0, sticky="ew")
        self.size_label = ctk.CTkLabel(
            size_frame, text=str(self.style.font_size),
            font=ctk.CTkFont(family=ff, size=11),
            text_color=COLORS["text_secondary"], width=35,
        )
        self.size_label.grid(row=0, column=1)
        row += 1

        # Bold / Italic
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 0))
        self.bold_sw = ctk.CTkSwitch(toggle_frame, text="Bold",
                                     font=ctk.CTkFont(family=ff, size=12),
                                     text_color=COLORS["text_secondary"],
                                     command=lambda: setattr(self.style, 'bold', bool(self.bold_sw.get())))
        self.bold_sw.grid(row=0, column=0, padx=(0, 16))
        if self.style.bold:
            self.bold_sw.select()

        self.italic_sw = ctk.CTkSwitch(toggle_frame, text="Italic",
                                       font=ctk.CTkFont(family=ff, size=12),
                                       text_color=COLORS["text_secondary"],
                                       command=lambda: setattr(self.style, 'italic', bool(self.italic_sw.get())))
        self.italic_sw.grid(row=0, column=1)
        if self.style.italic:
            self.italic_sw.select()
        row += 1

        # Position offset
        ctk.CTkLabel(self, text="Offset:", font=ctk.CTkFont(family=ff, size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        off_frame = ctk.CTkFrame(self, fg_color="transparent")
        off_frame.grid(row=row, column=1, sticky="ew", padx=16, pady=(6, 0))
        off_frame.grid_columnconfigure(0, weight=1)
        self.offset_slider = ctk.CTkSlider(
            off_frame, from_=-50, to=50, number_of_steps=100,
            progress_color=COLORS["accent"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], fg_color=COLORS["progress_bg"],
            command=self._on_offset_change, height=14,
        )
        self.offset_slider.set(getattr(self.style, 'position_offset', 0))
        self.offset_slider.grid(row=0, column=0, sticky="ew")
        self.offset_label = ctk.CTkLabel(
            off_frame, text=f"{getattr(self.style, 'position_offset', 0):+d}%",
            font=ctk.CTkFont(family=ff, size=11),
            text_color=COLORS["text_secondary"], width=40,
        )
        self.offset_label.grid(row=0, column=1)
        row += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(12, 14), padx=16, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame, text="Apply",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=ff, size=12),
            command=self._apply, height=30,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Cancel",
            fg_color=COLORS["button_secondary"], hover_color=COLORS["button_secondary_hover"],
            font=ctk.CTkFont(family=ff, size=12),
            text_color=COLORS["text_primary"],
            command=self.destroy, height=30,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _add_color_row(self, row: int, ff, label: str, attr: str) -> int:
        ctk.CTkLabel(self, text=f"{label}:", font=ctk.CTkFont(family=ff, size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=16, pady=(4, 0))

        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.grid(row=row, column=1, sticky="w", padx=16, pady=(4, 0))

        swatch = tk.Canvas(color_frame, width=22, height=22, highlightthickness=0, cursor="hand2")
        swatch.grid(row=0, column=0, padx=(0, 6))
        current_color = getattr(self.style, attr)
        self._draw_swatch(swatch, current_color)

        hex_label = ctk.CTkLabel(color_frame, text=current_color,
                                 font=ctk.CTkFont(family=ff, size=11),
                                 text_color=COLORS["text_secondary"])
        hex_label.grid(row=0, column=1)

        swatch.bind("<Button-1>", lambda e, a=attr, s=swatch, hl=hex_label: self._pick_color(a, s, hl))
        return row + 1

    def _draw_swatch(self, canvas, color: str):
        canvas.delete("all")
        canvas.create_oval(2, 2, 20, 20, fill=color, outline=color)
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        border = COLORS["border"][1] if isinstance(COLORS["border"], (list, tuple)) else COLORS["border"]
        bg = COLORS["bg_secondary"][1] if isinstance(COLORS["bg_secondary"], (list, tuple)) else COLORS["bg_secondary"]
        canvas.create_oval(2, 2, 20, 20, outline=border if is_dark else "#CCCCCC", width=1)
        canvas.configure(bg=bg if is_dark else "#F3F4F6")

    def _pick_color(self, attr: str, swatch, label):
        current = getattr(self.style, attr)
        result = colorchooser.askcolor(color=current, title=f"Choose {attr.replace('_', ' ').title()}")
        if result[1]:
            setattr(self.style, attr, result[1])
            self._draw_swatch(swatch, result[1])
            label.configure(text=result[1])

    def _on_size_change(self, value):
        self.style.font_size = int(value)
        self.size_label.configure(text=str(int(value)))

    def _on_offset_change(self, value):
        v = int(round(float(value)))
        self.style.position_offset = v
        self.offset_label.configure(text=f"{v:+d}%")

    def _apply(self):
        if self.subtitle_index < len(self.state.subtitles):
            self.state.subtitles[self.subtitle_index].style_override = self.style
            self.state.notify("subtitles_edited")
        self.destroy()
