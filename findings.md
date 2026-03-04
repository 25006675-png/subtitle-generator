# Findings

## Architecture Overview
- **State**: `app/state.py` — `AppState` dataclass with observer pattern (`add_listener` / `notify`)
- **Model**: `core/subtitle_model.py` — `SubtitleEntry`, `SubtitleStyle`, `WordEntry`, `SpeakerInfo`
- **Preview**: `ui/video_preview.py` — `VideoPreview` CTkFrame, renders via PIL/Pillow + OpenCV
- **Style UI**: `ui/panels/style_panel.py` — `StylePanel` + `StyleColumn` per style key
- **Subtitle List**: `ui/subtitle_list.py` — compact 24px rows, double-click inline edit
- **Export**: `export/ass_writer.py` — ASS format writer

## Bug B: Classic Highlight Outline Color
- **Location**: `video_preview.py:714-715`
- **Bug**: Active word glow outline drawn with `fill=highlight_color` (same as text) → no contrast
- **Fix**: Use `fill=outline_color` (or black) for the outline, keep `fill=highlight_color` for the text itself

## Performance Root Cause
- Playback ticks at 16ms via `after(16, _tick_playback)` → triggers `state.set_preview_time()` → notifies listeners → `_request_render()` → `after(16, _render)`
- `_render()` runs entirely on main thread: frame extract (cached) + PIL subtitle drawing (NOT cached during animation)
- Classic mode worst: creates new RGBA overlay PER WORD in a loop (`video_preview.py:699-706`)
- Fix 1 (quick win): batch classic word backgrounds into one composite
- Fix 2 (proper): offload PIL compositing to daemon thread

## Threading Plan
```
Main thread: schedules render params into queue
Daemon thread: reads queue, does PIL work, posts result back via after(0, ...)
Queue maxsize=2: drop old request if queue full (always render latest frame)
```

## SubtitleStyle Current Fields
font_family, font_size, primary_color, outline_color, outline_thickness,
bold, italic, background_enabled, background_color, background_opacity, position

## New Fields to Add to SubtitleStyle
- shadow_enabled: bool = False
- shadow_color: str = "#000000"
- shadow_blur: int = 0           # 0=hard shadow, >0=blur radius
- shadow_offset_x: int = 2
- shadow_offset_y: int = 2
- glow_enabled: bool = False
- glow_color: str = "#FFFFFF"
- glow_radius: int = 5           # Gaussian blur radius for glow
- position_offset: int = 0       # Vertical offset % of img_h, -50 to +50

## New AppState Fields
- classic_history_highlight: bool = False  (spoken words stay highlighted)

## SubtitleEntry New Field
- style_override: SubtitleStyle | None = None  (per-line style)

## get_style_for_subtitle Priority Order (after change)
1. sub.style_override (new — per-line)
2. per-speaker style
3. primary_style (global fallback)

## ASS Export Shadow Mapping
- ASS Style field "Shadow" = drop shadow depth (integer)
- `shadow_offset_x` → can approximate with Shadow value = max(offset_x, offset_y)
- No blur support in ASS natively; `shadow_blur` is preview-only
- `position_offset` → use `\pos` override tag per dialogue line

## Per-Line Style UI
- Right-click context menu on subtitle rows
- Opens `LineStyleDialog` (CTkToplevel)
- Small colored indicator in row if override active
- Clear button in dialog to remove override
