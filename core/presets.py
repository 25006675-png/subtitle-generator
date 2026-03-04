import json
import os
from core.subtitle_model import SubtitleStyle

BUILTIN_PRESETS_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "presets.json")
USER_PRESETS_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "user_presets.json")


class PresetManager:
    def __init__(self):
        self._builtin: dict[str, SubtitleStyle] = {}
        self._user: dict[str, SubtitleStyle] = {}
        self._load_builtin()
        self._load_user()

    def _load_builtin(self):
        try:
            with open(BUILTIN_PRESETS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, style_dict in data.items():
                self._builtin[name] = SubtitleStyle.from_dict(style_dict)
        except Exception:
            pass

    def _load_user(self):
        try:
            with open(USER_PRESETS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, style_dict in data.items():
                self._user[name] = SubtitleStyle.from_dict(style_dict)
        except Exception:
            pass

    def get_all_names(self) -> list[str]:
        return list(self._builtin.keys()) + list(self._user.keys())

    def get_preset(self, name: str) -> SubtitleStyle | None:
        return self._builtin.get(name) or self._user.get(name)

    def is_user_preset(self, name: str) -> bool:
        return name in self._user

    def save_user_preset(self, name: str, style: SubtitleStyle):
        self._user[name] = style
        self._persist_user()

    def delete_user_preset(self, name: str) -> bool:
        if name in self._user:
            del self._user[name]
            self._persist_user()
            return True
        return False

    def _persist_user(self):
        data = {name: style.to_dict() for name, style in self._user.items()}
        try:
            with open(USER_PRESETS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
