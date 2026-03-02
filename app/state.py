from dataclasses import dataclass, field
from typing import Callable
from core.subtitle_model import SubtitleEntry, SubtitleStyle


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
