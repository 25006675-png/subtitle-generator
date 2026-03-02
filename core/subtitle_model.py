from dataclasses import dataclass, field


@dataclass
class SubtitleEntry:
    index: int
    start: float  # seconds
    end: float    # seconds
    original_text: str = ""
    translated_text: str = ""

    def duration(self) -> float:
        return self.end - self.start


@dataclass
class SubtitleStyle:
    font_family: str = "Arial"
    font_size: int = 48
    primary_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_thickness: int = 2
    bold: bool = False
    italic: bool = False
    background_enabled: bool = False
    background_color: str = "#000000"
    background_opacity: float = 0.5
    position: str = "bottom"  # "top", "center", "bottom"

    def to_dict(self) -> dict:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "primary_color": self.primary_color,
            "outline_color": self.outline_color,
            "outline_thickness": self.outline_thickness,
            "bold": self.bold,
            "italic": self.italic,
            "background_enabled": self.background_enabled,
            "background_color": self.background_color,
            "background_opacity": self.background_opacity,
            "position": self.position,
        }
