import customtkinter as ctk
import os
from tkinter import filedialog
from app.theme import COLORS, FONTS, SPACING, RADIUS, IconRenderer, get_font_family
from export.srt_writer import write_srt
from export.ass_writer import write_ass
from export.ffmpeg_burner import check_ffmpeg, burn_subtitles, QUALITY_PRESETS


class ExportPanel(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state

        self.grid_columnconfigure(0, weight=1)

        ff = get_font_family()

        # Title
        ctk.CTkLabel(
            self, text="Export",
            font=ctk.CTkFont(family=ff, size=FONTS["display"][1], weight="bold"),
            text_color=COLORS["text_heading"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # --- Subtitle Export Section ---
        sub_section = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        sub_section.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        sub_section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sub_section, text="Export Subtitle Files",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        # Format checkboxes
        fmt_frame = ctk.CTkFrame(sub_section, fg_color="transparent")
        fmt_frame.grid(row=1, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        self.srt_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            fmt_frame, text="SRT", variable=self.srt_var,
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            checkmark_color=COLORS["button_text"],
        ).grid(row=0, column=0, padx=(0, SPACING["xl"]))

        self.ass_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            fmt_frame, text="ASS (styled)", variable=self.ass_var,
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            checkmark_color=COLORS["button_text"],
        ).grid(row=0, column=1)

        # Bilingual option
        self.bilingual_export_var = ctk.BooleanVar(value=True)
        self.bilingual_check = ctk.CTkCheckBox(
            sub_section, text="Include translations (bilingual)", variable=self.bilingual_export_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            checkmark_color=COLORS["button_text"],
        )
        self.bilingual_check.grid(row=2, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # Export button with download icon
        btn_frame = ctk.CTkFrame(sub_section, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        self._download_icon = IconRenderer.get_colored("download", 16, "#FFFFFF")

        self.export_btn = ctk.CTkButton(
            btn_frame,
            text="Export Subtitles",
            image=self._download_icon,
            compound="left",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_primary_hover"],
            text_color=COLORS["button_text"],
            corner_radius=RADIUS["md"],
            height=38, width=180,
            command=self._export_subtitles,
            cursor="hand2",
        )
        self.export_btn.grid(row=0, column=0)

        self.export_status = ctk.CTkLabel(
            btn_frame, text="",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_muted"],
        )
        self.export_status.grid(row=0, column=1, padx=SPACING["md"])

        # --- FFmpeg Burn-in Section ---
        burn_section = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        burn_section.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        burn_section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            burn_section, text="Burn Subtitles into Video",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        # FFmpeg status badge (pill-shaped)
        ffmpeg_ok = check_ffmpeg()
        badge_text = "FFmpeg Found" if ffmpeg_ok else "FFmpeg Not Found"
        badge_color = COLORS["success"] if ffmpeg_ok else COLORS["warning"]

        self.ffmpeg_badge = ctk.CTkLabel(
            burn_section,
            text=f"  {badge_text}  ",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1], weight="bold"),
            text_color=COLORS["button_text"] if ffmpeg_ok else ("#000000", "#000000"),
            fg_color=badge_color,
            corner_radius=RADIUS["pill"],
            height=22,
        )
        self.ffmpeg_badge.grid(row=1, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # Quality preset
        q_frame = ctk.CTkFrame(burn_section, fg_color="transparent")
        q_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"])
        q_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            q_frame, text="Quality:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.quality_var = ctk.StringVar(value="Medium (balanced)")
        self.quality_dropdown = ctk.CTkComboBox(
            q_frame, values=list(QUALITY_PRESETS.keys()),
            variable=self.quality_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["sm"], height=30,
            state="readonly",
        )
        self.quality_dropdown.grid(row=0, column=1, sticky="ew")

        # Burn button + progress
        burn_action = ctk.CTkFrame(burn_section, fg_color="transparent")
        burn_action.grid(row=3, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        burn_action.grid_columnconfigure(1, weight=1)

        self.burn_btn = ctk.CTkButton(
            burn_action,
            text="Burn into Video",
            image=self._download_icon,
            compound="left",
            font=ctk.CTkFont(family=ff, size=FONTS["body_bold"][1], weight="bold"),
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_primary_hover"],
            text_color=COLORS["button_text"],
            corner_radius=RADIUS["md"],
            height=38, width=180,
            command=self._start_burn,
            cursor="hand2",
            state="normal" if ffmpeg_ok else "disabled",
        )
        self.burn_btn.grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.burn_progress = ctk.CTkProgressBar(
            burn_action,
            progress_color=COLORS["progress_fill"],
            fg_color=COLORS["progress_bg"],
            height=12, corner_radius=6,
        )
        self.burn_progress.grid(row=0, column=1, sticky="ew")
        self.burn_progress.set(0)

        self.burn_pct_label = ctk.CTkLabel(
            burn_action, text="0%",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
            width=36,
        )
        self.burn_pct_label.grid(row=0, column=2, padx=(SPACING["xs"], 0))

        self.burn_status = ctk.CTkLabel(
            burn_section, text="",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_muted"], anchor="w",
        )
        self.burn_status.grid(row=4, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["md"]))

    def _export_subtitles(self):
        if not self.state.subtitles:
            self.export_status.configure(text="No subtitles to export.", text_color=COLORS["error"])
            return

        out_dir = filedialog.askdirectory(title="Select Export Folder")
        if not out_dir:
            return

        base_name = os.path.splitext(self.state.video_info.get("filename", "subtitles"))[0]
        bilingual = self.state.bilingual and self.bilingual_export_var.get()
        exported = []

        if self.srt_var.get():
            srt_path = os.path.join(out_dir, f"{base_name}.srt")
            write_srt(self.state.subtitles, srt_path, bilingual=bilingual)
            exported.append("SRT")

        if self.ass_var.get():
            ass_path = os.path.join(out_dir, f"{base_name}.ass")
            write_ass(
                self.state.subtitles, ass_path,
                primary_style=self.state.primary_style,
                secondary_style=self.state.secondary_style if bilingual else None,
                bilingual=bilingual,
            )
            exported.append("ASS")

        if exported:
            self.export_status.configure(
                text=f"Exported: {', '.join(exported)} to {out_dir}",
                text_color=COLORS["success"],
            )
        else:
            self.export_status.configure(text="No formats selected.", text_color=COLORS["warning"])

    def _start_burn(self):
        if not self.state.subtitles or not self.state.video_path:
            self.burn_status.configure(text="Need video and subtitles.", text_color=COLORS["error"])
            return
        if self.state.is_burning:
            return

        import tempfile
        tmp_ass = os.path.join(tempfile.gettempdir(), "subtitle_burn_temp.ass")
        bilingual = self.state.bilingual and self.bilingual_export_var.get()
        write_ass(
            self.state.subtitles, tmp_ass,
            primary_style=self.state.primary_style,
            secondary_style=self.state.secondary_style if bilingual else None,
            bilingual=bilingual,
        )

        base = os.path.splitext(self.state.video_path)[0]
        output_path = filedialog.asksaveasfilename(
            title="Save Video With Subtitles",
            initialfile=f"{os.path.basename(base)}_subtitled.mp4",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("All files", "*.*")],
        )
        if not output_path:
            return

        self.state.is_burning = True
        self.burn_btn.configure(state="disabled", text="Burning...")
        self.burn_progress.set(0)
        self.burn_pct_label.configure(text="0%")
        self.burn_status.configure(text="Starting FFmpeg...", text_color=COLORS["text_muted"])

        def on_progress(p):
            self.after(0, lambda: self._update_burn_progress(p))

        def on_complete(path):
            self.after(0, lambda: self._on_burn_done(path))

        def on_error(msg):
            self.after(0, lambda: self._on_burn_error(msg))

        burn_subtitles(
            self.state.video_path, tmp_ass, output_path,
            quality_preset=self.quality_var.get(),
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        )

    def _update_burn_progress(self, p):
        self.burn_progress.set(p)
        pct = int(p * 100)
        self.burn_pct_label.configure(text=f"{pct}%")
        self.burn_status.configure(text=f"Burning... {pct}%")

    def _on_burn_done(self, path):
        self.state.is_burning = False
        self.burn_btn.configure(state="normal", text="Burn into Video")
        self.burn_progress.set(1.0)
        self.burn_pct_label.configure(text="100%")
        self.burn_status.configure(
            text=f"Done! Saved to {os.path.basename(path)}",
            text_color=COLORS["success"],
        )

    def _on_burn_error(self, msg):
        self.state.is_burning = False
        self.burn_btn.configure(state="normal", text="Burn into Video")
        self.burn_status.configure(text=f"Error: {msg}", text_color=COLORS["error"])
