import customtkinter as ctk
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family


class SubtitleList(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=0, **kwargs)
        self.state = state
        self.rows = []

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
        col_header = ctk.CTkFrame(self, fg_color=COLORS["bg_tertiary"], height=28,
                                   corner_radius=RADIUS["xs"])
        col_header.grid(row=1, column=0, sticky="ew", padx=SPACING["md"])
        col_header.grid_columnconfigure(2, weight=1)
        col_header.grid_columnconfigure(3, weight=1)

        for col, (text, w) in enumerate([("#", 30), ("TIME", 90), ("ORIGINAL", 100), ("TRANSLATION", 100)]):
            ctk.CTkLabel(
                col_header, text=text,
                font=ctk.CTkFont(family=ff, size=FONTS["caption"][1], weight="bold"),
                text_color=COLORS["text_muted"],
                width=w,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=(SPACING["sm"] if col == 0 else 0, SPACING["sm"]))

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar"],
            scrollbar_button_hover_color=COLORS["scrollbar_hover"],
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["sm"], pady=(SPACING["xs"], SPACING["sm"]))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Listen to state
        self.state.add_listener(self._on_state_change)

    def _on_state_change(self, field):
        if field == "subtitles":
            self._rebuild_list()
        elif field == "selected_subtitle":
            self._update_selection()
        elif field == "bilingual":
            self._rebuild_list()

    def _rebuild_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.rows = []

        ff = get_font_family()
        subs = self.state.subtitles
        self.count_label.configure(text=f"{len(subs)} lines")

        for i, sub in enumerate(subs):
            row_color = COLORS["row_even"] if i % 2 == 0 else COLORS["row_odd"]

            # Outer row frame
            row = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=row_color,
                corner_radius=RADIUS["xs"],
                height=40,
                cursor="hand2",
            )
            row.grid(row=i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(2, weight=1)
            row.grid_columnconfigure(3, weight=1)
            row.grid_propagate(False)

            # Selection accent strip (hidden by default)
            accent_strip = ctk.CTkFrame(row, fg_color=COLORS["accent"], width=3, corner_radius=0)
            accent_strip.grid(row=0, column=0, sticky="ns", rowspan=1)
            accent_strip.grid_remove()

            # Index
            ctk.CTkLabel(
                row, text=str(sub.index),
                font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
                text_color=COLORS["text_muted"],
                width=30, anchor="center",
            ).grid(row=0, column=1, padx=(SPACING["sm"], SPACING["xs"]))

            # Time
            time_str = f"{self._fmt(sub.start)}-{self._fmt(sub.end)}"
            ctk.CTkLabel(
                row, text=time_str,
                font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
                text_color=COLORS["text_secondary"],
                width=90, anchor="w",
            ).grid(row=0, column=2, padx=SPACING["xs"], sticky="w")

            # Original text (editable)
            orig_entry = ctk.CTkEntry(
                row,
                font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
                fg_color="transparent",
                border_width=0,
                text_color=COLORS["text_primary"],
                height=30,
            )
            orig_entry.insert(0, sub.original_text)
            orig_entry.grid(row=0, column=3, sticky="ew", padx=SPACING["xs"])
            orig_entry.bind("<FocusOut>", lambda e, idx=i: self._on_text_edit(idx, "original"))
            orig_entry.bind("<Return>", lambda e, idx=i: self._on_text_edit(idx, "original"))

            # Translation text
            if self.state.bilingual:
                trans_entry = ctk.CTkEntry(
                    row,
                    font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
                    fg_color="transparent",
                    border_width=0,
                    text_color=COLORS["accent"],
                    height=30,
                )
                trans_entry.insert(0, sub.translated_text or "")
                trans_entry.grid(row=0, column=4, sticky="ew", padx=SPACING["xs"])
                trans_entry.bind("<FocusOut>", lambda e, idx=i: self._on_text_edit(idx, "translated"))
                trans_entry.bind("<Return>", lambda e, idx=i: self._on_text_edit(idx, "translated"))

            # Row click + hover bindings on all children
            for child in row.winfo_children():
                if not isinstance(child, ctk.CTkEntry):
                    child.bind("<Button-1>", lambda e, idx=i: self._on_row_click(idx))
                child.bind("<Enter>", lambda e, idx=i: self._on_row_hover(idx, True))
                child.bind("<Leave>", lambda e, idx=i: self._on_row_hover(idx, False))

            row.bind("<Button-1>", lambda e, idx=i: self._on_row_click(idx))
            row.bind("<Enter>", lambda e, idx=i: self._on_row_hover(idx, True))
            row.bind("<Leave>", lambda e, idx=i: self._on_row_hover(idx, False))

            self.rows.append((row, accent_strip))

        self._update_selection()

    def _on_row_click(self, index):
        self.state.set_selected_subtitle(index)

    def _on_row_hover(self, index, entering):
        if index >= len(self.rows):
            return
        row, _ = self.rows[index]
        if index == self.state.selected_subtitle_index:
            return
        if entering:
            row.configure(fg_color=COLORS["row_hover"])
        else:
            color = COLORS["row_even"] if index % 2 == 0 else COLORS["row_odd"]
            row.configure(fg_color=color)

    def _on_text_edit(self, index, field):
        if index >= len(self.state.subtitles):
            return
        row, _ = self.rows[index]
        entries = [w for w in row.winfo_children() if isinstance(w, ctk.CTkEntry)]
        if field == "original" and entries:
            self.state.subtitles[index].original_text = entries[0].get()
        elif field == "translated" and len(entries) > 1:
            self.state.subtitles[index].translated_text = entries[1].get()
        self.state.notify("subtitles_edited")

    def _update_selection(self):
        sel = self.state.selected_subtitle_index
        for i, (row, accent_strip) in enumerate(self.rows):
            if i == sel:
                row.configure(fg_color=COLORS["row_selected"])
                accent_strip.grid()
            else:
                color = COLORS["row_even"] if i % 2 == 0 else COLORS["row_odd"]
                row.configure(fg_color=color)
                accent_strip.grid_remove()

    @staticmethod
    def _fmt(seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
