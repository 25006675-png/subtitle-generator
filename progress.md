# Progress Log

## Session: 2026-03-04

### Started
- Created task_plan.md, findings.md, progress.md

### Phase 1 — Data Model — COMPLETE
- [x] SubtitleStyle new fields (shadow, glow, position_offset)
- [x] SubtitleEntry.style_override
- [x] AppState.classic_history_highlight + setter
- [x] AppState.get_style_for_subtitle updated

### Phase 2 — Video Preview Renderer — COMPLETE
- [x] Daemon thread rendering + queue (queue.Queue maxsize=2)
- [x] Fix classic per-word bg batching (one composite)
- [x] Bug B: Fix active-word outline color (uses outline_color not highlight_color)
- [x] Feature C: history highlight rendering (classic_history_highlight flag)
- [x] Feature D: Shadow rendering (_apply_shadow helper)
- [x] Feature E: Glow rendering (_apply_glow helper)
- [x] Feature F: position_offset in y calculation

### Phase 3 — Style Panel UI — COMPLETE
- [x] Classic: "Keep History Highlight" toggle
- [x] StyleColumn: Shadow section (enable, color, X/Y/blur sliders)
- [x] StyleColumn: Glow section (enable, color, radius slider)
- [x] StyleColumn: Position offset slider (-50..+50%)

### Phase 4 — Per-Line Style UI — COMPLETE
- [x] Right-click context menu on rows
- [x] LineStyleDialog CTkToplevel (color, size, bold/italic, offset)
- [x] Override indicator dot (● active, ○ inactive)
- [x] subtitles_edited listener to rebuild list

### Phase 5 — ASS Export — COMPLETE
- [x] Shadow depth in build_style_line (max of offset_x/y)
- [x] position_offset as \pos tag
- [x] style_override respected for pos tag

### Errors
(none yet)
