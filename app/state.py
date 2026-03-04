from dataclasses import dataclass, field
from typing import Callable
from core.subtitle_model import SubtitleEntry, SubtitleStyle, SpeakerInfo


@dataclass
class AppState:
    # Video
    video_path: str = ""
    video_info: dict = field(default_factory=dict)

    # Subtitles
    subtitles: list[SubtitleEntry] = field(default_factory=list)
    selected_subtitle_index: int = -1

    # Styles
    primary_style: SubtitleStyle = field(default_factory=SubtitleStyle)
    secondary_style: SubtitleStyle = field(
        default_factory=lambda: SubtitleStyle(
            primary_color="#FFD700",
            position="bottom",
            font_size=36,
        )
    )

    # Translation
    bilingual: bool = False
    secondary_on_top: bool = False
    target_language: str = "Japanese"

    # Navigation
    current_step: int = 0  # 0-3

    # Processing flags
    is_transcribing: bool = False
    transcribe_progress: float = 0.0
    is_translating: bool = False
    translate_progress: float = 0.0
    is_burning: bool = False
    burn_progress: float = 0.0

    # Preview
    preview_time: float = 0.0

    # Feature 2: Cloud Transcription
    transcription_provider: str = "local"  # "local", "groq", "openai"

    # Feature 3: Karaoke
    karaoke_mode: str = "off"  # "off", "word_by_word", "classic", "popup"
    animation_style: str = "none"  # "none", "fade", "pop", "slide_up", "typewriter"
    karaoke_highlight_color: str = "#FFFF00"
    transition_duration: float = 0.30      # fade/pop/slide in-duration seconds (0.05-1.0)
    classic_dimmed_opacity: float = 0.5    # unspoken-word opacity in Classic mode (0.1-0.9)
    popup_scale: float = 1.5               # Pop-up word scale multiplier (1.0-2.5)
    popup_trail_count: int = 3             # Pop-up trailing words shown (0-5)
    wordbyw_entry_style: str = "instant"   # "instant", "fade", "pop"
    wordbyw_history_style: str = "full"    # "full", "dimmed"
    classic_active_marker: str = "color"   # "color" | "box" | "color_box"
    classic_history_on: bool = False        # mirror active marker for spoken words

    # Feature 4: Multi-Speaker
    speakers: dict = field(default_factory=dict)  # {speaker_id: SpeakerInfo}
    is_diarizing: bool = False
    diarize_progress: float = 0.0
    hf_token: str = ""

    # Observer
    _listeners: list[Callable] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        self._listeners = [l for l in self._listeners if l is not callback]

    def notify(self, field_name: str):
        for listener in self._listeners:
            try:
                listener(field_name)
            except Exception:
                pass

    def set_video(self, path: str, info: dict):
        self.video_path = path
        self.video_info = info
        self.subtitles = []
        self.selected_subtitle_index = -1
        self.preview_time = 0.0
        self.speakers = {}
        self.notify("video")

    def set_subtitles(self, subs: list[SubtitleEntry]):
        self.subtitles = subs
        self.selected_subtitle_index = 0 if subs else -1
        self.notify("subtitles")

    def set_selected_subtitle(self, index: int):
        if 0 <= index < len(self.subtitles):
            self.selected_subtitle_index = index
            self.preview_time = self.subtitles[index].start
            self.notify("selected_subtitle")

    def set_step(self, step: int):
        self.current_step = step
        self.notify("step")

    def set_preview_time(self, t: float):
        self.preview_time = t
        self.notify("preview_time")

    def get_subtitle_at_time(self, t: float) -> SubtitleEntry | None:
        for sub in self.subtitles:
            if sub.start <= t <= sub.end:
                return sub
        return None

    def update_primary_style(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.primary_style, k):
                setattr(self.primary_style, k, v)
        self.notify("style")

    def update_secondary_style(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.secondary_style, k):
                setattr(self.secondary_style, k, v)
        self.notify("style")

    def set_bilingual(self, enabled: bool):
        self.bilingual = enabled
        self.notify("bilingual")

    def toggle_secondary_on_top(self):
        self.secondary_on_top = not self.secondary_on_top
        self.notify("bilingual")

    # Feature 2: Cloud Transcription
    def set_transcription_provider(self, provider: str):
        self.transcription_provider = provider
        self.notify("transcription_provider")

    # Feature 3: Karaoke
    def set_karaoke_mode(self, mode: str):
        self.karaoke_mode = mode
        self.notify("karaoke_mode")

    def set_animation_style(self, style: str):
        self.animation_style = style
        self.notify("animation_style")

    def set_karaoke_highlight_color(self, color: str):
        self.karaoke_highlight_color = color
        self.notify("karaoke_highlight_color")

    def set_transition_duration(self, v):
        self.transition_duration = max(0.05, min(1.0, float(v)))
        self.notify("transition_duration")

    def set_classic_dimmed_opacity(self, v):
        self.classic_dimmed_opacity = max(0.1, min(0.9, float(v)))
        self.notify("classic_dimmed_opacity")

    def set_popup_scale(self, v):
        self.popup_scale = max(1.0, min(2.5, float(v)))
        self.notify("popup_scale")

    def set_popup_trail_count(self, v):
        self.popup_trail_count = max(0, min(5, int(v)))
        self.notify("popup_trail_count")

    def set_wordbyw_entry_style(self, v: str):
        if v in ("instant", "fade", "pop"):
            self.wordbyw_entry_style = v
            self.notify("wordbyw_entry_style")

    def set_wordbyw_history_style(self, v: str):
        if v in ("full", "dimmed"):
            self.wordbyw_history_style = v
            self.notify("wordbyw_history_style")

    def set_classic_active_marker(self, v: str):
        if v in ("color", "box", "color_box"):
            self.classic_active_marker = v
            self.notify("classic_active_marker")

    def set_classic_history_on(self, v: bool):
        self.classic_history_on = bool(v)
        self.notify("classic_history_on")

    def get_word_at_time(self, t: float):
        """Returns (SubtitleEntry, word_index) or (None, -1)."""
        sub = self.get_subtitle_at_time(t)
        if sub and sub.words:
            for i, w in enumerate(sub.words):
                if w.start <= t <= w.end:
                    return sub, i
            # If between words, find closest
            for i, w in enumerate(sub.words):
                if t < w.start:
                    return sub, max(0, i - 1)
            return sub, len(sub.words) - 1
        return None, -1

    # Feature 4: Multi-Speaker
    def set_speakers(self, speakers: dict):
        self.speakers = speakers
        self.notify("speakers")

    def update_speaker(self, speaker_id: str, display_name: str = None, color: str = None):
        if speaker_id in self.speakers:
            spk = self.speakers[speaker_id]
            if display_name is not None:
                spk.display_name = display_name
            if color is not None:
                if spk.style is None:
                    spk.style = SubtitleStyle(primary_color=color)
                else:
                    spk.style.primary_color = color
            self.notify("speakers")

    def get_style_for_subtitle(self, sub: SubtitleEntry) -> SubtitleStyle:
        """Returns per-line override > per-speaker style > primary_style."""
        if getattr(sub, 'style_override', None) is not None:
            return sub.style_override
        if sub.speaker_id and sub.speaker_id in self.speakers:
            spk = self.speakers[sub.speaker_id]
            if spk.style:
                return spk.style
        return self.primary_style
