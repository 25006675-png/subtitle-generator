# Task Plan — Subtitle Generator Feature Sprint

## Goal
Implement 7 improvements identified in PM review session:
A. Fix video preview lag (thread rendering)
B. Fix Classic highlight bug (outline color)
C. Classic "history highlight" subsetting
D. Shadow settings in Appearance
E. Glow settings in Appearance
F. Precise position slider (vertical offset)
G. Per-line styling (style override per subtitle entry)

## Status: in_progress

---

## Phase 1 — Data Model (subtitle_model.py + state.py)
**Status:** pending

Changes:
- `SubtitleStyle` — add fields: `shadow_enabled`, `shadow_color`, `shadow_blur`, `shadow_offset_x`, `shadow_offset_y`, `glow_enabled`, `glow_color`, `glow_radius`, `position_offset`
- `SubtitleEntry` — add field: `style_override: SubtitleStyle | None = None`
- `AppState` — add fields: `classic_history_highlight: bool = False`; add setters; update `get_style_for_subtitle` to check `sub.style_override` first

**Files:** `core/subtitle_model.py`, `app/state.py`

---

## Phase 2 — Video Preview Renderer (video_preview.py)
**Status:** pending

Changes:
- **Lag fix**: move PIL compositing to daemon thread using `threading.Thread` + `queue.Queue(maxsize=2)`. Main thread queues render requests; worker thread renders; result posted via `self.after(0, ...)`.
- Also fix Classic per-word bg: batch all word backgrounds into one RGBA composite (same as `_draw_stacked_texts`) instead of per-word overlay.
- **Bug B**: Classic active-word outline — change `fill=highlight_color` to `fill=outline_color` (black)
- **Feature C**: Classic history highlight — when `state.classic_history_highlight`, spoken words use `highlight_color` instead of `base_color`
- **Feature D**: Shadow rendering — draw shadow text with offset on a separate layer, apply `ImageFilter.GaussianBlur` if blur > 0, composite under main text
- **Feature E**: Glow rendering — render text on RGBA layer, blur it, composite below main text
- **Feature F**: Position offset — apply `style.position_offset` (−50..+50 % of img_h) to y calculation

**Files:** `ui/video_preview.py`

---

## Phase 3 — Style Panel UI (style_panel.py)
**Status:** pending

Changes:
- **Feature C**: Add "Keep History Highlight" toggle in Classic settings sub-frame
- **Features D+E**: Add "Shadow" and "Glow" sections to `StyleColumn` with:
  - Shadow: enable switch, color swatch, blur slider (0–20), offset X/Y sliders (0–20)
  - Glow: enable switch, color swatch, radius slider (0–30)
- **Feature F**: Add vertical offset slider (-50..+50) under Position segment in `StyleColumn`

**Files:** `ui/panels/style_panel.py`

---

## Phase 4 — Per-Line Style UI (subtitle_list.py)
**Status:** pending

Changes:
- Right-click context menu on subtitle rows → "Set line style" → opens `LineStyleDialog` (CTkToplevel)
- `LineStyleDialog`: compact popup with color picker, size slider (inherit/override), bold/italic toggles, clear button
- Show a small colored square in the row if a style override is active
- Update `_rebuild_list` to show override indicator

**Files:** `ui/subtitle_list.py`

---

## Phase 5 — ASS Export (ass_writer.py)
**Status:** pending

Changes:
- `build_style_line`: add shadow fields from `SubtitleStyle` to ASS Shadow parameter
- Note: glow is preview-only (no ASS equivalent — skip or approximate with large shadow)
- Note: `position_offset` — translate to ASS `\an` + margin or `\pos` override

**Files:** `export/ass_writer.py`

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | - | - |

---

## Key Decisions
- Per-word styling deferred (too complex data model change); per-LINE via `SubtitleEntry.style_override` is the target
- Glow is preview-only in ASS export (no native equivalent)
- Threading approach: daemon thread with `queue.Queue(maxsize=2)`, drop-on-full semantics for smooth playback
- Position offset is stored as integer percentage of image height (−50..+50)
- Classic history highlight is a state flag (not per-style) since it's a karaoke behavior
