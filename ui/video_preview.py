import customtkinter as ctk
import cv2
import time
import os
import re
import functools
import threading
import queue
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk
from app.theme import COLORS, FONTS, SPACING, RADIUS, IconRenderer, get_font_family
from core.subtitle_model import SubtitleStyle


# ---------------------------------------------------------------------------
# Font resolution — Windows registry + bold/italic variant lookup
# ---------------------------------------------------------------------------

_FONT_REGISTRY: dict | None = None  # lazy-loaded: {lowercase_display_name: abs_path}


def _load_font_registry() -> dict:
    global _FONT_REGISTRY
    if _FONT_REGISTRY is not None:
        return _FONT_REGISTRY
    _FONT_REGISTRY = {}
    try:
        import winreg
        fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        )
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                # Strip trailing "(TrueType)", "(OpenType)" etc.
                clean = re.sub(r"\s*\(.*?\)\s*$", "", name).strip().lower()
                path = value if os.path.isabs(value) else os.path.join(fonts_dir, value)
                _FONT_REGISTRY[clean] = path
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception:
        pass
    return _FONT_REGISTRY


@functools.lru_cache(maxsize=128)
def _resolve_font_path(family: str, bold: bool, italic: bool) -> str | None:
    """Return an absolute font file path for the given family + style, or None."""
    registry = _load_font_registry()

    style_parts = []
    if bold:
        style_parts.append("Bold")
    if italic:
        style_parts.append("Italic")

    # Build candidate display names: styled first, then plain family as fallback
    candidates = []
    if style_parts:
        candidates.append((family + " " + " ".join(style_parts)).lower())
    candidates.append(family.lower())

    for name in candidates:
        path = registry.get(name)
        if path and os.path.exists(path):
            return path
    return None

if os.name == "nt":
    _vlc_base_candidates = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
    ]
    for _base in _vlc_base_candidates:
        if os.path.isdir(_base):
            try:
                os.add_dll_directory(_base)
            except Exception:
                pass
            plugins_dir = os.path.join(_base, "plugins")
            if os.path.isdir(plugins_dir):
                os.environ.setdefault("VLC_PLUGIN_PATH", plugins_dir)
            break

try:
    import vlc
    HAS_VLC = True
except Exception:
    vlc = None
    HAS_VLC = False


class VideoPreview(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=0, **kwargs)
        self.state = state
        self._photo = None  # prevent GC
        self._capture = None
        self._capture_path = ""
        self._frame_cache = OrderedDict()
        self._scaled_frame_cache = OrderedDict()
        self._cache_limit = 160
        self._scaled_cache_limit = 120
        self._render_after_id = None
        self._play_after_id = None
        self._is_playing = False
        self._last_tick = 0.0
        self._suppress_scrub_callback = False
        self._canvas_image_id = None
        self._vlc_instance = None
        self._vlc_player = None
        self._audio_ready = False
        self._is_muted = False
        self._volume = 80

        # Threaded rendering
        self._render_queue: queue.Queue = queue.Queue(maxsize=2)
        self._render_thread = threading.Thread(target=self._render_worker, daemon=True)
        self._render_thread.start()
        self._pending_photo = None  # latest rendered result waiting for display

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Canvas for video frame
        self.canvas = ctk.CTkCanvas(
            self, bg="#000000", highlightthickness=0, cursor="crosshair",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=SPACING["sm"], pady=(SPACING["sm"], 0))
        self.canvas.bind("<Configure>", self._on_resize)

        # Time scrubber
        scrubber_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_tertiary"], height=44, corner_radius=RADIUS["md"])
        scrubber_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["sm"])
        scrubber_frame.grid_columnconfigure(2, weight=1)

        # Pillow play/pause icons
        self._play_icon = IconRenderer.get_colored("play", 16, "#FFFFFF")
        self._pause_icon = IconRenderer.get_colored("pause", 16, "#FFFFFF")

        self.play_btn = ctk.CTkButton(
            scrubber_frame,
            text="",
            image=self._play_icon,
            width=34,
            height=30,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=RADIUS["pill"],
            command=self._toggle_playback,
            cursor="hand2",
        )
        self.play_btn.grid(row=0, column=0, padx=(SPACING["sm"], SPACING["sm"]))

        self.time_label = ctk.CTkLabel(
            scrubber_frame, text="00:00",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=60,
        )
        self.time_label.grid(row=0, column=1, padx=(0, SPACING["sm"]))

        self.scrubber = ctk.CTkSlider(
            scrubber_frame,
            from_=0, to=1,
            number_of_steps=1000,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["progress_bg"],
            command=self._on_scrub,
            height=14,
        )
        self.scrubber.grid(row=0, column=2, sticky="ew")
        self.scrubber.set(0)

        self.duration_label = ctk.CTkLabel(
            scrubber_frame, text="00:00",
            font=ctk.CTkFont(family=FONTS["mono_small"][0], size=FONTS["mono_small"][1]),
            text_color=COLORS["text_secondary"], width=60,
        )
        self.duration_label.grid(row=0, column=3, padx=(SPACING["sm"], 0))

        # Pillow volume icons
        self._volume_icon = IconRenderer.get("volume", 16)
        self._mute_icon = IconRenderer.get("volume_mute", 16)

        self.mute_btn = ctk.CTkButton(
            scrubber_frame,
            text="",
            image=self._volume_icon,
            width=34,
            height=30,
            fg_color=COLORS["button_secondary"],
            hover_color=COLORS["button_secondary_hover"],
            corner_radius=RADIUS["md"],
            command=self._toggle_mute,
            cursor="hand2",
        )
        self.mute_btn.grid(row=0, column=4, padx=(SPACING["sm"], SPACING["sm"]))

        self.volume_slider = ctk.CTkSlider(
            scrubber_frame,
            from_=0,
            to=100,
            number_of_steps=20,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["progress_bg"],
            command=self._on_volume_change,
            height=14,
            width=90,
        )
        self.volume_slider.grid(row=0, column=5, padx=(0, SPACING["sm"]))
        self.volume_slider.set(self._volume)

        if not HAS_VLC:
            self.mute_btn.configure(state="disabled")
            self.volume_slider.configure(state="disabled")

        # State listener
        self.state.add_listener(self._on_state_change)
        self.bind("<Destroy>", self._on_destroy)

        # Show placeholder
        self._show_placeholder()

    def _on_state_change(self, field):
        if field in ("video", "preview_time", "subtitles", "selected_subtitle",
                      "style", "bilingual", "karaoke_mode", "speakers", "animation_style",
                      "karaoke_highlight_color", "transition_duration", "classic_dimmed_opacity",
                      "classic_history_mode",
                      "popup_scale", "popup_trail_count",
                      "wordbyw_entry_style", "wordbyw_history_style",
                      "subtitles_edited"):
            if field == "video":
                self._reset_video_session()
                self._setup_audio_player(self.state.video_path)

            # Clear scaled frame cache if style or karaoke modes changed to ensure re-render with new styles
            if field in ("style", "karaoke_mode", "animation_style", "bilingual", "subtitles_edited"):
                self._scaled_frame_cache.clear()

            self._request_render()

    def _on_resize(self, event=None):
        self._request_render()

    def _on_scrub(self, value):
        if self._suppress_scrub_callback:
            return
        duration = self.state.video_info.get("duration", 0)
        if duration > 0:
            t = value * duration
            self.state.set_preview_time(t)
            self._seek_audio(t)

    def _request_render(self):
        """Queue a render request; drop the oldest if full."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        params = self._snapshot_render_params(cw, ch)
        # Non-blocking put: drop if queue is full (always render the latest)
        try:
            self._render_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self._render_queue.put_nowait(params)
        except queue.Full:
            pass

    def _snapshot_render_params(self, cw: int, ch: int) -> dict:
        """Snapshot all state needed for rendering (called on main thread)."""
        sub = self.state.get_subtitle_at_time(self.state.preview_time)
        return {
            "video_path": self.state.video_path,
            "preview_time": self.state.preview_time,
            "canvas_w": cw,
            "canvas_h": ch,
            "subtitle": sub,
            "karaoke_mode": self.state.karaoke_mode,
            "animation_style": getattr(self.state, 'animation_style', 'none'),
            "transition_duration": getattr(self.state, 'transition_duration', 0.30),
            "karaoke_highlight_color": getattr(self.state, 'karaoke_highlight_color', '#FFFF00'),
            "classic_dimmed_opacity": getattr(self.state, 'classic_dimmed_opacity', 0.5),
            "classic_history_mode": getattr(self.state, 'classic_history_mode', 'none'),
            "popup_scale": getattr(self.state, 'popup_scale', 1.5),
            "popup_trail_count": getattr(self.state, 'popup_trail_count', 3),
            "wordbyw_entry_style": getattr(self.state, 'wordbyw_entry_style', 'instant'),
            "wordbyw_history_style": getattr(self.state, 'wordbyw_history_style', 'full'),
            "bilingual": self.state.bilingual,
            "secondary_on_top": self.state.secondary_on_top,
            "secondary_style": self.state.secondary_style,
            "is_playing": self._is_playing,
            "style": self.state.get_style_for_subtitle(sub) if sub else self.state.primary_style,
            "video_info": self.state.video_info,
        }

    def _render_worker(self):
        """Daemon thread: consume render params, produce PIL images."""
        while True:
            try:
                params = self._render_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if params is None:
                break

            try:
                img = self._render_frame(params)
                if img is not None:
                    # Schedule display on main thread
                    self.after(0, lambda i=img: self._display_frame(i))
            except Exception:
                pass

    def _display_frame(self, img: Image.Image):
        """Main thread: display a rendered PIL image on the canvas."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        self._photo = ImageTk.PhotoImage(img)
        if self._canvas_image_id is None:
            self._canvas_image_id = self.canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor="center")
        else:
            self.canvas.itemconfigure(self._canvas_image_id, image=self._photo)
            self.canvas.coords(self._canvas_image_id, cw // 2, ch // 2)
        self._update_time_labels()

    def _render_frame(self, params: dict) -> Image.Image | None:
        """Worker thread: full render pipeline."""
        if not params["video_path"]:
            return None

        img = self._get_scaled_frame(
            params["preview_time"], params["canvas_w"], params["canvas_h"],
            params["video_path"], params["video_info"]
        )
        if img is None:
            return None

        sub = params["subtitle"]
        if sub:
            karaoke = params["karaoke_mode"]
            if karaoke == "classic" and sub.words:
                img = self._draw_karaoke_classic(img, sub, params)
            elif karaoke == "popup" and sub.words:
                img = self._draw_karaoke_popup(img, sub, params)
            elif karaoke == "word_by_word" and sub.words:
                img = self._draw_karaoke_word_by_word(img, sub, params)
            else:
                effect = self._compute_anim_effect(sub, params)
                img = self._draw_subtitle(img, sub, params, effect=effect)

        return img

    def _extract_frame(self, time_seconds: float, video_path: str, video_info: dict) -> Image.Image | None:
        if not self._ensure_capture(video_path):
            return None

        fps = video_info.get("fps", 0) or 0
        if fps <= 0:
            fps = 30.0

        frame_index = max(0, int(time_seconds * fps))
        cached = self._frame_cache.get(frame_index)
        if cached is not None:
            self._frame_cache.move_to_end(frame_index)
            return cached

        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = self._capture.read()
        if not ok:
            return None

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        self._frame_cache[frame_index] = image
        if len(self._frame_cache) > self._cache_limit:
            self._frame_cache.popitem(last=False)
        return image

    def _get_scaled_frame(self, time_seconds: float, canvas_w: int, canvas_h: int,
                          video_path: str, video_info: dict) -> Image.Image | None:
        fps = video_info.get("fps", 0) or 30.0
        frame_index = max(0, int(time_seconds * fps))
        key = (frame_index, canvas_w, canvas_h)

        cached = self._scaled_frame_cache.get(key)
        if cached is not None:
            self._scaled_frame_cache.move_to_end(key)
            return cached

        frame = self._extract_frame(time_seconds, video_path, video_info)
        if frame is None:
            return None

        scaled = self._fit_image(frame, canvas_w, canvas_h)
        self._scaled_frame_cache[key] = scaled
        if len(self._scaled_frame_cache) > self._scaled_cache_limit:
            self._scaled_frame_cache.popitem(last=False)
        return scaled

    def _ensure_capture(self, path: str) -> bool:
        if self._capture is not None and self._capture_path == path and self._capture.isOpened():
            return True

        self._release_capture()
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return False
        self._capture = cap
        self._capture_path = path
        self._frame_cache.clear()
        self._scaled_frame_cache.clear()
        return True

    def _release_capture(self):
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None
        self._capture_path = ""

    def _reset_video_session(self):
        self._pause_playback(update_button=True)
        self._release_capture()
        self._frame_cache.clear()
        self._scaled_frame_cache.clear()
        self._release_audio_player()

    def _toggle_playback(self):
        if not self.state.video_path:
            return
        if self._is_playing:
            self._pause_playback(update_button=True)
        else:
            self._start_playback()

    def _start_playback(self):
        duration = self.state.video_info.get("duration", 0)
        if duration <= 0:
            return

        if not self._audio_ready and self.state.video_path:
            self._setup_audio_player(self.state.video_path)

        if self.state.preview_time >= duration:
            self.state.set_preview_time(0)

        self._is_playing = True
        self.play_btn.configure(image=self._pause_icon)
        self._last_tick = time.perf_counter()
        self._play_audio(self.state.preview_time)
        self._tick_playback()

    def _pause_playback(self, update_button: bool):
        self._is_playing = False
        self._pause_audio()
        if self._play_after_id is not None:
            try:
                self.after_cancel(self._play_after_id)
            except Exception:
                pass
            self._play_after_id = None
        if update_button:
            self.play_btn.configure(image=self._play_icon)

    def _tick_playback(self):
        if not self._is_playing:
            return

        duration = self.state.video_info.get("duration", 0)
        audio_time = self._get_audio_time() if self._audio_ready else None

        if audio_time is not None:
            next_time = audio_time
        else:
            now = time.perf_counter()
            elapsed = max(0.0, now - self._last_tick)
            self._last_tick = now
            next_time = self.state.preview_time + elapsed

        if next_time >= duration:
            self.state.set_preview_time(duration)
            self._pause_playback(update_button=True)
            return

        if abs(next_time - self.state.preview_time) > 0.001:
            self.state.set_preview_time(next_time)

        self._play_after_id = self.after(16, self._tick_playback)

    def _fit_image(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        ratio = min(max_w / img.width, max_h / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)

        result = Image.new("RGB", (max_w, max_h), (0, 0, 0))
        resized = img.resize((new_w, new_h), Image.BILINEAR)
        offset_x = (max_w - new_w) // 2
        offset_y = (max_h - new_h) // 2
        result.paste(resized, (offset_x, offset_y))
        return result

    def _get_font(self, style: SubtitleStyle, img_h: int, size_override: int = None, scale: float = 1.0):
        base = size_override or max(12, int(style.font_size * img_h / 1080))
        font_size = max(4, int(base * scale))

        path = _resolve_font_path(style.font_family, style.bold, style.italic)
        if path:
            try:
                return ImageFont.truetype(path, font_size)
            except OSError:
                pass

        fallbacks = ["msyh.ttc", "simhei.ttf", "arial.ttf", "msgothic.ttc"]
        for f_name in fallbacks:
            try:
                return ImageFont.truetype(f_name, font_size)
            except OSError:
                continue

        return ImageFont.load_default()

    def _compute_anim_effect(self, sub, params: dict) -> dict:
        anim = params["animation_style"]
        if anim == "none":
            return {}
        if not params["is_playing"]:
            stable = {
                "fade":       {"type": "fade",       "alpha": 1.0},
                "pop":        {"type": "pop",         "scale": 1.0},
                "slide_up":   {"type": "slide_up",    "y_offset": 0},
                "typewriter": {"type": "typewriter",  "char_frac": 1.0},
            }
            return stable.get(anim, {})
        t = params["preview_time"]
        dur = max(0.001, params["transition_duration"])
        t_in = t - sub.start
        t_out = sub.end - t
        if anim == "fade":
            return {"type": "fade", "alpha": min(min(1.0, t_in / dur), min(1.0, t_out / (dur * 0.67)))}
        elif anim == "pop":
            return {"type": "pop", "scale": min(1.0, t_in / dur) if t_in < dur else 1.0}
        elif anim == "slide_up":
            return {"type": "slide_up", "y_offset": int(60 * max(0.0, 1.0 - t_in / dur)) if t_in < dur else 0}
        elif anim == "typewriter":
            total = max(0.001, sub.end - sub.start)
            return {"type": "typewriter", "char_frac": min(1.0, t_in / (total * 0.85))}
        return {}

    def _draw_subtitle(self, img: Image.Image, sub, params: dict, effect: dict = None) -> Image.Image:
        anim_type = (effect or {}).get("type", "none")

        if anim_type == "typewriter":
            from types import SimpleNamespace
            frac = effect.get("char_frac", 1.0)
            n = max(1, int(len(sub.original_text) * frac))
            sub = SimpleNamespace(
                original_text=sub.original_text[:n],
                translated_text=getattr(sub, 'translated_text', ""),
                speaker_id=getattr(sub, 'speaker_id', ""),
                style_override=getattr(sub, 'style_override', None),
            )
            effect = None

        scale = effect.get("scale", 1.0) if effect else 1.0
        y_offset = effect.get("y_offset", 0) if effect else 0

        if anim_type == "fade":
            alpha = effect.get("alpha", 1.0)
            base = img.copy()
            rendered = self._draw_subtitle_content(img.copy(), sub, params, scale=scale, y_offset=y_offset)
            return Image.blend(base, rendered, alpha)

        return self._draw_subtitle_content(img, sub, params, scale=scale, y_offset=y_offset)

    def _draw_subtitle_content(self, img: Image.Image, sub, params: dict,
                                scale: float = 1.0, y_offset: int = 0) -> Image.Image:
        img = img.copy()
        w, h = img.size

        primary_style = params["style"]

        texts = []
        if params["secondary_on_top"]:
            if params["bilingual"] and sub.translated_text:
                texts.append((sub.translated_text, params["secondary_style"]))
            texts.append((sub.original_text, primary_style))
        else:
            texts.append((sub.original_text, primary_style))
            if params["bilingual"] and sub.translated_text:
                texts.append((sub.translated_text, params["secondary_style"]))

        pos_groups = {"top": [], "center": [], "bottom": []}
        for text, style in texts:
            pos_groups[style.position].append((text, style))

        for pos, items in pos_groups.items():
            img = self._draw_stacked_texts(img, items, pos, w, h, scale=scale, y_offset=y_offset)

        return img

    def _compute_y_base(self, position: str, style: SubtitleStyle, total_stack_h: int,
                         img_h: int, y_offset: int = 0) -> int:
        """Compute y start for a text stack, incorporating position_offset."""
        offset_px = int(img_h * getattr(style, 'position_offset', 0) / 100)
        if position == "top":
            base = int(img_h * 0.10)
        elif position == "center":
            base = (img_h - total_stack_h) // 2
        else:
            base = int(img_h * 0.90) - total_stack_h
        return base + y_offset + offset_px

    def _draw_stacked_texts(self, img: Image.Image, items, position: str,
                            img_w: int, img_h: int, scale: float = 1.0, y_offset: int = 0) -> Image.Image:
        if not items:
            return img

        draw = ImageDraw.Draw(img)
        gap = 10
        blocks = []
        total_stack_h = 0

        for text, style in items:
            font, lines, block_w, block_h = self._prepare_text_block(
                draw, text, style, img_w, img_h, scale=scale
            )
            blocks.append({"style": style, "font": font, "lines": lines, "w": block_w, "h": block_h})
            total_stack_h += block_h + gap
        total_stack_h -= gap

        # Use the first style's position_offset for the group
        first_style = items[0][1]
        current_y = self._compute_y_base(position, first_style, total_stack_h, img_h, y_offset)

        # First pass: collect all render items
        render_items = []
        for block in blocks:
            line_y = current_y
            for line_text, line_w, line_h in block["lines"]:
                x = (img_w - line_w) // 2
                render_items.append((block["style"], block["font"], line_text, x, line_y, line_w, line_h))
                line_y += line_h + 2
            current_y += block["h"] + gap

        # Batch all backgrounds into a single composite
        if any(item[0].background_enabled for item in render_items):
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            pad = 6
            for style, _, _, x, y, w, h in render_items:
                if style.background_enabled:
                    bg = self._hex_to_rgb(style.background_color)
                    op = int(style.background_opacity * 255)
                    ov_draw.rounded_rectangle(
                        [x - pad, y - 2, x + w + pad, y + h + 2], radius=4, fill=(*bg, op)
                    )
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        _DIR8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        for style, font, text, x, y, w, h in render_items:
            img = self._apply_glow(img, style, font, text, x, y)
            img = self._apply_shadow(img, style, font, text, x, y)
            draw = ImageDraw.Draw(img)
            t = style.outline_thickness
            if t > 0:
                oc = self._hex_to_rgb(style.outline_color)
                for dx, dy in _DIR8:
                    draw.text((x + dx * t, y + dy * t), text, font=font, fill=oc)
            draw.text((x, y), text, font=font, fill=self._hex_to_rgb(style.primary_color))

        return img

    # ------------------------------------------------------------------
    # Glow and Shadow helpers
    # ------------------------------------------------------------------

    def _apply_glow(self, img: Image.Image, style: SubtitleStyle,
                    font, text: str, x: int, y: int) -> Image.Image:
        if not getattr(style, 'glow_enabled', False):
            return img
        radius = max(1, getattr(style, 'glow_radius', 5))
        glow_color = self._hex_to_rgb(getattr(style, 'glow_color', '#FFFFFF'))

        # Draw text on transparent layer, blur it, composite under original
        glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        # Draw multiple times to intensify glow
        for _ in range(3):
            gd.text((x, y), text, font=font, fill=(*glow_color, 200))
        blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius))

        base = img.convert("RGBA")
        result = Image.alpha_composite(base, blurred)
        return result.convert("RGB")

    def _apply_shadow(self, img: Image.Image, style: SubtitleStyle,
                      font, text: str, x: int, y: int) -> Image.Image:
        if not getattr(style, 'shadow_enabled', False):
            return img
        sx = getattr(style, 'shadow_offset_x', 2)
        sy = getattr(style, 'shadow_offset_y', 2)
        blur = getattr(style, 'shadow_blur', 0)
        sc = self._hex_to_rgb(getattr(style, 'shadow_color', '#000000'))

        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.text((x + sx, y + sy), text, font=font, fill=(*sc, 220))
        if blur > 0:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))

        base = img.convert("RGBA")
        result = Image.alpha_composite(base, shadow_layer)
        return result.convert("RGB")

    # ------------------------------------------------------------------
    # Karaoke modes
    # ------------------------------------------------------------------

    def _draw_karaoke_classic(self, img: Image.Image, sub, params: dict) -> Image.Image:
        """Classic karaoke: all words shown, spoken words highlighted, current word glowing."""
        img = img.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size
        current_time = params["preview_time"]

        style = params["style"]
        font = self._get_font(style, h)

        words = self._get_karaoke_words(sub)
        if not words:
            return self._draw_subtitle(img, sub, params)

        word_metrics = []
        total_w = 0
        space_w = draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]

        for i, we in enumerate(words):
            text = we["word"].strip()
            if not text:
                continue
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            word_metrics.append({
                "text": text, "w": tw, "h": th,
                "start": we["start"], "end": we["end"], "index": i,
            })
            total_w += tw + (space_w if i < len(words) - 1 else 0)

        if not word_metrics:
            return self._draw_subtitle(img, sub, params)

        max_h = max(m["h"] for m in word_metrics)
        offset_px = int(h * getattr(style, 'position_offset', 0) / 100)

        if style.position == "top":
            y = int(h * 0.10) + offset_px
        elif style.position == "center":
            y = (h - max_h) // 2 + offset_px
        else:
            y = int(h * 0.90) - max_h + offset_px

        start_x = (w - total_w) // 2
        cur_x = start_x

        highlight_color = self._hex_to_rgb(params["karaoke_highlight_color"])
        history_mode = params["classic_history_mode"]
        dimmed_a = int(params["classic_dimmed_opacity"] * 255)
        pr, pg, pb = self._hex_to_rgb(style.primary_color)
        dimmed_color = (int(pr * dimmed_a / 255), int(pg * dimmed_a / 255), int(pb * dimmed_a / 255))
        outline_color = self._hex_to_rgb(style.outline_color)
        thickness = style.outline_thickness
        base_color = self._hex_to_rgb(style.primary_color)

        # Batch all word backgrounds in one composite pass
        if style.background_enabled:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            pad = 4
            tmp_x = start_x
            bg_color = self._hex_to_rgb(style.background_color)
            opacity = int(style.background_opacity * 255)
            for m in word_metrics:
                ov_draw.rounded_rectangle(
                    [tmp_x - pad, y - 2, tmp_x + m["w"] + pad, y + m["h"] + 2],
                    radius=4, fill=(*bg_color, opacity),
                )
                tmp_x += m["w"] + space_w
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        # Highlight background box: draw behind active (and spoken) words in "box" mode
        if history_mode == "box":
            hl_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            hl_draw = ImageDraw.Draw(hl_overlay)
            pad = 5
            tmp_x = start_x
            for m in word_metrics:
                is_active = current_time >= m["start"] and current_time < m["end"]
                is_spoken = current_time >= m["end"]
                if is_active:
                    hl_draw.rounded_rectangle(
                        [tmp_x - pad, y - 3, tmp_x + m["w"] + pad, y + m["h"] + 3],
                        radius=5, fill=(*highlight_color, 180),
                    )
                elif is_spoken:
                    hl_draw.rounded_rectangle(
                        [tmp_x - pad, y - 3, tmp_x + m["w"] + pad, y + m["h"] + 3],
                        radius=5, fill=(*highlight_color, 90),
                    )
                tmp_x += m["w"] + space_w
            img = Image.alpha_composite(img.convert("RGBA"), hl_overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        _DIR8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

        for m in word_metrics:
            active = current_time >= m["start"] and current_time < m["end"]
            spoken = current_time >= m["end"]

            if active:
                color = highlight_color
            elif spoken:
                color = highlight_color if history_mode == "color" else base_color
            else:
                color = dimmed_color

            # Outline: active word uses style outline_color for contrast; others use outline_color
            if thickness > 0:
                if active:
                    t2 = thickness + 1
                    for dx, dy in _DIR8:
                        draw.text((cur_x + dx * t2, y + dy * t2), m["text"], font=font, fill=outline_color)
                else:
                    for dx, dy in _DIR8:
                        draw.text((cur_x + dx * thickness, y + dy * thickness), m["text"], font=font, fill=outline_color)

            draw.text((cur_x, y), m["text"], font=font, fill=color)
            cur_x += m["w"] + space_w

        return img

    def _draw_karaoke_popup(self, img: Image.Image, sub, params: dict) -> Image.Image:
        """Pop-up mode: show only current word, large and centered."""
        img = img.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size
        current_time = params["preview_time"]

        style = params["style"]
        words = self._get_karaoke_words(sub)
        if not words:
            return self._draw_subtitle(img, sub, params)

        current_word = None
        current_idx = -1
        for i, we in enumerate(words):
            if we["start"] <= current_time <= we["end"]:
                current_word = we
                current_idx = i
                break

        if current_word is None:
            for i, we in enumerate(words):
                if current_time < we["start"]:
                    current_word = we
                    current_idx = i
                    break
            if current_word is None:
                return img

        scale_mult = params["popup_scale"]
        large_size = max(12, int(style.font_size * h / 1080 * scale_mult))
        large_font = self._get_font(style, h, size_override=large_size)

        word_text = current_word["word"].strip()
        if not word_text:
            return img

        bbox = draw.textbbox((0, 0), word_text, font=large_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        offset_px = int(h * getattr(style, 'position_offset', 0) / 100)
        x = (w - tw) // 2
        if style.position == "top":
            y = int(h * 0.12) + offset_px
        elif style.position == "center":
            y = (h - th) // 2 + offset_px
        else:
            y = int(h * 0.85) - th + offset_px

        _DIR8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        outline_color = self._hex_to_rgb(style.outline_color)
        thickness = style.outline_thickness
        if thickness > 0:
            for dx, dy in _DIR8:
                draw.text((x + dx * thickness, y + dy * thickness), word_text, font=large_font, fill=outline_color)

        text_color = self._hex_to_rgb(style.primary_color)
        draw.text((x, y), word_text, font=large_font, fill=text_color)

        small_size = max(12, int(style.font_size * h / 1080 * 0.7))
        small_font = self._get_font(style, h, size_override=small_size)
        trail_y = y - int(th * 0.6)

        trail_count = params["popup_trail_count"]
        for offset in range(1, min(trail_count + 1, current_idx + 1)):
            prev_idx = current_idx - offset
            if prev_idx < 0:
                break
            prev_word = words[prev_idx]["word"].strip()
            if not prev_word:
                continue

            alpha = max(80, 200 - offset * 60)
            dimmed = (alpha, alpha, alpha)

            pbbox = draw.textbbox((0, 0), prev_word, font=small_font)
            pw = pbbox[2] - pbbox[0]
            ph = pbbox[3] - pbbox[1]
            px = (w - pw) // 2
            trail_y -= ph + 4

            draw.text((px, trail_y), prev_word, font=small_font, fill=dimmed)

        return img

    def _draw_karaoke_word_by_word(self, img: Image.Image, sub, params: dict) -> Image.Image:
        """Word-by-word mode: words appear one at a time, building the full sentence."""
        import math
        from types import SimpleNamespace

        words = self._get_karaoke_words(sub)
        if not words:
            return self._draw_subtitle(img, sub, params)

        current_time = params["preview_time"]
        visible = [w for w in words if w["start"] <= current_time]
        if not visible:
            return img

        entry_style = params["wordbyw_entry_style"]
        history_style = params["wordbyw_history_style"]

        def make_sub(word_list):
            text = " ".join(w["word"] for w in word_list).strip()
            if not text:
                return None
            return SimpleNamespace(
                original_text=text,
                translated_text=sub.translated_text if hasattr(sub, "translated_text") else None,
                speaker_id=sub.speaker_id if hasattr(sub, "speaker_id") else None,
                style_override=getattr(sub, 'style_override', None),
            )

        newest = visible[-1]
        t_in = current_time - newest["start"]
        entry_dur = 0.15

        full_sub = make_sub(visible)
        prev_sub = make_sub(visible[:-1]) if len(visible) > 1 else None

        def render(base, s):
            if s is None:
                return base.copy()
            return self._draw_subtitle(base.copy(), s, params)

        def apply_history(base_img, rendered_img):
            if history_style == "dimmed":
                return Image.blend(base_img, rendered_img, 0.65)
            return rendered_img

        if entry_style == "instant":
            return apply_history(img, render(img, full_sub))

        if entry_style == "fade":
            alpha = min(1.0, t_in / entry_dur)
        else:
            alpha = min(1.0, math.sqrt(max(0.0, t_in / entry_dur)))

        if alpha >= 1.0:
            return apply_history(img, render(img, full_sub))

        prev_rendered = render(img, prev_sub)
        full_rendered = render(img, full_sub)

        if history_style == "dimmed":
            prev_final = Image.blend(img, prev_rendered, 0.65)
            full_final = Image.blend(img, full_rendered, 0.65)
        else:
            prev_final = prev_rendered
            full_final = full_rendered

        return Image.blend(prev_final, full_final, alpha)

    def _get_karaoke_words(self, sub) -> list[dict]:
        if getattr(sub, "words", None):
            return [
                {"word": w.word, "start": float(w.start), "end": float(w.end)}
                for w in sub.words
            ]

        text = (getattr(sub, "original_text", "") or "").strip()
        tokens = text.split()
        if not tokens:
            return []

        start = float(getattr(sub, "start", 0.0))
        end = float(getattr(sub, "end", start + 0.001))
        duration = max(0.001, end - start)
        step = duration / max(1, len(tokens))

        fallback = []
        for i, token in enumerate(tokens):
            w_start = start + i * step
            w_end = end if i == len(tokens) - 1 else min(end, w_start + step)
            fallback.append({"word": token, "start": w_start, "end": w_end})
        return fallback

    def _prepare_text_block(self, draw: ImageDraw.Draw, text: str, style: SubtitleStyle,
                            img_w: int, img_h: int, scale: float = 1.0):
        font = self._get_font(style, img_h, scale=scale)

        max_width = int(img_w * 0.85)
        lines = []
        words = text.split()

        if not words:
            return font, [], 0, 0

        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    l_bbox = draw.textbbox((0, 0), current_line, font=font)
                    lines.append((current_line, l_bbox[2]-l_bbox[0], l_bbox[3]-l_bbox[1]))
                current_line = word

        if current_line:
            l_bbox = draw.textbbox((0, 0), current_line, font=font)
            lines.append((current_line, l_bbox[2]-l_bbox[0], l_bbox[3]-l_bbox[1]))

        block_h = sum(l[2] for l in lines) + (len(lines)-1)*2
        block_w = max(l[1] for l in lines) if lines else 0

        return font, lines, block_w, block_h

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def _show_placeholder(self):
        self.canvas.delete("all")
        self._canvas_image_id = None
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 10 and ch > 10:
            ff = get_font_family()
            self.canvas.create_text(
                cw // 2, ch // 2 - 10,
                text="\u25B6",
                fill="#4B5563",
                font=(ff, 28),
            )
            self.canvas.create_text(
                cw // 2, ch // 2 + 24,
                text="No video loaded",
                fill="#6B7280",
                font=(ff, 13),
            )

    def _update_time_labels(self):
        t = self.state.preview_time
        d = self.state.video_info.get("duration", 0)
        self.time_label.configure(text=self._fmt(t))
        self.duration_label.configure(text=self._fmt(d))
        if d > 0:
            self._suppress_scrub_callback = True
            try:
                self.scrubber.set(t / d)
            finally:
                self._suppress_scrub_callback = False

    def _on_destroy(self, event=None):
        if event is not None and event.widget is not self:
            return
        self._pause_playback(update_button=False)
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except Exception:
                pass
            self._render_after_id = None
        # Signal worker thread to stop
        try:
            self._render_queue.put_nowait(None)
        except Exception:
            pass
        self._release_capture()
        self._release_audio_player()

    def _setup_audio_player(self, path: str):
        if not HAS_VLC or not path:
            self._audio_ready = False
            return
        try:
            self._release_audio_player()
            self._vlc_instance = vlc.Instance("--quiet")
            self._vlc_player = self._vlc_instance.media_player_new()

            media = None
            try:
                media = self._vlc_instance.media_new_path(path)
            except Exception:
                pass

            if media is None:
                try:
                    media = self._vlc_instance.media_new(path)
                except Exception:
                    pass

            if media is None:
                raise RuntimeError("Failed to create VLC media")

            media.add_option(":no-video")
            self._vlc_player.set_media(media)
            self._vlc_player.audio_set_volume(int(self._volume))
            self._vlc_player.audio_set_mute(self._is_muted)
            self._audio_ready = True
        except Exception:
            self._audio_ready = False
            self._vlc_instance = None
            self._vlc_player = None

    def _release_audio_player(self):
        if self._vlc_player is not None:
            try:
                self._vlc_player.stop()
            except Exception:
                pass
        self._vlc_player = None
        self._vlc_instance = None
        self._audio_ready = False

    def _play_audio(self, time_seconds: float):
        if not self._audio_ready or self._vlc_player is None:
            return
        try:
            self._vlc_player.play()
            self._vlc_player.audio_set_volume(int(self._volume))
            self._vlc_player.audio_set_mute(self._is_muted)
            self.after(80, lambda: self._seek_audio(time_seconds))
        except Exception:
            self._audio_ready = False

    def _pause_audio(self):
        if not self._audio_ready or self._vlc_player is None:
            return
        try:
            self._vlc_player.pause()
        except Exception:
            self._audio_ready = False

    def _seek_audio(self, time_seconds: float):
        if not self._audio_ready or self._vlc_player is None:
            return
        try:
            self._vlc_player.set_time(max(0, int(time_seconds * 1000)))
        except Exception:
            self._audio_ready = False

    def _get_audio_time(self) -> float | None:
        if not self._audio_ready or self._vlc_player is None:
            return None
        try:
            current_ms = self._vlc_player.get_time()
            if current_ms is None or current_ms < 0:
                return None
            return current_ms / 1000.0
        except Exception:
            self._audio_ready = False
            return None

    def _toggle_mute(self):
        self._is_muted = not self._is_muted
        self.mute_btn.configure(image=self._mute_icon if self._is_muted else self._volume_icon)
        if self._audio_ready and self._vlc_player is not None:
            try:
                self._vlc_player.audio_set_mute(self._is_muted)
            except Exception:
                self._audio_ready = False

    def _on_volume_change(self, value):
        self._volume = int(value)
        if self._volume == 0 and not self._is_muted:
            self._is_muted = True
            self.mute_btn.configure(image=self._mute_icon)
        elif self._volume > 0 and self._is_muted:
            self._is_muted = False
            self.mute_btn.configure(image=self._volume_icon)

        if self._audio_ready and self._vlc_player is not None:
            try:
                self._vlc_player.audio_set_volume(self._volume)
                self._vlc_player.audio_set_mute(self._is_muted)
            except Exception:
                self._audio_ready = False

    @staticmethod
    def _fmt(seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
