# Burn-In Preview Parity Design

## Goal

Make burned-in subtitle exports look as close as possible to the live video preview, including:

- entry animations
- karaoke highlighting modes
- bilingual stacking and translation animation
- glow, shadow, background, wrapping, and font behavior

## Problem

The preview and export paths used different rendering models:

- preview: Pillow drawing in `ui/video_preview.py`
- burn-in export: ASS generation plus FFmpeg `ass` filter

That split guaranteed visual drift. ASS could approximate the styling, but it could not reliably match the preview's exact layout and animation behavior.

## Chosen Approach

Use Pillow as the source of truth for both preview and burn-in.

The burn-in path now renders transparent subtitle overlay images and composites them over the source video in FFmpeg. This keeps export fidelity aligned with the preview renderer instead of re-implementing the same styling in ASS.

## Architecture

### Shared renderer

`core/subtitle_renderer.py` contains the extracted subtitle renderer used by both paths:

- font resolution helpers
- render param builder
- normal subtitle drawing
- karaoke renderers
- glow, shadow, background, wrapping, and safe-width guide logic

`ui/video_preview.py` now delegates its active rendering entry points to this shared renderer.

### Burn-in export

`export/ffmpeg_burner.py` now:

- snapshots the needed app state for rendering
- renders transparent PNG overlays per timed segment
- writes an FFmpeg concat schedule for those overlay frames
- composites the overlay stream over the source video with FFmpeg's `overlay` filter

ASS remains available for subtitle file export, but not for the burn-in path.

## Timing Strategy

Three export strategies are used depending on cue behavior:

1. Static cues
Render one subtitle image and hold it for the cue duration.

2. Burst-plus-hold cues
For entry effects like `pop` and `slide_up`, render a short sampled burst for the animated portion, then hold a stable frame for the remainder.

3. Full sampled cues
For karaoke, fade, and typewriter-style behavior, sample the cue across its duration for safer parity.

This favors fidelity over speed, which matches the user-approved requirement.

## Tradeoffs

- Pros: much higher visual parity with preview, one renderer to maintain, no ASS feature-mapping drift
- Cons: more temporary overlay assets, slower exports for karaoke-heavy or densely animated timelines, video re-encode remains required

## Validation Completed

- shared renderer imports and renders successfully in the configured Python environment
- state snapshotting for export works
- overlay schedule generation creates a schedule file and PNG assets
- modified files report no editor diagnostics
- post-fix FFmpeg burn completes successfully with RGB overlay evaluation
- subtitle-time output frames are materially closer to the locally rendered expected composite than to the untouched source frames

## Glow Parity Adjustment

The original shared glow implementation still produced a mismatch even after preview/export unification:

- preview glow looked too dense because the halo mask was being hardened by a thresholded inner mask and doubled alpha
- export glow looked weaker because the overlay chain did not explicitly resolve in RGB before final YUV encoding

The fix was:

- soften the renderer's glow halo by removing the doubled alpha boost
- reduce the subtraction hardness of the inner mask so the halo keeps a soft edge
- slightly spread the outer blur so the glow reads as a halo instead of a bubble
- force FFmpeg overlay evaluation in RGB with `overlay=format=rgb`

This keeps the glow profile defined once in the shared renderer while giving FFmpeg a better chance to preserve the same gradient in the final MP4.

## Remaining Validation

A real end-to-end FFmpeg burn against an actual video should still be run to confirm the full pipeline under real media inputs.