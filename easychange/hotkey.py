"""Background listener for the global shortcut (Alt+8 by default).

Press the shortcut while a file is selected in File Explorer (or on the desktop)
and the wheel opens for that file at the mouse pointer.
"""
from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

from . import config, winutil

MOD = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
ERROR_ALREADY_EXISTS = 183


def parse_hotkey(text: str) -> tuple[int, int]:
    """'alt+8' -> (modifiers, virtual key code). Only top-row digits are used for
    digits: Alt + numpad digits is how Windows types special characters."""
    *mods, key = [p.strip().lower() for p in text.split("+")]
    if not mods:
        raise ValueError("The shortcut needs at least one modifier, e.g. alt+8")
    m = 0
    for name in mods:
        if name not in MOD:
            raise ValueError(f"Unknown modifier '{name}'")
        m |= MOD[name]
    if len(key) == 1 and key.isalnum():
        vk = ord(key.upper())
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    else:
        raise ValueError(f"Unsupported key '{key}'")
    return m, vk


def launcher_command() -> list[str]:
    """How to start EasyChange: the built .exe, or pythonw + the source launcher."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = str(pyw if pyw.exists() else sys.executable)
    return [exe, str(Path(__file__).resolve().parent.parent / "easychange.pyw")]


# --------------------------------------------------------------------------- #
# Finding the selected file in Explorer
# --------------------------------------------------------------------------- #

def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _active_tab(hwnd: int) -> int | None:
    """Windows 11 Explorer has tabs that share one top-level window; the visible
    ShellTabWindowClass child is the active one."""
    user32 = ctypes.windll.user32
    child = 0
    while True:
        child = user32.FindWindowExW(hwnd, child, "ShellTabWindowClass", None)
        if not child:
            return None
        if user32.IsWindowVisible(child):
            return child


def _tab_hwnd(window) -> int | None:
    import pythoncom
    from win32com.shell import shell
    try:
        sp = window._oleobj_.QueryInterface(pythoncom.IID_IServiceProvider)
        browser = sp.QueryService(shell.SID_STopLevelBrowser, shell.IID_IShellBrowser)
        return browser.GetWindow()
    except Exception:
        return None


def _selected_paths(doc) -> list[str]:
    try:
        items = doc.SelectedItems()
        return [items.Item(i).Path for i in range(items.Count)]
    except Exception:
        return []


def selected_files(hwnd: int) -> list[str]:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    shell_app = win32com.client.Dispatch("Shell.Application")
    cls = _class_name(hwnd)

    if cls in ("Progman", "WorkerW"):  # the desktop
        try:
            # CSIDL_DESKTOP, SWC_DESKTOP, SWFO_NEEDDISPATCH
            res = shell_app.Windows().FindWindowSW(0, pythoncom.Empty, 8, 0, 1)
            if isinstance(res, tuple):  # pywin32 may return (dispatch, hwnd)
                res = next(r for r in res if hasattr(r, "Document"))
            return _selected_paths(res.Document)
        except Exception:
            logging.exception("Could not read desktop selection")
            return []

    if cls not in ("CabinetWClass", "ExploreWClass"):
        return []
    matches = []
    for w in shell_app.Windows():
        try:
            if int(w.HWND) == hwnd:
                matches.append(w)
        except Exception:
            continue
    if len(matches) > 1:
        tab = _active_tab(hwnd)
        for w in matches:
            if tab and _tab_hwnd(w) == tab:
                return _selected_paths(w.Document)
    return _selected_paths(matches[0].Document) if matches else []


# --------------------------------------------------------------------------- #
# Where is the file's icon? (so the wheel opens right on top of it)
# --------------------------------------------------------------------------- #

_uia = None


def _automation():
    global _uia
    if _uia is None:
        import comtypes.client
        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation
        _uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
    return _uia


def icon_position(files: list[str]) -> tuple[int, int] | None:
    """Screen position of the selected file's icon in Explorer, via UI Automation
    (the accessibility API). None if it can't be found; the wheel then opens at
    the mouse pointer."""
    try:
        el = _automation().GetFocusedElement()
        name = (el.CurrentName or "").lower()
        # Explorer may hide extensions, so accept "report" as well as "report.docx".
        names = {Path(f).name.lower() for f in files} | {Path(f).stem.lower() for f in files}
        if name not in names:
            return None
        r = el.CurrentBoundingRectangle
        w, h = r.right - r.left, r.bottom - r.top
        if w <= 0 or h <= 0:
            return None
        if w > 3 * h:  # a row in Details/List view: the icon is at its left end
            return r.left + h, r.top + h // 2
        return (r.left + r.right) // 2, (r.top + r.bottom) // 2
    except Exception:
        logging.exception("Finding the icon position failed")
        return None


# --------------------------------------------------------------------------- #
# Listener loop
# --------------------------------------------------------------------------- #

def _launch(args: list[str], at: tuple[int, int] | None = None) -> None:
    ctypes.windll.user32.AllowSetForegroundWindow(-1)  # let the popup take focus
    if at:
        args = [f"--at={at[0]},{at[1]}"] + args
    subprocess.Popen(launcher_command() + args, close_fds=True)


def _file_args(files: list[str]) -> list[str]:
    if len(files) == 1:
        return [files[0]]
    # Many paths could exceed the command-line length limit; pass them in a file
    # (the wheel deletes it after reading).
    lst = config.app_dir() / f"selection-{os.getpid()}-{id(files)}.txt"
    lst.write_text("\n".join(files), encoding="utf-8")
    return ["--files-from", str(lst)]


def on_hotkey() -> None:
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    try:
        files = [p for p in selected_files(hwnd) if os.path.isfile(p)]
    except Exception:
        logging.exception("Reading the Explorer selection failed")
        files = []
    if files:
        _launch(_file_args(files), icon_position(files))
    elif _class_name(hwnd) in ("CabinetWClass", "ExploreWClass", "Progman", "WorkerW"):
        _launch(["--message", "Select a file first"])
    # In any other app the shortcut does nothing, so it doesn't get in the way.


def run() -> int:
    kernel32, user32 = ctypes.windll.kernel32, ctypes.windll.user32
    winutil.enable_dpi_awareness()  # so icon positions match the wheel's pixels
    kernel32.CreateMutexW(None, False, "Local\\EasyChangeHotkey")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        return 0  # already running

    combo = config.load().get("hotkey", config.DEFAULT_HOTKEY)
    try:
        mods, vk = parse_hotkey(combo)
    except ValueError as e:
        user32.MessageBoxW(None, f"Invalid shortcut '{combo}': {e}", "EasyChange", 0x10)
        return 1
    if not user32.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, vk):
        user32.MessageBoxW(
            None, f"The shortcut {combo.upper()} is already used by another app.\n"
                  f"Pick another one in:\n{config.path()}", "EasyChange", 0x30)
        return 1

    config.pid_file().write_text(str(os.getpid()))
    logging.info("Listening for %s", combo)
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            on_hotkey()
    user32.UnregisterHotKey(None, 1)
    return 0
