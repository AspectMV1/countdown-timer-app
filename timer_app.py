"""A small, offline countdown timer built with Python's standard library."""

import ctypes
import math
import sys
import time
import tkinter as tk
import tkinter.font as tkfont


BACKGROUND = "#0b0d12"
PANEL = "#171a22"
PANEL_HOVER = "#232733"
BORDER = "#303541"
TEXT = "#f4f6f8"
MUTED = "#8f96a3"
SUCCESS = "#79d39b"
WARNING = "#f0c674"
DANGER = "#ff8b82"


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", _RECT),
        ("rcWork", _RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


class _WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", _POINT),
        ("ptMaxPosition", _POINT),
        ("rcNormalPosition", _RECT),
        ("rcDevice", _RECT),
    ]


GA_ROOT = 2
GWL_STYLE = -16
GWL_EXSTYLE = -20
MONITOR_DEFAULTTONEAREST = 2
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOWMAXIMIZED = 3
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
SWP_NOOWNERZORDER = 0x0200
WS_OVERLAPPEDWINDOW = 0x00CF0000
WINDOW_EDGE_STYLES = 0x00020301
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWCP_DONOTROUND = 1
DWMWCP_ROUNDSMALL = 3
DWMWA_COLOR_NONE = 0xFFFFFFFE
MANUAL_RESIZE_BORDER = 9


def _load_user32():
    if sys.platform != "win32":
        return None
    try:
        user32 = ctypes.windll.user32
        user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        user32.GetAncestor.restype = ctypes.c_void_p
        user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_ssize_t,
        ]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.GetWindowPlacement.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_WINDOWPLACEMENT),
        ]
        user32.GetWindowPlacement.restype = ctypes.c_int
        user32.SetWindowPlacement.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_WINDOWPLACEMENT),
        ]
        user32.SetWindowPlacement.restype = ctypes.c_int
        user32.MonitorFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        user32.MonitorFromWindow.restype = ctypes.c_void_p
        user32.GetMonitorInfoW.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_MONITORINFO),
        ]
        user32.GetMonitorInfoW.restype = ctypes.c_int
        user32.SetWindowPos.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        user32.SetWindowPos.restype = ctypes.c_int
        user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.ShowWindow.restype = ctypes.c_int
        user32.GetWindowRect.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_RECT),
        ]
        user32.GetWindowRect.restype = ctypes.c_int
        user32.IsZoomed.argtypes = [ctypes.c_void_p]
        user32.IsZoomed.restype = ctypes.c_int
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        try:
            user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
            user32.GetDpiForWindow.restype = ctypes.c_uint
            user32.GetSystemMetricsForDpi.argtypes = [
                ctypes.c_int,
                ctypes.c_uint,
            ]
            user32.GetSystemMetricsForDpi.restype = ctypes.c_int
        except AttributeError:
            pass
        return user32
    except (AttributeError, OSError):
        return None


_USER32 = _load_user32()


def _load_dwmapi():
    if sys.platform != "win32":
        return None
    try:
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
        return dwmapi
    except (AttributeError, OSError):
        return None


_DWMAPI = _load_dwmapi()
_FRAMELESS_WINDOWS = set()


def _native_window_handle(window):
    if _USER32 is None:
        raise OSError("Native Windows APIs are unavailable")
    widget_handle = ctypes.c_void_p(window.winfo_id())
    top_handle = _USER32.GetAncestor(widget_handle, GA_ROOT)
    return ctypes.c_void_p(top_handle or widget_handle.value)


def _native_window_bounds(window):
    """Return the window's outer rectangle in absolute desktop coordinates."""
    rectangle = _RECT()
    if not _USER32.GetWindowRect(
        _native_window_handle(window),
        ctypes.byref(rectangle),
    ):
        raise ctypes.WinError()
    return (
        rectangle.left,
        rectangle.top,
        rectangle.right - rectangle.left,
        rectangle.bottom - rectangle.top,
    )


def _set_dwm_window_style(handle, rounded):
    """Apply the optional modern Windows border and corner appearance."""
    if _DWMAPI is None:
        return
    try:
        border_color = ctypes.c_uint(DWMWA_COLOR_NONE)
        _DWMAPI.DwmSetWindowAttribute(
            handle,
            DWMWA_BORDER_COLOR,
            ctypes.byref(border_color),
            ctypes.sizeof(border_color),
        )
        corner_preference = ctypes.c_int(
            DWMWCP_ROUNDSMALL if rounded else DWMWCP_DONOTROUND
        )
        _DWMAPI.DwmSetWindowAttribute(
            handle,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_preference),
            ctypes.sizeof(corner_preference),
        )
    except (OSError, ValueError):
        pass


def _apply_frameless_style(window, rounded=True):
    """Remove all native chrome and edge styles from a Tk top-level."""
    if _USER32 is None:
        raise OSError("Native Windows APIs are unavailable")

    window.update_idletasks()
    handle = _native_window_handle(window)
    style = _USER32.GetWindowLongPtrW(handle, GWL_STYLE)
    exstyle = _USER32.GetWindowLongPtrW(handle, GWL_EXSTYLE)
    frameless_style = (
        (style & ~(WS_CAPTION | WS_THICKFRAME | WS_MAXIMIZEBOX))
        | WS_SYSMENU
        | WS_MINIMIZEBOX
    )
    frameless_exstyle = (
        (exstyle & ~(WINDOW_EDGE_STYLES | WS_EX_TOOLWINDOW))
        | WS_EX_APPWINDOW
    )
    changed = frameless_style != style or frameless_exstyle != exstyle

    if frameless_style != style:
        _USER32.SetWindowLongPtrW(handle, GWL_STYLE, frameless_style)
    if frameless_exstyle != exstyle:
        _USER32.SetWindowLongPtrW(handle, GWL_EXSTYLE, frameless_exstyle)

    _set_dwm_window_style(handle, rounded)
    if changed:
        refresh_flags = (
            SWP_NOMOVE
            | SWP_NOSIZE
            | SWP_NOZORDER
            | SWP_NOOWNERZORDER
            | SWP_FRAMECHANGED
        )
        if not _USER32.SetWindowPos(
            handle,
            None,
            0,
            0,
            0,
            0,
            refresh_flags,
        ):
            raise ctypes.WinError()
        window.update_idletasks()

    final_style = _USER32.GetWindowLongPtrW(handle, GWL_STYLE)
    if final_style & (WS_CAPTION | WS_THICKFRAME):
        raise OSError("Windows did not remove the native frame")

    handle_value = int(handle.value)
    _FRAMELESS_WINDOWS.add(handle_value)
    return handle_value


def _install_frameless_chrome(window):
    """Guarantee custom chrome; never fall back to a Windows title bar."""
    try:
        return _apply_frameless_style(window, rounded=True)
    except (OSError, tk.TclError, ValueError):
        try:
            window.overrideredirect(True)
            window.update_idletasks()
            if _USER32 is not None:
                return _apply_frameless_style(window, rounded=True)
        except (OSError, tk.TclError, ValueError):
            pass
        return None


def _remove_frameless_chrome(handle_value):
    if handle_value is not None:
        _FRAMELESS_WINDOWS.discard(handle_value)


def _set_native_window_bounds(window, bounds, bring_to_front=False):
    """Place a window using signed virtual-desktop coordinates."""
    x, y, width, height = bounds
    flags = SWP_FRAMECHANGED | SWP_SHOWWINDOW | SWP_NOOWNERZORDER
    if not bring_to_front:
        flags |= SWP_NOZORDER
    if not _USER32.SetWindowPos(
        _native_window_handle(window),
        None,
        x,
        y,
        width,
        height,
        flags,
    ):
        raise ctypes.WinError()


def _capture_native_fullscreen_state(window):
    """Save placement/styles and find the monitor containing the window."""
    window.update_idletasks()
    handle = _native_window_handle(window)

    placement = _WINDOWPLACEMENT()
    placement.length = ctypes.sizeof(_WINDOWPLACEMENT)
    if not _USER32.GetWindowPlacement(handle, ctypes.byref(placement)):
        raise ctypes.WinError()

    monitor = _USER32.MonitorFromWindow(handle, MONITOR_DEFAULTTONEAREST)
    if not monitor:
        raise ctypes.WinError()
    monitor_info = _MONITORINFO()
    monitor_info.cbSize = ctypes.sizeof(_MONITORINFO)
    if not _USER32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
        raise ctypes.WinError()

    rectangle = monitor_info.rcMonitor
    return {
        "handle": handle,
        "placement": placement,
        "style": _USER32.GetWindowLongPtrW(handle, GWL_STYLE),
        "exstyle": _USER32.GetWindowLongPtrW(handle, GWL_EXSTYLE),
        "monitor_bounds": (
            rectangle.left,
            rectangle.top,
            rectangle.right - rectangle.left,
            rectangle.bottom - rectangle.top,
        ),
    }


def _enter_native_fullscreen(window, state):
    """Turn a Tk window into a borderless window on its current monitor."""
    handle = state["handle"]
    if state["placement"].showCmd == SW_SHOWMAXIMIZED:
        _USER32.ShowWindow(handle, SW_RESTORE)

    _USER32.SetWindowLongPtrW(
        handle,
        GWL_STYLE,
        state["style"] & ~WS_OVERLAPPEDWINDOW,
    )
    _USER32.SetWindowLongPtrW(
        handle,
        GWL_EXSTYLE,
        state["exstyle"] & ~WINDOW_EDGE_STYLES,
    )
    _set_native_window_bounds(window, state["monitor_bounds"], bring_to_front=True)
    window.update_idletasks()


def _restore_native_window(window, state):
    """Restore the exact styles, monitor, size, and maximized state."""
    handle = _native_window_handle(window)
    _USER32.SetWindowLongPtrW(handle, GWL_STYLE, state["style"])
    _USER32.SetWindowLongPtrW(handle, GWL_EXSTYLE, state["exstyle"])
    if not _USER32.SetWindowPlacement(
        handle,
        ctypes.byref(state["placement"]),
    ):
        raise ctypes.WinError()
    refresh_flags = (
        SWP_NOMOVE
        | SWP_NOSIZE
        | SWP_NOZORDER
        | SWP_FRAMECHANGED
        | SWP_NOOWNERZORDER
    )
    if not _USER32.SetWindowPos(
        handle,
        None,
        0,
        0,
        0,
        0,
        refresh_flags,
    ):
        raise ctypes.WinError()
    window.update_idletasks()


def parse_time_text(value):
    """Convert M, MM:SS, or H:MM:SS text to a positive number of seconds."""
    value = value.strip()
    if not value:
        raise ValueError("Enter a time first")

    parts = value.split(":")
    if len(parts) > 3 or any(not part.isdigit() for part in parts):
        raise ValueError("Use minutes, MM:SS, or H:MM:SS")

    numbers = [int(part) for part in parts]
    if len(numbers) == 1:
        total = numbers[0] * 60
    elif len(numbers) == 2:
        minutes, seconds = numbers
        if seconds >= 60:
            raise ValueError("Seconds must be below 60")
        total = minutes * 60 + seconds
    else:
        hours, minutes, seconds = numbers
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Minutes and seconds must be below 60")
        total = hours * 3600 + minutes * 60 + seconds

    if total <= 0:
        raise ValueError("Set a time longer than zero")
    if total > 3599999:
        raise ValueError("Maximum timer length is 999:59:59")
    return total


def format_time(seconds):
    """Format remaining seconds without dropping a second too early."""
    whole_seconds = int(math.ceil(max(0.0, seconds)))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return "{}:{:02d}:{:02d}".format(hours, minutes, secs)
    return "{:02d}:{:02d}".format(minutes, secs)


class HoverButton(tk.Button):
    """A flat Tk button with a subtle hover state."""

    def __init__(
        self,
        parent,
        *,
        background=PANEL,
        foreground=TEXT,
        hover_background=PANEL_HOVER,
        **kwargs
    ):
        self.normal_background = background
        self.hover_background = hover_background
        self.fade_locked = False
        super().__init__(
            parent,
            background=background,
            foreground=foreground,
            activebackground=hover_background,
            activeforeground=foreground,
            disabledforeground=MUTED,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
            **kwargs
        )
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _event):
        if not self.fade_locked and str(self["state"]) != tk.DISABLED:
            self.configure(background=self.hover_background)

    def _on_leave(self, _event):
        if not self.fade_locked:
            self.configure(background=self.normal_background)


class CountdownTimer:
    TICK_INTERVAL_MS = 50
    CONTROLS_VISIBLE_MS = 10_000
    CONTROLS_FADE_SECONDS = 0.55
    FADE_INTERVAL_MS = 25
    COLOR_OPTIONS = (
        "background",
        "foreground",
        "activebackground",
        "activeforeground",
        "disabledforeground",
        "highlightbackground",
        "highlightcolor",
        "insertbackground",
        "selectbackground",
        "selectforeground",
    )

    def __init__(self, root):
        self.root = root
        self.configured_seconds = 20 * 60
        self.remaining_seconds = float(self.configured_seconds)
        self.deadline = None
        self.running = False
        self.fullscreen = False
        self.fullscreen_transition = False
        self.fullscreen_native_state = None
        self.fullscreen_focus_widget = None
        self.fullscreen_refresh_after_id = None
        self.always_on_top = False
        self.after_id = None
        self.resize_after_id = None
        self.closing = False
        self.frameless_handle = None
        self.window_drag_start = None
        self.window_drag_bounds = None
        self.window_resize_edge = None

        self.controls_state = "visible"
        self.controls_hide_after_id = None
        self.controls_fade_after_id = None
        self.controls_generation = 0
        self.controls_fade_started = None
        self.control_target_colors = {}
        self.status_offset = -85

        self.time_text = tk.StringVar(value="20:00")
        self.display_text = tk.StringVar(value="20:00")
        self.status_text = tk.StringVar(value="READY")

        self._configure_window()
        self._build_interface()
        self._set_content_minimum_size()
        self.frameless_handle = _install_frameless_chrome(self.root)
        self._bind_shortcuts()
        self._setup_control_fade()
        self._render()
        self.root.after_idle(self._resize_timer_text)
        self._schedule_controls_hide()

    def _configure_window(self):
        self.root.title("Offline Timer")
        self.root.configure(background=BACKGROUND)
        self.root.geometry("560x400")
        self.root.minsize(420, 320)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _set_content_minimum_size(self):
        """Keep scaled controls separated at the narrowest window size."""
        if self.closing:
            return
        try:
            self.root.update_idletasks()
            gap = 8
            settings_width = self.settings_panel.winfo_reqwidth()
            left_extent = 14 + self.topmost_button.winfo_reqwidth()
            right_extent = 12 + self.window_controls.winfo_reqwidth()
            top_bar_width = settings_width + 2 * (
                max(left_extent, right_extent) + gap
            )
            content_width = self.bottom_panel.winfo_reqwidth() + 28
            minimum_width = max(420, top_bar_width, content_width)
            top_extent = 20 + self.settings_panel.winfo_reqheight()
            bottom_extent = 10 + self.bottom_panel.winfo_reqheight()
            status_height = self.status_label.winfo_reqheight()

            def vertical_layout_fits(height):
                pixel_size = max(48, min(int(height * 0.27), 240))
                self.timer_font.configure(size=-pixel_size)
                self.root.update_idletasks()
                timer_height = self.timer_label.winfo_reqheight()
                timer_top = height / 2 - timer_height / 2
                timer_bottom = height / 2 + timer_height / 2
                status_top = timer_top - status_height - 8
                return (
                    top_extent <= status_top
                    and timer_bottom + 8 <= height - bottom_extent
                )

            if vertical_layout_fits(320):
                minimum_height = 320
            else:
                low = 321
                high = 640
                while high < 4096 and not vertical_layout_fits(high):
                    low = high + 1
                    high *= 2
                high = min(high, 4096)
                while low < high:
                    middle = (low + high) // 2
                    if vertical_layout_fits(middle):
                        high = middle
                    else:
                        low = middle + 1
                minimum_height = low

            self.root.minsize(minimum_width, minimum_height)
        except tk.TclError:
            pass

    def _build_interface(self):
        self.timer_font = tkfont.Font(family="Segoe UI", size=-120, weight="normal")
        self.control_font = tkfont.Font(family="Segoe UI", size=11)
        self.small_font = tkfont.Font(family="Segoe UI", size=9)
        self.status_font = tkfont.Font(family="Segoe UI", size=9, weight="bold")

        self.settings_panel = tk.Frame(self.root, background=BACKGROUND)
        self.settings_panel.place(relx=0.5, y=20, anchor="n")

        tk.Label(
            self.settings_panel,
            text="SET TIME",
            font=self.small_font,
            foreground=MUTED,
            background=BACKGROUND,
        ).pack(pady=(0, 7))

        settings_row = tk.Frame(self.settings_panel, background=BACKGROUND)
        settings_row.pack()

        self.time_entry = tk.Entry(
            settings_row,
            textvariable=self.time_text,
            width=11,
            justify="center",
            font=self.control_font,
            foreground=TEXT,
            insertbackground=TEXT,
            background=PANEL,
            selectbackground="#465069",
            selectforeground=TEXT,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=MUTED,
        )
        self.time_entry.pack(side="left", ipady=9)

        self.set_button = HoverButton(
            settings_row,
            text="Set",
            command=self.apply_time,
            font=self.control_font,
            padx=18,
            pady=9,
        )
        self.set_button.pack(side="left", padx=(8, 0))

        self.topmost_button = HoverButton(
            self.root,
            text="On top  Off",
            command=self.toggle_always_on_top,
            background=BACKGROUND,
            hover_background=PANEL_HOVER,
            font=self.small_font,
            padx=8,
            pady=6,
        )
        self.topmost_button.place(x=14, y=10, anchor="nw")

        self.window_controls = tk.Frame(self.root, background=BACKGROUND)
        self.window_controls.place(relx=1.0, x=-12, y=10, anchor="ne")

        self.minimize_button = HoverButton(
            self.window_controls,
            text="\u2212",
            command=self.minimize_window,
            background=BACKGROUND,
            foreground=MUTED,
            hover_background=PANEL_HOVER,
            font=self.small_font,
            padx=7,
            pady=5,
        )
        self.minimize_button.pack(side="left", padx=(0, 3))

        self.fullscreen_button = HoverButton(
            self.window_controls,
            text="\u2197",
            command=self.toggle_fullscreen,
            background=BACKGROUND,
            foreground=MUTED,
            hover_background=PANEL_HOVER,
            font=self.small_font,
            padx=7,
            pady=5,
        )
        self.fullscreen_button.pack(side="left", padx=(0, 3))

        self.close_button = HoverButton(
            self.window_controls,
            text="\u00d7",
            command=self.close,
            background=BACKGROUND,
            foreground=MUTED,
            hover_background=PANEL_HOVER,
            font=self.small_font,
            padx=7,
            pady=5,
        )
        self.close_button.pack(side="left")

        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_text,
            font=self.status_font,
            foreground=MUTED,
            background=BACKGROUND,
        )

        self.timer_label = tk.Label(
            self.root,
            textvariable=self.display_text,
            font=self.timer_font,
            foreground=TEXT,
            background=BACKGROUND,
            borderwidth=0,
            cursor="hand2",
        )
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")

        self.bottom_panel = tk.Frame(self.root, background=BACKGROUND)

        self.quick_controls = tk.Frame(self.bottom_panel, background=BACKGROUND)
        for column, (label, seconds) in enumerate(
            (("+ 30 sec", 30), ("+ 1 min", 60), ("+ 5 min", 300))
        ):
            button = HoverButton(
                self.quick_controls,
                text=label,
                command=lambda amount=seconds: self.add_time(amount),
                font=self.small_font,
                padx=13,
                pady=8,
            )
            button.grid(row=0, column=column, padx=4)
        self.quick_controls.pack(pady=(0, 8))

        self.main_controls = tk.Frame(self.bottom_panel, background=BACKGROUND)

        self.start_button = HoverButton(
            self.main_controls,
            text="Start",
            command=self.toggle_timer,
            background=TEXT,
            foreground=BACKGROUND,
            hover_background="#ffffff",
            font=self.control_font,
            width=13,
            pady=10,
        )
        self.start_button.pack(side="left", padx=4)

        self.reset_button = HoverButton(
            self.main_controls,
            text="Reset",
            command=self.reset,
            font=self.control_font,
            width=10,
            pady=10,
        )
        self.reset_button.pack(side="left", padx=4)
        self.main_controls.pack(pady=(0, 8))

        self.shortcut_label = tk.Label(
            self.bottom_panel,
            text="Space  start / pause     Ctrl+R  reset     Esc  leave fullscreen",
            font=self.small_font,
            foreground=MUTED,
            background=BACKGROUND,
        )
        self.shortcut_label.pack()
        self.bottom_panel.place(relx=0.5, rely=1.0, y=-10, anchor="s")

    def _bind_shortcuts(self):
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.leave_fullscreen)
        self.root.bind("<space>", self._space_pressed)
        self.root.bind("<Control-r>", self._reset_shortcut)
        self.root.bind("<Control-R>", self._reset_shortcut)
        self.root.bind("<Configure>", self._window_resized)
        self.root.bind("<Map>", self._window_mapped, add="+")
        self.root.bind("<Motion>", self._update_resize_cursor, add="+")
        self.root.bind("<Leave>", self._clear_resize_cursor, add="+")
        self.root.bind("<ButtonPress-1>", self._begin_window_drag, add="+")
        self.root.bind("<B1-Motion>", self._drag_window, add="+")
        self.root.bind("<ButtonRelease-1>", self._end_window_drag, add="+")
        self.root.bind("<FocusOut>", self._end_window_drag, add="+")
        self.time_entry.bind("<Return>", self._apply_shortcut)
        self.time_entry.bind("<KP_Enter>", self._apply_shortcut)
        self.time_entry.bind("<Control-a>", self._select_all)
        self.time_entry.bind("<Control-A>", self._select_all)

    def _setup_control_fade(self):
        self.control_groups = (
            self.settings_panel,
            self.topmost_button,
            self.window_controls,
            self.status_label,
            self.bottom_panel,
        )
        self.control_widgets = []
        seen = set()
        for group in self.control_groups:
            for widget in self._walk_widgets(group):
                if widget in seen:
                    continue
                seen.add(widget)
                self.control_widgets.append(widget)
                widget.bind("<ButtonPress>", self._control_activity, add="+")
                widget.bind("<KeyPress>", self._control_activity, add="+")

        self.timer_label.bind("<Button-1>", self._timer_clicked)

    def _walk_widgets(self, widget):
        yield widget
        for child in widget.winfo_children():
            yield from self._walk_widgets(child)

    def _control_activity(self, _event=None):
        if self.closing or self.controls_state == "hidden":
            return None
        if self.controls_state == "fading":
            self._show_controls()
        else:
            self._schedule_controls_hide()
        return None

    def _timer_clicked(self, _event=None):
        self._show_controls()
        return "break"

    def _schedule_controls_hide(self):
        if self.closing or self.controls_state != "visible":
            return
        self._cancel_controls_delay()
        self.controls_generation += 1
        generation = self.controls_generation
        self.controls_hide_after_id = self.root.after(
            self.CONTROLS_VISIBLE_MS,
            lambda: self._begin_controls_fade(generation),
        )

    def _begin_controls_fade(self, generation):
        self.controls_hide_after_id = None
        if (
            self.closing
            or generation != self.controls_generation
            or self.controls_state != "visible"
        ):
            return

        self.controls_state = "fading"
        self.controls_fade_started = time.monotonic()
        self.control_target_colors = self._snapshot_control_colors()
        self._set_fade_lock(True)
        self._fade_controls_frame(generation)

    def _fade_controls_frame(self, generation):
        self.controls_fade_after_id = None
        if (
            self.closing
            or generation != self.controls_generation
            or self.controls_state != "fading"
        ):
            return

        elapsed = time.monotonic() - self.controls_fade_started
        progress = min(1.0, elapsed / self.CONTROLS_FADE_SECONDS)
        self._apply_control_alpha(1.0 - progress)

        if progress >= 1.0:
            for group in self.control_groups:
                group.place_forget()
            self._restore_control_colors()
            self._set_fade_lock(False)
            self.controls_state = "hidden"
            self.root.focus_set()
            return

        self.controls_fade_after_id = self.root.after(
            self.FADE_INTERVAL_MS,
            lambda: self._fade_controls_frame(generation),
        )

    def _show_controls(self):
        if self.closing:
            return

        previous_state = self.controls_state
        self.controls_generation += 1
        self._cancel_control_callbacks()

        if previous_state == "fading":
            self._restore_control_colors()
            self._set_fade_lock(False)
        elif previous_state == "hidden":
            self._place_control_groups()

        self.controls_state = "visible"
        self._schedule_controls_hide()

    def _place_control_groups(self):
        self.settings_panel.place(relx=0.5, y=20, anchor="n")
        self.topmost_button.place(x=14, y=10, anchor="nw")
        self.window_controls.place(relx=1.0, x=-12, y=10, anchor="ne")
        self.status_label.place(
            relx=0.5,
            rely=0.5,
            y=self.status_offset,
            anchor="center",
        )
        self.bottom_panel.place(relx=0.5, rely=1.0, y=-10, anchor="s")

    def _snapshot_control_colors(self):
        targets = {}
        for widget in self.control_widgets:
            colors = {}
            for option in self.COLOR_OPTIONS:
                try:
                    value = str(widget.cget(option))
                    self.root.winfo_rgb(value)
                except tk.TclError:
                    continue
                colors[option] = value

            if isinstance(widget, HoverButton):
                colors["background"] = widget.normal_background
                colors["activebackground"] = widget.hover_background
            if colors:
                targets[widget] = colors
        return targets

    def _apply_control_alpha(self, alpha):
        for widget, colors in self.control_target_colors.items():
            faded = {
                option: self._blend_color(BACKGROUND, color, alpha)
                for option, color in colors.items()
            }
            try:
                widget.configure(**faded)
            except tk.TclError:
                pass

    def _restore_control_colors(self):
        for widget, colors in self.control_target_colors.items():
            try:
                widget.configure(**colors)
            except tk.TclError:
                pass

    def _blend_color(self, start, end, amount):
        start_rgb = self.root.winfo_rgb(start)
        end_rgb = self.root.winfo_rgb(end)
        blended = [
            round((first + (last - first) * amount) / 257)
            for first, last in zip(start_rgb, end_rgb)
        ]
        return "#{:02x}{:02x}{:02x}".format(*blended)

    def _set_fade_lock(self, locked):
        for widget in self.control_widgets:
            if isinstance(widget, HoverButton):
                widget.fade_locked = locked

    def _update_fade_target(self, widget, option, color):
        if self.controls_state != "fading":
            return
        if widget in self.control_target_colors:
            self.control_target_colors[widget][option] = color

    def _cancel_controls_delay(self):
        if self.controls_hide_after_id is not None:
            try:
                self.root.after_cancel(self.controls_hide_after_id)
            except tk.TclError:
                pass
            self.controls_hide_after_id = None

    def _cancel_control_callbacks(self):
        self._cancel_controls_delay()
        if self.controls_fade_after_id is not None:
            try:
                self.root.after_cancel(self.controls_fade_after_id)
            except tk.TclError:
                pass
            self.controls_fade_after_id = None

    def _window_resized(self, event):
        if event.widget is not self.root or self.closing:
            return
        if self.resize_after_id is not None:
            self.root.after_cancel(self.resize_after_id)
        self.resize_after_id = self.root.after(30, self._resize_timer_text)

    def _window_mapped(self, event):
        if event.widget is self.root and not self.closing:
            self.root.after_idle(self._set_content_minimum_size)
            self.root.after_idle(self._refresh_frameless_chrome)

    def _refresh_frameless_chrome(self):
        if self.closing or self.fullscreen or self.fullscreen_transition:
            return
        handle_value = _install_frameless_chrome(self.root)
        if handle_value is not None:
            self.frameless_handle = handle_value

    def _resize_edge_at_pointer(self, event):
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        border = MANUAL_RESIZE_BORDER
        on_left = event.x < border
        on_right = event.x >= width - border
        on_top = event.y < border
        on_bottom = event.y >= height - border

        if on_top and on_left:
            return "nw"
        if on_top and on_right:
            return "ne"
        if on_bottom and on_left:
            return "sw"
        if on_bottom and on_right:
            return "se"
        if on_left:
            return "w"
        if on_right:
            return "e"
        if on_top:
            return "n"
        if on_bottom:
            return "s"
        return None

    def _update_resize_cursor(self, event):
        if (
            event.widget is not self.root
            or self.window_drag_start is not None
            or self.closing
            or self.fullscreen
            or self.fullscreen_transition
        ):
            return None
        cursor_by_edge = {
            "n": "sb_v_double_arrow",
            "s": "sb_v_double_arrow",
            "e": "sb_h_double_arrow",
            "w": "sb_h_double_arrow",
            "nw": "size_nw_se",
            "se": "size_nw_se",
            "ne": "size_ne_sw",
            "sw": "size_ne_sw",
        }
        edge = self._resize_edge_at_pointer(event)
        try:
            self.root.configure(cursor=cursor_by_edge.get(edge, ""))
        except tk.TclError:
            pass
        return None

    def _clear_resize_cursor(self, _event=None):
        if self.window_drag_start is None:
            try:
                self.root.configure(cursor="")
            except tk.TclError:
                pass
        return None

    def _begin_window_drag(self, event):
        """Begin moving or edge-resizing the custom mini-player window."""
        self._end_window_drag()
        if (
            event.widget is not self.root
            or self.closing
            or self.fullscreen
            or self.fullscreen_transition
        ):
            return None

        if _USER32 is not None:
            try:
                handle = _native_window_handle(self.root)
                if _USER32.IsZoomed(handle):
                    return None
                self.window_drag_bounds = _native_window_bounds(self.root)
            except (OSError, tk.TclError):
                self.window_drag_bounds = None
                return None
        else:
            try:
                self.window_drag_bounds = (
                    self.root.winfo_x(),
                    self.root.winfo_y(),
                    self.root.winfo_width(),
                    self.root.winfo_height(),
                )
            except tk.TclError:
                self.window_drag_bounds = None
                return None

        self.window_drag_start = (event.x_root, event.y_root)
        self.window_resize_edge = self._resize_edge_at_pointer(event)
        return "break"

    def _drag_window(self, event):
        if (
            self.window_drag_start is None
            or self.window_drag_bounds is None
            or self.closing
            or self.fullscreen
            or self.fullscreen_transition
        ):
            return None

        start_x, start_y = self.window_drag_start
        left, top, width, height = self.window_drag_bounds
        delta_x = event.x_root - start_x
        delta_y = event.y_root - start_y
        edge = self.window_resize_edge
        new_left = left
        new_top = top
        new_width = width
        new_height = height

        if edge:
            minimum_width, minimum_height = self.root.minsize()
            right = left + width
            bottom = top + height

            if "w" in edge:
                new_left = min(left + delta_x, right - minimum_width)
                new_width = right - new_left
            elif "e" in edge:
                new_width = max(minimum_width, width + delta_x)

            if "n" in edge:
                new_top = min(top + delta_y, bottom - minimum_height)
                new_height = bottom - new_top
            elif "s" in edge:
                new_height = max(minimum_height, height + delta_y)
        else:
            new_left = left + delta_x
            new_top = top + delta_y

        if _USER32 is not None:
            flags = SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_NOACTIVATE
            if not edge:
                flags |= SWP_NOSIZE
                new_width = 0
                new_height = 0
            try:
                if not _USER32.SetWindowPos(
                    _native_window_handle(self.root),
                    None,
                    new_left,
                    new_top,
                    new_width,
                    new_height,
                    flags,
                ):
                    raise ctypes.WinError()
            except (OSError, tk.TclError):
                self._end_window_drag()
                return None
        else:
            try:
                self.root.geometry(f"{new_width}x{new_height}+{new_left}+{new_top}")
            except tk.TclError:
                self._end_window_drag()
                return None
        return "break"

    def _end_window_drag(self, _event=None):
        self.window_drag_start = None
        self.window_drag_bounds = None
        self.window_resize_edge = None
        self._clear_resize_cursor()
        return None

    def _resize_timer_text(self):
        self.resize_after_id = None
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        character_count = max(len(self.display_text.get()), 5)
        by_height = int(height * 0.27)
        by_width = int((width * 0.82) / (character_count * 0.56))
        pixel_size = max(48, min(by_height, by_width, 240))
        self.timer_font.configure(size=-pixel_size)
        self.root.update_idletasks()

        timer_height = self.timer_label.winfo_reqheight()
        status_height = self.status_label.winfo_reqheight()
        self.status_offset = -(timer_height // 2 + status_height // 2 + 8)
        if self.controls_state != "hidden":
            self.status_label.place(
                relx=0.5,
                rely=0.5,
                y=self.status_offset,
                anchor="center",
            )

    def _set_status(self, text, color=MUTED):
        self.status_text.set(text)
        self.status_label.configure(foreground=color)
        self._update_fade_target(self.status_label, "foreground", color)

    def _show_valid_entry(self):
        self.time_entry.configure(
            highlightbackground=BORDER,
            highlightcolor=MUTED,
        )
        self._update_fade_target(self.time_entry, "highlightbackground", BORDER)
        self._update_fade_target(self.time_entry, "highlightcolor", MUTED)

    def _show_invalid_entry(self, message):
        self.time_entry.configure(
            highlightbackground=DANGER,
            highlightcolor=DANGER,
        )
        self._update_fade_target(self.time_entry, "highlightbackground", DANGER)
        self._update_fade_target(self.time_entry, "highlightcolor", DANGER)
        self._set_status(message, DANGER)

    def apply_time(self):
        try:
            seconds = parse_time_text(self.time_text.get())
        except ValueError as error:
            self._show_invalid_entry(str(error))
            return

        self._cancel_tick()
        self.running = False
        self.deadline = None
        self.configured_seconds = seconds
        self.remaining_seconds = float(seconds)
        self.time_text.set(format_time(seconds))
        self._show_valid_entry()
        self._set_status("READY", MUTED)
        self.timer_label.configure(foreground=TEXT)
        self._render()

    def toggle_timer(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.remaining_seconds <= 0:
            self.remaining_seconds = float(self.configured_seconds)

        self.running = True
        self.deadline = time.monotonic() + self.remaining_seconds
        self.timer_label.configure(foreground=TEXT)
        self._set_status("RUNNING", SUCCESS)
        self._render()
        self._schedule_tick()

    def pause(self):
        if not self.running:
            return
        self.remaining_seconds = max(0.0, self.deadline - time.monotonic())
        self.running = False
        self.deadline = None
        self._cancel_tick()
        if self.remaining_seconds <= 0:
            self._complete()
            return
        self._set_status("PAUSED", WARNING)
        self._render()

    def reset(self):
        self._cancel_tick()
        self.running = False
        self.deadline = None
        self.remaining_seconds = float(self.configured_seconds)
        self.timer_label.configure(foreground=TEXT)
        self._set_status("READY", MUTED)
        self._render()

    def add_time(self, seconds):
        if self.running:
            self.deadline += seconds
            self.remaining_seconds = max(0.0, self.deadline - time.monotonic())
        else:
            self.remaining_seconds += seconds
            self.timer_label.configure(foreground=TEXT)
            self._set_status("READY", MUTED)
        self._render()

    def _schedule_tick(self):
        self._cancel_tick()
        if self.running and not self.closing:
            self.after_id = self.root.after(self.TICK_INTERVAL_MS, self._tick)

    def _tick(self):
        self.after_id = None
        if not self.running or self.closing:
            return

        self.remaining_seconds = max(0.0, self.deadline - time.monotonic())
        if self.remaining_seconds <= 0:
            self._complete()
            return

        self._render()
        self._schedule_tick()

    def _complete(self):
        self._cancel_tick()
        self.running = False
        self.deadline = None
        self.remaining_seconds = 0.0
        self.timer_label.configure(foreground=DANGER)
        self._set_status("TIME'S UP", DANGER)
        self._render()
        try:
            self.root.bell()
        except tk.TclError:
            pass

    def _cancel_tick(self):
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

    def _render(self):
        new_text = format_time(self.remaining_seconds)
        changed_length = len(new_text) != len(self.display_text.get())
        self.display_text.set(new_text)
        self.start_button.configure(text="Pause" if self.running else "Start")
        if changed_length:
            self.root.after_idle(self._resize_timer_text)

    def minimize_window(self):
        self._end_window_drag()
        if self.fullscreen and not self.fullscreen_transition:
            self._exit_fullscreen()
        self.root.after_idle(self._perform_minimize)

    def _perform_minimize(self):
        if self.closing:
            return
        try:
            if _USER32 is not None:
                _USER32.ShowWindow(_native_window_handle(self.root), SW_MINIMIZE)
            else:
                self.root.iconify()
        except (OSError, tk.TclError):
            try:
                self.root.iconify()
            except tk.TclError:
                pass

    def toggle_always_on_top(self):
        requested = not self.always_on_top
        try:
            self.root.attributes("-topmost", requested)
        except tk.TclError:
            return

        self.always_on_top = requested
        if self.fullscreen_native_state is not None:
            if requested:
                self.fullscreen_native_state["exstyle"] |= WS_EX_TOPMOST
            else:
                self.fullscreen_native_state["exstyle"] &= ~WS_EX_TOPMOST

        color = SUCCESS if requested else TEXT
        self.topmost_button.configure(
            text="On top  On" if requested else "On top  Off",
            foreground=color,
            activeforeground=color,
        )
        self._update_fade_target(self.topmost_button, "foreground", color)
        self._update_fade_target(self.topmost_button, "activeforeground", color)
        self.root.after_idle(self._refresh_frameless_chrome)

    def toggle_fullscreen(self, _event=None):
        if _event is not None:
            self._control_activity()
        if self.fullscreen_transition:
            return "break"
        if self.fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()
        return "break"

    def _enter_fullscreen(self):
        self._end_window_drag()
        self.fullscreen_transition = True
        native_state = None
        self.fullscreen_focus_widget = self.root.focus_get()
        try:
            if _USER32 is not None:
                native_state = _capture_native_fullscreen_state(self.root)
                _enter_native_fullscreen(self.root, native_state)
            else:
                self.root.attributes("-fullscreen", True)

            self.fullscreen_native_state = native_state
            self.fullscreen = True
            if _USER32 is not None:
                _set_dwm_window_style(_native_window_handle(self.root), False)
            self.fullscreen_button.configure(text="\u2199")
            self._schedule_fullscreen_refresh(restore_focus=False)
        except (OSError, tk.TclError):
            if native_state is not None:
                try:
                    _restore_native_window(self.root, native_state)
                except (OSError, tk.TclError):
                    pass
            else:
                try:
                    self.root.attributes("-fullscreen", False)
                except tk.TclError:
                    pass
            self.fullscreen_native_state = None
            self.fullscreen = False
            if _USER32 is not None:
                _set_dwm_window_style(_native_window_handle(self.root), True)
        finally:
            self.fullscreen_transition = False

    def _exit_fullscreen(self):
        self.fullscreen_transition = True
        try:
            if self.fullscreen_native_state is not None:
                _restore_native_window(self.root, self.fullscreen_native_state)
            else:
                self.root.attributes("-fullscreen", False)

            self.fullscreen_native_state = None
            self.fullscreen = False
            if _USER32 is not None:
                _set_dwm_window_style(_native_window_handle(self.root), True)
            self.fullscreen_button.configure(text="\u2197")
            self._schedule_fullscreen_refresh(restore_focus=True)
        except (OSError, tk.TclError):
            pass
        finally:
            self.fullscreen_transition = False

    def _schedule_fullscreen_refresh(self, restore_focus):
        if self.fullscreen_refresh_after_id is not None:
            try:
                self.root.after_cancel(self.fullscreen_refresh_after_id)
            except tk.TclError:
                pass

        def refresh():
            self.fullscreen_refresh_after_id = None
            if self.closing:
                return
            self._resize_timer_text()
            if not restore_focus:
                return
            widget = self.fullscreen_focus_widget
            try:
                if widget is not None and widget.winfo_viewable():
                    widget.focus_set()
                else:
                    self.root.focus_set()
            except tk.TclError:
                self.root.focus_set()

        self.fullscreen_refresh_after_id = self.root.after_idle(refresh)

    def leave_fullscreen(self, _event=None):
        if self.fullscreen:
            if _event is not None:
                self._control_activity()
            if not self.fullscreen_transition:
                self._exit_fullscreen()
            return "break"
        return None

    def _space_pressed(self, _event):
        if self.root.focus_get() is self.time_entry:
            return None
        self._control_activity()
        self.toggle_timer()
        return "break"

    def _reset_shortcut(self, _event):
        if self.root.focus_get() is self.time_entry:
            return None
        self._control_activity()
        self.reset()
        return "break"

    def _apply_shortcut(self, _event):
        self._control_activity()
        self.apply_time()
        return "break"

    def _select_all(self, _event):
        self._control_activity()
        self.time_entry.selection_range(0, tk.END)
        return "break"

    def close(self):
        self.closing = True
        self.controls_generation += 1
        self._cancel_tick()
        self._cancel_control_callbacks()
        if self.fullscreen_refresh_after_id is not None:
            try:
                self.root.after_cancel(self.fullscreen_refresh_after_id)
            except tk.TclError:
                pass
            self.fullscreen_refresh_after_id = None
        if self.resize_after_id is not None:
            try:
                self.root.after_cancel(self.resize_after_id)
            except tk.TclError:
                pass
            self.resize_after_id = None
        self._end_window_drag()
        _remove_frameless_chrome(self.frameless_handle)
        self.frameless_handle = None
        self.root.destroy()


def enable_windows_dpi_awareness():
    """Use per-monitor DPI coordinates and keep text crisp on Windows."""
    if sys.platform != "win32":
        return
    try:
        setter = ctypes.windll.user32.SetProcessDpiAwarenessContext
        setter.argtypes = [ctypes.c_void_p]
        setter.restype = ctypes.c_int
        if setter(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass

    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def main():
    enable_windows_dpi_awareness()
    root = tk.Tk()
    root.withdraw()
    CountdownTimer(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()








