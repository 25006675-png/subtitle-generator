import customtkinter as ctk
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family
from core.transcriber import Transcriber, AVAILABLE_MODELS
from core.cloud_transcriber import CloudTranscriber
from core.subtitle_model import SubtitleEntry, WordEntry
from core.config import load_config, save_config


class TranscribePanel(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.transcriber = Transcriber()
        self.cloud_transcriber = CloudTranscriber()
        self._loading_dots = 0
        self._loading_after_id = None

        self.grid_columnconfigure(0, weight=1)

        ff = get_font_family()

        # Check pyannote availability once, used by the speakers toggle
        self._has_pyannote = False
        try:
            import pyannote.audio
            self._has_pyannote = True
        except ImportError:
            pass

        # Title
        ctk.CTkLabel(
            self, text="Transcribe & Translate",
            font=ctk.CTkFont(family=ff, size=FONTS["display"][1], weight="bold"),
            text_color=COLORS["text_heading"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # --- Transcription Section ---
        trans_section = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"],
                                      border_width=2, border_color=COLORS["accent_muted"])
        trans_section.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        trans_section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            trans_section, text="Speech to Text",
            font=ctk.CTkFont(family=FONTS["subheading"][0], size=FONTS["subheading"][1]),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        # --- Provider selector (Feature 2) ---
        provider_frame = ctk.CTkFrame(trans_section, fg_color="transparent")
        provider_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        provider_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            provider_frame, text="Provider:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.provider_var = ctk.StringVar(value="Local (Free)")
        self.provider_selector = ctk.CTkSegmentedButton(
            provider_frame,
            values=["Local (Free)", "Groq (Cloud)", "OpenAI (Cloud)"],
            variable=self.provider_var,
            font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_provider_change,
        )
        self.provider_selector.grid(row=0, column=1, sticky="ew")

        # --- API Key frame (hidden for local) ---
        self.api_key_frame = ctk.CTkFrame(trans_section, fg_color="transparent")
        self.api_key_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        self.api_key_frame.grid_columnconfigure(1, weight=1)
        self.api_key_frame.grid_remove()  # Hidden by default

        ctk.CTkLabel(
            self.api_key_frame, text="API Key:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.api_key_entry = ctk.CTkEntry(
            self.api_key_frame,
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
            show="*", height=30,
        )
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])

        self.save_key_btn = ctk.CTkButton(
            self.api_key_frame, text="Save",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["button_secondary"],
            hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            height=30, width=60,
            command=self._save_api_key,
            cursor="hand2",
        )
        self.save_key_btn.grid(row=0, column=2, padx=SPACING["xs"])

        # Model selector (only for local)
        model_frame = ctk.CTkFrame(trans_section, fg_color="transparent")
        model_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["lg"])
        model_frame.grid_columnconfigure(1, weight=1)
        self.model_frame = model_frame

        ctk.CTkLabel(
            model_frame, text="Model:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.model_var = ctk.StringVar(value="base")
        self.model_selector = ctk.CTkSegmentedButton(
            model_frame,
            values=AVAILABLE_MODELS,
            variable=self.model_var,
            font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
        )
        self.model_selector.grid(row=0, column=1, sticky="ew")

        # --- Detect Speakers toggle ---
        speakers_row = ctk.CTkFrame(trans_section, fg_color="transparent")
        speakers_row.grid(row=4, column=0, sticky="ew", padx=SPACING["lg"], pady=(SPACING["sm"], 0))
        speakers_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            speakers_row, text="Speakers:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.detect_speakers_switch = ctk.CTkSwitch(
            speakers_row,
            text="Detect after transcription" if self._has_pyannote else "Detect after transcription (install pyannote.audio)",
            font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"] if self._has_pyannote else COLORS["text_muted"],
            state="normal" if self._has_pyannote else "disabled",
        )
        self.detect_speakers_switch.grid(row=0, column=1, sticky="w")

        # Transcribe button + progress
        action_frame = ctk.CTkFrame(trans_section, fg_color="transparent")
        action_frame.grid(row=5, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        action_frame.grid_columnconfigure(1, weight=1)

        self.transcribe_btn = ctk.CTkButton(
            action_frame,
            text="Transcribe",
            font=ctk.CTkFont(family=FONTS["body_bold"][0], size=FONTS["body_bold"][1]),
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_primary_hover"],
            text_color=COLORS["button_text"],
            corner_radius=RADIUS["md"],
            height=38,
            width=130,
            command=self._start_transcription,
            cursor="hand2",
        )
        self.transcribe_btn.grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.trans_progress = ctk.CTkProgressBar(
            action_frame,
            progress_color=COLORS["progress_fill"],
            fg_color=COLORS["progress_bg"],
            height=12,
            corner_radius=6,
        )
        self.trans_progress.grid(row=0, column=1, sticky="ew")
        self.trans_progress.set(0)

        self.trans_pct_label = ctk.CTkLabel(
            action_frame, text="0%",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
            width=36,
        )
        self.trans_pct_label.grid(row=0, column=2, padx=(SPACING["xs"], 0))

        self.trans_status = ctk.CTkLabel(
            trans_section, text="",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.trans_status.grid(row=6, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # --- Language Setting ---
        source_frame = ctk.CTkFrame(trans_section, fg_color="transparent")
        source_frame.grid(row=7, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        source_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            source_frame, text="Spoken:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.source_lang_var = ctk.StringVar(value="Auto Detect")
        self.source_lang_dropdown = ctk.CTkComboBox(
            source_frame,
            values=["Auto Detect", "English", "Malay", "Chinese", "Japanese", "French", "German", "Spanish"],
            variable=self.source_lang_var,
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            dropdown_font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            fg_color=COLORS["entry_bg"],
            border_color=COLORS["entry_border"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"],
            height=32,
            state="readonly",
        )
        self.source_lang_dropdown.grid(row=0, column=1, sticky="ew")

        # --- Translation Section ---
        translate_section = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"],
                                          border_width=2, border_color=COLORS["accent_muted"])
        translate_section.grid(row=3, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        translate_section.grid_columnconfigure(0, weight=1)

        # Bilingual toggle
        bi_frame = ctk.CTkFrame(translate_section, fg_color="transparent")
        bi_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))
        bi_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bi_frame, text="Translation",
            font=ctk.CTkFont(family=FONTS["subheading"][0], size=FONTS["subheading"][1]),
            text_color=COLORS["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        self.bilingual_switch = ctk.CTkSwitch(
            bi_frame,
            text="Enable",
            font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            text_color=COLORS["text_secondary"],
            command=self._toggle_bilingual,
        )
        self.bilingual_switch.grid(row=0, column=1, sticky="e")

        # Language selector
        lang_frame = ctk.CTkFrame(translate_section, fg_color="transparent")
        lang_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"])
        lang_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            lang_frame, text="Target:",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        from core.translator import LANGUAGES
        self.lang_var = ctk.StringVar(value="Japanese")
        self.lang_dropdown = ctk.CTkComboBox(
            lang_frame,
            values=LANGUAGES,
            variable=self.lang_var,
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            dropdown_font=ctk.CTkFont(family=FONTS["small"][0], size=FONTS["small"][1]),
            fg_color=COLORS["entry_bg"],
            border_color=COLORS["entry_border"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"],
            height=32,
            state="readonly",
        )
        self.lang_dropdown.grid(row=0, column=1, sticky="ew")

        # Translate button + progress
        t_action = ctk.CTkFrame(translate_section, fg_color="transparent")
        t_action.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["md"])
        t_action.grid_columnconfigure(1, weight=1)

        self.translate_btn = ctk.CTkButton(
            t_action,
            text="Translate",
            font=ctk.CTkFont(family=FONTS["body_bold"][0], size=FONTS["body_bold"][1]),
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_primary_hover"],
            text_color=COLORS["button_text"],
            corner_radius=RADIUS["md"],
            height=38,
            width=130,
            command=self._start_translation,
            cursor="hand2",
        )
        self.translate_btn.grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.tl_progress = ctk.CTkProgressBar(
            t_action,
            progress_color=COLORS["progress_fill"],
            fg_color=COLORS["progress_bg"],
            height=12,
            corner_radius=6,
        )
        self.tl_progress.grid(row=0, column=1, sticky="ew")
        self.tl_progress.set(0)

        self.tl_pct_label = ctk.CTkLabel(
            t_action, text="0%",
            font=ctk.CTkFont(family=ff, size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
            width=36,
        )
        self.tl_pct_label.grid(row=0, column=2, padx=(SPACING["xs"], 0))

        self.tl_status = ctk.CTkLabel(
            translate_section, text="",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.tl_status.grid(row=3, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["md"]))

    def _on_provider_change(self, value):
        provider_map = {
            "Local (Free)": "local",
            "Groq (Cloud)": "groq",
            "OpenAI (Cloud)": "openai",
        }
        provider = provider_map.get(value, "local")
        self.state.set_transcription_provider(provider)

        if provider == "local":
            self.api_key_frame.grid_remove()
            self.model_frame.grid()
        else:
            self.model_frame.grid_remove()
            self.api_key_frame.grid()
            # Load saved key
            config = load_config()
            key_field = "groq_api_key" if provider == "groq" else "openai_api_key"
            saved_key = config.get(key_field, "")
            self.api_key_entry.delete(0, "end")
            if saved_key:
                self.api_key_entry.insert(0, saved_key)

    def _save_api_key(self):
        provider = self.state.transcription_provider
        key = self.api_key_entry.get().strip()
        if not key:
            return
        config = load_config()
        key_field = "groq_api_key" if provider == "groq" else "openai_api_key"
        config[key_field] = key
        save_config(config)

    def _start_transcription(self):
        if not self.state.video_path:
            self.trans_status.configure(text="No video loaded.", text_color=COLORS["error"])
            return
        if self.state.is_transcribing:
            return

        self.state.is_transcribing = True
        self.transcribe_btn.configure(state="disabled", text="Transcribing")
        self.trans_progress.set(0)
        self.trans_pct_label.configure(text="0%")
        self.trans_status.configure(text="Loading model...", text_color=COLORS["text_muted"])
        self._start_loading_animation(self.transcribe_btn, "Transcribing")

        # Determine language code
        lang_map = {
            "Auto Detect": None,
            "English": "en",
            "Malay": "ms",
            "Chinese": "zh",
            "Japanese": "ja",
            "French": "fr",
            "German": "de",
            "Spanish": "es",
        }
        selected_lang = lang_map.get(self.source_lang_var.get())
        use_word_timestamps = True

        def on_progress(p):
            self.after(0, lambda: self._update_trans_progress(p))

        def on_complete(results):
            self.after(0, lambda: self._on_transcription_done(results))

        def on_error(msg):
            self.after(0, lambda: self._on_transcription_error(msg))

        provider = self.state.transcription_provider

        if provider == "local":
            model_size = self.model_var.get()
            self.transcriber.model_size = model_size
            self.transcriber.transcribe(
                self.state.video_path,
                language=selected_lang,
                word_timestamps=use_word_timestamps,
                on_progress=on_progress,
                on_complete=on_complete,
                on_error=on_error,
            )
        else:
            # Cloud transcription
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                config = load_config()
                key_field = "groq_api_key" if provider == "groq" else "openai_api_key"
                api_key = config.get(key_field, "")

            if not api_key:
                self._on_transcription_error(f"No API key set for {provider}. Enter and save your key first.")
                return

            self.trans_status.configure(text="Extracting audio & uploading...", text_color=COLORS["text_muted"])
            self.cloud_transcriber.transcribe(
                self.state.video_path,
                provider=provider,
                api_key=api_key,
                language=selected_lang,
                word_timestamps=use_word_timestamps,
                on_progress=on_progress,
                on_complete=on_complete,
                on_error=on_error,
            )

    def _update_trans_progress(self, p):
        self.trans_progress.set(p)
        pct = int(p * 100)
        self.trans_pct_label.configure(text=f"{pct}%")
        self.trans_status.configure(text=f"Transcribing... {pct}%")

    def _on_transcription_done(self, results):
        entries = []
        for r in results:
            original_text = (r.get("text") or "").strip()
            if not original_text and r.get("words"):
                original_text = " ".join((w.get("word") or "").strip() for w in r["words"]).strip()

            entry = SubtitleEntry(
                index=r["index"],
                start=r["start"],
                end=r["end"],
                original_text=original_text,
            )
            # Populate word entries if available (Feature 3)
            if "words" in r and r["words"]:
                entry.words = [
                    WordEntry(word=w["word"], start=w["start"], end=w["end"])
                    for w in r["words"]
                ]
            entries.append(entry)

        self.state.set_subtitles(entries)

        if not entries:
            self.trans_status.configure(text="No speech detected in this video.", text_color=COLORS["error"])
            self._finish_transcription_flow()
            return

        # Chain to diarization if toggle is on
        if self.detect_speakers_switch.get() and self._has_pyannote:
            self.trans_status.configure(
                text=f"{len(entries)} segments found. Detecting speakers...",
                text_color=COLORS["text_muted"],
            )
            self.trans_progress.set(0)
            self.trans_pct_label.configure(text="0%")
            self._run_diarization()
        else:
            self.trans_status.configure(text=f"Done! {len(entries)} segments found.", text_color=COLORS["success"])
            self._finish_transcription_flow()

    def _finish_transcription_flow(self):
        self.state.is_transcribing = False
        self._stop_loading_animation()
        self.transcribe_btn.configure(state="normal", text="Transcribe")
        self.trans_progress.set(1.0)
        self.trans_pct_label.configure(text="100%")

    def _on_transcription_error(self, msg):
        self.state.is_transcribing = False
        self._stop_loading_animation()
        self.transcribe_btn.configure(state="normal", text="Transcribe")
        if "SSL" in msg or "connection" in msg.lower():
            self.trans_status.configure(text=f"Connection Error: {msg[:60]}...", text_color=COLORS["error"])
        else:
            self.trans_status.configure(text=f"Error: {msg}", text_color=COLORS["error"])

    def _run_diarization(self):
        from core.config import HF_TOKEN
        from core.diarizer import Diarizer

        self.state.is_diarizing = True
        self.state.hf_token = HF_TOKEN
        diarizer = Diarizer()

        def on_progress(p):
            self.after(0, lambda: self._update_diarize_progress(p))

        def on_complete(result):
            self.after(0, lambda: self._on_diarization_done(result))

        def on_error(msg):
            self.after(0, lambda: self._on_diarization_error(msg))

        diarizer.diarize(
            self.state.video_path,
            hf_token=HF_TOKEN,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        )

    def _update_diarize_progress(self, p):
        self.trans_progress.set(p)
        pct = int(p * 100)
        self.trans_pct_label.configure(text=f"{pct}%")
        self.trans_status.configure(text=f"Detecting speakers... {pct}%")

    def _on_diarization_done(self, diarization_segments):
        from core.diarizer import assign_speakers_to_subtitles
        from core.subtitle_model import SpeakerInfo, SubtitleStyle

        assign_speakers_to_subtitles(self.state.subtitles, diarization_segments)

        speaker_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                          "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
        unique_speakers = sorted(set(s.speaker_id for s in self.state.subtitles if s.speaker_id))
        speakers = {}
        for i, spk_id in enumerate(unique_speakers):
            color = speaker_colors[i % len(speaker_colors)]
            speakers[spk_id] = SpeakerInfo(
                id=spk_id,
                display_name=spk_id,
                style=SubtitleStyle(primary_color=color),
            )

        self.state.set_speakers(speakers)
        self.state.is_diarizing = False
        self.state.notify("subtitles")
        self.trans_status.configure(
            text=f"Done! {len(self.state.subtitles)} segments, {len(unique_speakers)} speakers detected.",
            text_color=COLORS["success"],
        )
        self._finish_transcription_flow()

    def _on_diarization_error(self, msg):
        self.state.is_diarizing = False
        self.trans_status.configure(text=f"Speaker detection failed: {msg}", text_color=COLORS["error"])
        self._finish_transcription_flow()

    def _toggle_bilingual(self):
        enabled = bool(self.bilingual_switch.get())
        self.state.set_bilingual(enabled)

    def _start_translation(self):
        if not self.state.subtitles:
            self.tl_status.configure(text="No subtitles to translate.", text_color=COLORS["error"])
            return
        if self.state.is_translating:
            return

        self.state.is_translating = True
        self.state.target_language = self.lang_var.get()
        self.translate_btn.configure(state="disabled", text="Translating")
        self.tl_progress.set(0)
        self.tl_pct_label.configure(text="0%")
        self.tl_status.configure(text="Sending to Gemini...", text_color=COLORS["text_muted"])
        self._start_loading_animation(self.translate_btn, "Translating")

        # Enable bilingual if not already
        if not self.state.bilingual:
            self.bilingual_switch.select()
            self.state.set_bilingual(True)

        from core.translator import Translator
        translator = Translator()

        def on_progress(p):
            self.after(0, lambda: self._update_tl_progress(p))

        def on_complete(translations):
            self.after(0, lambda: self._on_translation_done(translations))

        def on_error(msg):
            self.after(0, lambda: self._on_translation_error(msg))

        translator.translate(
            self.state.subtitles,
            self.state.target_language,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        )

    def _update_tl_progress(self, p):
        self.tl_progress.set(p)
        pct = int(p * 100)
        self.tl_pct_label.configure(text=f"{pct}%")
        self.tl_status.configure(text=f"Translating... {pct}%")

    def _on_translation_done(self, translations):
        for sub in self.state.subtitles:
            if sub.index in translations:
                sub.translated_text = translations[sub.index]
        self.state.notify("subtitles")
        self.state.is_translating = False
        self._stop_loading_animation()
        self.translate_btn.configure(state="normal", text="Translate")
        self.tl_progress.set(1.0)
        self.tl_pct_label.configure(text="100%")
        self.tl_status.configure(
            text=f"Done! {len(translations)} lines translated.",
            text_color=COLORS["success"],
        )

    def _on_translation_error(self, msg):
        self.state.is_translating = False
        self._stop_loading_animation()
        self.translate_btn.configure(state="normal", text="Translate")
        self.tl_status.configure(text=f"Error: {msg}", text_color=COLORS["error"])

    def _start_loading_animation(self, btn, base_text):
        self._loading_dots = 0
        self._loading_btn = btn
        self._loading_base = base_text
        self._tick_loading()

    def _tick_loading(self):
        if not (self.state.is_transcribing or self.state.is_translating or self.state.is_diarizing):
            return
        dots = "." * (self._loading_dots % 4)
        self._loading_btn.configure(text=f"{self._loading_base}{dots}")
        self._loading_dots += 1
        self._loading_after_id = self.after(400, self._tick_loading)

    def _stop_loading_animation(self):
        if self._loading_after_id is not None:
            try:
                self.after_cancel(self._loading_after_id)
            except Exception:
                pass
            self._loading_after_id = None
