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

    # Shadow: use the larger of offset_x/offset_y as ASS shadow depth
    if getattr(style, 'shadow_enabled', False):
        shadow_depth = max(getattr(style, 'shadow_offset_x', 2), getattr(style, 'shadow_offset_y', 2))
    else:
        shadow_depth = 0

    if style.background_enabled:
        back_color = hex_to_ass_color(style.background_color, style.background_opacity)
        border_style = 3  # opaque box
    else:
        back_color = "&H00000000"
        border_style = 1  # outline + shadow

    return (
        f"Style: {name},{font},{size},{primary},&H000000FF,{outline},{back_color},"
        f"{bold},{italic},0,0,100,100,0,0,{border_style},{border},{shadow_depth},{alignment},10,10,10,1"
    )


def _entry_anim_tag(animation_style: str, position: str, duration_ms: int = 300) -> str:
    """Return ASS override tag string for entry animation (empty string if none)."""
    if animation_style == "fade":
        out_ms = int(duration_ms * 0.67)
        return rf"\fad({duration_ms},{out_ms})"
    elif animation_style == "pop":
        return rf"\fscx0\fscy0\t(0,{duration_ms},\fscx100\fscy100)"
    elif animation_style == "slide_up":
        if position == "bottom":
            return rf"\move(960,1130,960,1070,0,{duration_ms})"
        elif position == "top":
            return rf"\move(960,-20,960,50,0,{duration_ms})"
        else:
            return rf"\move(960,600,960,540,0,{duration_ms})"
    return ""


def write_ass(entries, output_path: str, primary_style: SubtitleStyle,
              secondary_style: SubtitleStyle | None = None, bilingual: bool = False,
              karaoke_mode: str = "off", speakers: dict = None,
              include_speaker_labels: bool = False, animation_style: str = "none",
              transition_duration: float = 0.30):
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

    # Per-speaker styles (Feature 4)
    speaker_style_names = {}
    if speakers:
        for spk_id, spk_info in speakers.items():
            if spk_info.style:
                style_name = f"Speaker_{spk_id.replace(' ', '_')}"
                lines.append(build_style_line(style_name, spk_info.style))
                speaker_style_names[spk_id] = style_name

    lines += [
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    duration_ms = int(transition_duration * 1000)
    anim_tag = _entry_anim_tag(animation_style, primary_style.position, duration_ms)

    def _pos_tag(style: SubtitleStyle) -> str:
        """Build \\pos tag from position_offset if non-zero, else empty string."""
        offset = getattr(style, 'position_offset', 0)
        if not offset:
            return ""
        # Map position to base Y at 1080p then apply offset
        base_y = {"bottom": 1010, "center": 540, "top": 70}.get(style.position, 1010)
        adjusted_y = base_y + int(1080 * offset / 100)
        return rf"\pos(960,{adjusted_y})"

    for entry in entries:
        start = format_ass_time(entry.start)
        end = format_ass_time(entry.end)

        # Determine style name
        style_name = "Primary"
        if entry.speaker_id and entry.speaker_id in speaker_style_names:
            style_name = speaker_style_names[entry.speaker_id]

        # Build text with optional speaker label
        text = entry.original_text.replace("\n", "\\N")
        if include_speaker_labels and entry.speaker_id:
            spk_name = entry.speaker_id
            if speakers and entry.speaker_id in speakers:
                spk_name = speakers[entry.speaker_id].display_name or entry.speaker_id
            text = f"[{spk_name}] {text}"

        # Typewriter: emit one sequential line per word
        if animation_style == "typewriter" and karaoke_mode == "off":
            words = entry.original_text.split()
            if len(words) > 1:
                dur = entry.end - entry.start
                step = dur / len(words)
                for i, _ in enumerate(words):
                    t0 = format_ass_time(entry.start + i * step)
                    t1 = format_ass_time(entry.start + (i + 1) * step) if i < len(words) - 1 else end
                    partial = " ".join(words[:i + 1]).replace("\n", "\\N")
                    lines.append(f"Dialogue: 0,{t0},{t1},{style_name},,0,0,0,,{partial}")
                if bilingual and entry.translated_text and secondary_style:
                    trans = entry.translated_text.replace("\n", "\\N")
                    lines.append(f"Dialogue: 0,{start},{end},Secondary,,0,0,0,,{trans}")
                continue

        # Determine effective style for position_offset
        eff_style = primary_style
        if entry.speaker_id and entry.speaker_id in speaker_style_names:
            if speakers and entry.speaker_id in speakers and speakers[entry.speaker_id].style:
                eff_style = speakers[entry.speaker_id].style
        if getattr(entry, 'style_override', None) is not None:
            eff_style = entry.style_override

        pos = _pos_tag(eff_style)

        # Karaoke mode (Feature 3)
        if karaoke_mode != "off" and hasattr(entry, 'words') and entry.words:
            karaoke_text = _build_karaoke_text(entry)
            prefix = f"{{{pos}}}" if pos else ""
            lines.append(f"Dialogue: 0,{start},{end},{style_name},,0,0,0,,{prefix}{karaoke_text}")
        else:
            tags = anim_tag + pos
            tagged = f"{{{tags}}}{text}" if tags else text
            lines.append(f"Dialogue: 0,{start},{end},{style_name},,0,0,0,,{tagged}")

        if bilingual and entry.translated_text and secondary_style:
            trans = entry.translated_text.replace("\n", "\\N")
            lines.append(f"Dialogue: 0,{start},{end},Secondary,,0,0,0,,{trans}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _build_karaoke_text(entry) -> str:
    """Build ASS karaoke text with \\kf tags for word-by-word highlighting."""
    parts = []
    for word in entry.words:
        duration_cs = max(1, int((word.end - word.start) * 100))
        parts.append(f"{{\\kf{duration_cs}}}{word.word}")
    return "".join(parts)
