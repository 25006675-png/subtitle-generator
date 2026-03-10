import customtkinter as ctk
import tkinter as tk
from app.theme import COLORS, SPACING, RADIUS, SIDEBAR
from app.state import AppState
from ui.sidebar import Sidebar
from ui.video_preview import VideoPreview
from ui.subtitle_list import SubtitleList
from ui.panels.video_panel import VideoPanel
from ui.panels.transcribe_panel import TranscribePanel
from ui.panels.style_panel import StylePanel
from ui.panels.export_panel import ExportPanel
from ui.panels.settings_panel import SettingsPanel


class SubtitleGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("SubGen - Subtitle Generator")
        self.geometry("1280x800")
        self.minsize(960, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # App state
        self.app_state = AppState()
        self.app_state.add_listener(self._on_state_change)

        # Root grid: sidebar | main content
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # main
        self.grid_rowconfigure(0, weight=1)

        self.configure(fg_color=COLORS["bg_primary"])

        # Sidebar
        self.sidebar = Sidebar(self, self.app_state)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.configure(width=SIDEBAR["expanded_width"])
        self.sidebar.grid_propagate(False)

        # Main content area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=SPACING["sm"], pady=SPACING["sm"])
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Draggable split panes
        pane_bg = self._resolve_pane_color()
        self.vertical_pane = tk.PanedWindow(
            self.main_frame,
            orient=tk.VERTICAL,
            sashwidth=4,
            bd=0,
            bg=pane_bg,
            relief=tk.FLAT,
        )
        self.vertical_pane.grid(row=0, column=0, sticky="nsew")

        self.top_pane = tk.PanedWindow(
            self.vertical_pane,
            orient=tk.HORIZONTAL,
            sashwidth=4,
            bd=0,
            bg=pane_bg,
            relief=tk.FLAT,
        )

        # Video preview
        self.video_preview = VideoPreview(self.top_pane, self.app_state)

        # Subtitle list
        self.subtitle_list = SubtitleList(self.top_pane, self.app_state)

        self.top_pane.add(self.video_preview, minsize=500, stretch="always")
        self.top_pane.add(self.subtitle_list, minsize=260)

        # Control panel container
        self.control_container = ctk.CTkFrame(
            self.vertical_pane,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
        )
        self.control_container.grid_columnconfigure(0, weight=1)
        self.control_container.grid_rowconfigure(0, weight=1)

        self.control_scroll = ctk.CTkScrollableFrame(
            self.control_container,
            fg_color="transparent",
            corner_radius=0,
        )
        self.control_scroll.grid(row=0, column=0, sticky="nsew")
        self.control_scroll.grid_columnconfigure(0, weight=1)

        self.vertical_pane.add(self.top_pane, minsize=260, stretch="always")
        self.vertical_pane.add(self.control_container, minsize=220)

        # Create all step panels
        self.panels = [
            VideoPanel(self.control_scroll, self.app_state),
            TranscribePanel(self.control_scroll, self.app_state),
            StylePanel(self.control_scroll, self.app_state),
            ExportPanel(self.control_scroll, self.app_state),
            SettingsPanel(self.control_scroll, self.app_state),
        ]
        self._active_panel_index = None

        # Fix black edge artifacts from CTkFrame inside PanedWindow
        for w in (self.video_preview, self.subtitle_list, self.control_container):
            try:
                w._canvas.configure(highlightthickness=0, bd=0)
            except Exception:
                pass

        # Show initial panel
        self._show_panel(0)
        self.after(120, self._set_initial_sashes)

    def _on_state_change(self, field):
        if field == "step":
            self._show_panel(self.app_state.current_step)
        elif field == "theme":
            self._update_pane_colors()

    def _show_panel(self, index):
        if not (0 <= index < len(self.panels)):
            return

        if self._active_panel_index == index:
            return

        if self._active_panel_index is not None and 0 <= self._active_panel_index < len(self.panels):
            self.panels[self._active_panel_index].grid_remove()

        self.panels[index].grid(row=0, column=0, sticky="nsew")
        self._active_panel_index = index

        parent_canvas = getattr(self.control_scroll, "_parent_canvas", None)
        if parent_canvas is not None:
            self.after_idle(lambda: parent_canvas.yview_moveto(0))

    def _resolve_pane_color(self) -> str:
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        color = COLORS["bg_primary"][1] if is_dark else COLORS["bg_primary"][0]
        return color

    def _update_pane_colors(self):
        """Update PanedWindow backgrounds on theme change."""
        color = self._resolve_pane_color()
        try:
            self.vertical_pane.configure(bg=color)
            self.top_pane.configure(bg=color)
        except Exception:
            pass

    def _set_initial_sashes(self):
        try:
            w = max(1, self.main_frame.winfo_width())
            h = max(1, self.main_frame.winfo_height())
            self.top_pane.sash_place(0, int(w * 0.62), 0)
            self.vertical_pane.sash_place(0, 0, int(h * 0.62))
        except tk.TclError:
            pass
