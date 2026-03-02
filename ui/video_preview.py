import customtkinter as ctk
import cv2
import time
import os
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont, ImageTk
from app.theme import COLORS, FONTS, SPACING, RADIUS, IconRenderer, get_font_family
from core.subtitle_model import SubtitleStyle

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
                      "style", "bilingual"):
            if field == "video":
                self._reset_video_session()
                self._setup_audio_player(self.state.video_path)
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
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except Exception:
                pass
        self._render_after_id = self.after(16, self._render)

    def _render(self):
        self._render_after_id = None
        if not self.state.video_path:
            self._pause_playback(update_button=True)
            self._show_placeholder()
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        # Extract and scale frame
        img = self._get_scaled_frame(self.state.preview_time, cw, ch)
        if img is None:
            self._show_placeholder()
            return

        # Overlay subtitles
        sub = self.state.get_subtitle_at_time(self.state.preview_time)
        if sub:
            img = self._draw_subtitle(img, sub)

        # Display
        self._photo = ImageTk.PhotoImage(img)
        if self._canvas_image_id is None:
            self._canvas_image_id = self.canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor="center")
        else:
            self.canvas.itemconfigure(self._canvas_image_id, image=self._photo)
            self.canvas.coords(self._canvas_image_id, cw // 2, ch // 2)

        # Update time labels
        self._update_time_labels()

    def _extract_frame(self, time_seconds: float) -> Image.Image | None:
        if not self._ensure_capture(self.state.video_path):
            return None

        fps = self.state.video_info.get("fps", 0) or 0
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

    def _get_scaled_frame(self, time_seconds: float, canvas_w: int, canvas_h: int) -> Image.Image | None:
        fps = self.state.video_info.get("fps", 0) or 30.0
        frame_index = max(0, int(time_seconds * fps))
        key = (frame_index, canvas_w, canvas_h)

        cached = self._scaled_frame_cache.get(key)
        if cached is not None:
            self._scaled_frame_cache.move_to_end(key)
            return cached

        frame = self._extract_frame(time_seconds)
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
        next_time = self._get_audio_time() if self._audio_ready else None
        if next_time is None:
            now = time.perf_counter()
            elapsed = max(0.0, now - self._last_tick)
            self._last_tick = now
            next_time = self.state.preview_time + elapsed

        if next_time >= duration:
            self.state.set_preview_time(duration)
            self._pause_playback(update_button=True)
            return

        self.state.set_preview_time(next_time)
        self._play_after_id = self.after(33, self._tick_playback)

    def _fit_image(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        ratio = min(max_w / img.width, max_h / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)

        # Create black background
        result = Image.new("RGB", (max_w, max_h), (0, 0, 0))
        resized = img.resize((new_w, new_h), Image.BILINEAR)
        offset_x = (max_w - new_w) // 2
        offset_y = (max_h - new_h) // 2
        result.paste(resized, (offset_x, offset_y))
        return result

    def _draw_subtitle(self, img: Image.Image, sub) -> Image.Image:
        img = img.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Determine rendering order
        texts = []
        if self.state.secondary_on_top:
            if self.state.bilingual and sub.translated_text:
                texts.append((sub.translated_text, self.state.secondary_style))
            texts.append((sub.original_text, self.state.primary_style))
        else:
            texts.append((sub.original_text, self.state.primary_style))
            if self.state.bilingual and sub.translated_text:
                texts.append((sub.translated_text, self.state.secondary_style))

        # We group texts by position to handle stacking
        pos_groups = {"top": [], "center": [], "bottom": []}
        for text, style in texts:
            pos_groups[style.position].append((text, style))

        # Render each group
        for pos, items in pos_groups.items():
            self._draw_stacked_texts(draw, items, pos, w, h)

        return img

    def _draw_stacked_texts(self, draw: ImageDraw.Draw, items, position: str, img_w: int, img_h: int):
        if not items:
            return

        # Prepare all blocks in the stack
        blocks = []
        total_stack_h = 0
        gap = 10  # Gap between stacked lines

        for text, style in items:
            # Wrap text and get block dimensions
            font, lines, block_w, block_h = self._prepare_text_block(draw, text, style, img_w, img_h)
            blocks.append({
                "style": style,
                "font": font,
                "lines": lines,
                "w": block_w,
                "h": block_h
            })
            total_stack_h += block_h + gap

        total_stack_h -= gap  # Remove last gap

        # Calculate starting Y
        if position == "top":
            current_y = int(img_h * 0.05)
        elif position == "center":
            current_y = (img_h - total_stack_h) // 2
        else:  # bottom
            current_y = int(img_h * 0.90) - total_stack_h

        # Draw each block
        for block in blocks:
            style = block["style"]
            font = block["font"]
            lines = block["lines"]
            block_w = block["w"]
            block_h = block["h"]
            
            # Start drawing this block at current_y
            line_y = current_y
            for line_text, line_w, line_h in lines:
                x = (img_w - line_w) // 2
                
                # Background
                if style.background_enabled:
                    pad = 6
                    bg_color = self._hex_to_rgb(style.background_color)
                    opacity = int(style.background_opacity * 255)
                    overlay = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
                    overlay_draw = ImageDraw.Draw(overlay)
                    overlay_draw.rounded_rectangle(
                        [x - pad, line_y - 2, x + line_w + pad, line_y + line_h + 2],
                        radius=4,
                        fill=(*bg_color, opacity),
                    )
                    draw._image.paste(Image.alpha_composite(
                        draw._image.convert("RGBA"), overlay
                    ).convert("RGB"), (0,0))
                    draw = ImageDraw.Draw(draw._image)

                # Outline
                outline_color = self._hex_to_rgb(style.outline_color)
                thickness = style.outline_thickness
                if thickness > 0:
                    for dx in range(-thickness, thickness + 1):
                        for dy in range(-thickness, thickness + 1):
                            if dx*dx + dy*dy <= thickness*thickness:
                                draw.text((x + dx, line_y + dy), line_text, font=font, fill=outline_color)

                # Main text
                text_color = self._hex_to_rgb(style.primary_color)
                draw.text((x, line_y), line_text, font=font, fill=text_color)
                line_y += line_h + 2 # Minor spacing between lines of same block
            
            current_y += block_h + gap

    def _prepare_text_block(self, draw: ImageDraw.Draw, text: str, style: SubtitleStyle, img_w: int, img_h: int):
        # Font setup - use a font that supports Chinese characters
        font_size = max(12, int(style.font_size * img_h / 1080))
        
        # Windows-specific font candidates that support Chinese/CJK
        font_candidates = [
            "msyh.ttc",     # Microsoft YaHei
            "simhei.ttf",   # SimHei
            "arial.ttf",    # Fallback
            "msgothic.ttc", # Japanese fallback
        ]
        
        font = None
        for f_name in font_candidates:
            try:
                font = ImageFont.truetype(f_name, font_size)
                break
            except OSError:
                continue
        
        if font is None:
            font = ImageFont.load_default()

        # Wrap text
        max_width = int(img_w * 0.85)
        lines = []
        words = text.split()
        
        if not words: # Handle empty/space text
            return font, [], 0, 0

        # Simple wrap for characters/words
        current_line = ""
        for word in words:
            # Check if this is CJK or space separated
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

        # Calculate block h/w
        block_h = sum(l[2] for l in lines) + (len(lines)-1)*2
        block_w = max(l[1] for l in lines) if lines else 0
        
        return font, lines, block_w, block_h

    def _draw_text_with_style(self, draw: ImageDraw.Draw, text: str,
                               style: SubtitleStyle, img_w: int, img_h: int):
        # Deprecated: replaced by _draw_stacked_texts
        pass

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
