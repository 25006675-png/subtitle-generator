import customtkinter as ctk
from app.theme import COLORS, FONTS, SPACING, RADIUS, get_font_family
from core.config import load_config, save_config
from core.transcriber import AVAILABLE_MODELS


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.grid_columnconfigure(0, weight=1)
        ff = get_font_family()

        # Title
        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(family=ff, size=FONTS["display"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # ── Transcription section ────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["card"])
        card.grid(row=1, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Transcription",
            font=ctk.CTkFont(family=ff, size=FONTS["subheading"][1], weight="bold"),
            text_color=COLORS["text_heading"], anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        self.transcription_note_label = ctk.CTkLabel(
            card,
            text="Base is the default local model for speed. Move up to a larger local model or use your own cloud API when you need better accuracy.",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            text_color=COLORS["text_muted"],
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self.transcription_note_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        card.bind(
            "<Configure>",
            lambda event, label=self.transcription_note_label: label.configure(wraplength=max(260, event.width - (SPACING["lg"] * 2))),
            add="+",
        )

        # Provider selector
        ctk.CTkLabel(
            card, text="Provider:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(0, SPACING["sm"]))

        self._provider_map = {"Local (Free)": "local", "Groq (Cloud)": "groq", "OpenAI (Cloud)": "openai"}
        self._provider_rev = {v: k for k, v in self._provider_map.items()}
        self.provider_var = ctk.StringVar(value=self._provider_rev.get(state.transcription_provider, "Local (Free)"))
        ctk.CTkSegmentedButton(
            card,
            values=list(self._provider_map.keys()),
            variable=self.provider_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self._on_provider_change,
        ).grid(row=2, column=1, sticky="ew", padx=(0, SPACING["lg"]), pady=(0, SPACING["sm"]))

        # Model row (local only)
        self.model_row = ctk.CTkFrame(card, fg_color="transparent")
        self.model_row.grid(row=3, column=0, columnspan=2, sticky="ew",
                            padx=SPACING["lg"], pady=(0, SPACING["sm"]))
        self.model_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.model_row, text="Model:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.model_var = ctk.StringVar(value=state.whisper_model)
        ctk.CTkSegmentedButton(
            self.model_row,
            values=AVAILABLE_MODELS,
            variable=self.model_var,
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=lambda v: state.set_whisper_model(v),
        ).grid(row=0, column=1, sticky="ew")

        # API key row (hidden for local)
        self.api_row = ctk.CTkFrame(card, fg_color="transparent")
        self.api_row.grid(row=4, column=0, columnspan=2, sticky="ew",
                          padx=SPACING["lg"], pady=(0, SPACING["md"]))
        self.api_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.api_row, text="API Key:",
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, SPACING["md"]))

        self.api_entry = ctk.CTkEntry(
            self.api_row,
            font=ctk.CTkFont(family=ff, size=FONTS["body"][1]),
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"],
            show="*", height=32,
            placeholder_text="Paste your API key here…",
        )
        self.api_entry.grid(row=0, column=1, sticky="ew", padx=SPACING["xs"])

        ctk.CTkButton(
            self.api_row, text="Save",
            font=ctk.CTkFont(family=ff, size=FONTS["small"][1]),
            fg_color=COLORS["button_secondary"], hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            height=32, width=64, cursor="hand2",
            command=self._save_api_key,
        ).grid(row=0, column=2, padx=(SPACING["xs"], 0))

        # Show/hide api_row based on current provider
        self._refresh_api_row(state.transcription_provider)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _on_provider_change(self, value):
        provider = self._provider_map.get(value, "local")
        self.state.set_transcription_provider(provider)
        self._refresh_api_row(provider)

    def _refresh_api_row(self, provider: str):
        if provider == "local":
            self.model_row.grid()
            self.api_row.grid_remove()
        else:
            self.model_row.grid_remove()
            self.api_row.grid()
            config = load_config()
            key_field = "groq_api_key" if provider == "groq" else "openai_api_key"
            saved = config.get(key_field, "")
            self.api_entry.delete(0, "end")
            if saved:
                self.api_entry.insert(0, saved)

    def _save_api_key(self):
        provider = self.state.transcription_provider
        key = self.api_entry.get().strip()
        if not key:
            return
        config = load_config()
        key_field = "groq_api_key" if provider == "groq" else "openai_api_key"
        config[key_field] = key
        save_config(config)
