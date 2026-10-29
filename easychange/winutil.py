"""Small Win32 helpers. Every function degrades gracefully on other platforms."""
from __future__ import annotations

import ctypes
import sys
import tkinter as tk

IS_WINDOWS = sys.platform == "win32"


def enable_dpi_awareness() -> None:
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def set_transparent_color(root: tk.Tk, color: str) -> bool:
    try:
        root.attributes("-transparentcolor", color)
        return True
    except tk.TclError:  # only Windows Tk supports this
        return False


def work_area(point: tuple[int, int], root: tk.Tk) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) of the monitor work area containing `point`."""
    if IS_WINDOWS:
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]
        try:
            user32 = ctypes.windll.user32
            user32.MonitorFromPoint.restype = wintypes.HMONITOR
            user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
            hmon = user32.MonitorFromPoint(wintypes.POINT(*point), 2)  # nearest monitor
            mi = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
            if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                r = mi.rcWork
                return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def force_foreground(root: tk.Tk) -> None:
    """Make sure the popup gets keyboard focus (Esc, arrows, Enter)."""
    if not IS_WINDOWS:
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
