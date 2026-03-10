# Bilingual Position Constraints And Note Wrapping

## Goal

Restore the original bilingual position constraint behavior while keeping preview and burn rendering aligned, and stop helper notes from wrapping too early in narrow fixed widths.

## Decisions

- Keep strict slot ordering between primary and secondary subtitle lines.
- When `Bilingual Order` is reversed, the slot-order rules reverse as well.
- Disable impossible `Top` / `Center` / `Bottom` buttons in both columns based on the current combination.
- Block slider moves that would cross the allowed order and show the existing hint to use `Bilingual Order`.
- Use `85%` as the bottom baseline.
- When both lines share the bottom slot, split them to `84%` and `86%` depending on stack order.
- Let glow, burn-in, transcription, and settings helper notes use the full available row width instead of a narrow fixed wrap.

## Implementation Scope

- `ui/panels/style_panel.py`: restore constraint helpers, button disabling, slider clamping, and note wrapping.
- `core/subtitle_renderer.py`: align position defaults and same-slot handling with the UI.
- `core/subtitle_model.py` and `app/state.py`: align bottom defaults to the new `85/84/86` baseline.
- `ui/panels/export_panel.py`, `ui/panels/transcribe_panel.py`, `ui/panels/settings_panel.py`: widen helper note wrapping.

## Validation

- Confirm impossible slot buttons disable on both columns.
- Confirm slider movement is blocked when it would violate line order.
- Confirm bottom uses `85%` by default and `84/86` when both lines share bottom.
- Confirm preview and burn renderer use the same vertical-position rules.
- Confirm helper notes use the full available row before wrapping.