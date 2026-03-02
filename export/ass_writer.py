from core.subtitle_model import SubtitleStyle


def hex_to_ass_color(hex_color: str, opacity: float = 1.0) -> str:
    """Convert #RRGGBB to &HAABBGGRR ASS format."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    a = int((1.0 - opacity) * 255)
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"


def position_to_alignment(position: str) -> int:
    """Map position string to ASS alignment number (numpad style)."""
    return {"bottom": 2, "center": 5, "top": 8}.get(position, 2)


def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_style_line(name: str, style: SubtitleStyle) -> str:
    font = style.font_family
    size = style.font_size
    primary = hex_to_ass_color(style.primary_color)
    outline = hex_to_ass_color(style.outline_color)
    bold = -1 if style.bold else 0
    italic = -1 if style.italic else 0
    border = style.outline_thickness
    alignment = position_to_alignment(style.position)

    if style.background_enabled:
        back_color = hex_to_ass_color(style.background_color, style.background_opacity)
        border_style = 3  # opaque box
    else:
        back_color = "&H00000000"
        border_style = 1  # outline + shadow

    return (
        f"Style: {name},{font},{size},{primary},&H000000FF,{outline},{back_color},"
        f"{bold},{italic},0,0,100,100,0,0,{border_style},{border},0,{alignment},10,10,10,1"
    )


def write_ass(entries, output_path: str, primary_style: SubtitleStyle,
              secondary_style: SubtitleStyle | None = None, bilingual: bool = False):
    lines = [
        "[Script Info]",
        "Title: Generated Subtitles",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, StrikeOut, Underline, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        build_style_line("Primary", primary_style),
    ]

    if bilingual and secondary_style:
        lines.append(build_style_line("Secondary", secondary_style))

    lines += [
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for entry in entries:
        start = format_ass_time(entry.start)
        end = format_ass_time(entry.end)
        text = entry.original_text.replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Primary,,0,0,0,,{text}")

        if bilingual and entry.translated_text and secondary_style:
            trans = entry.translated_text.replace("\n", "\\N")
            lines.append(f"Dialogue: 0,{start},{end},Secondary,,0,0,0,,{trans}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
