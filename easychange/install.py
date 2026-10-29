"""Turns the start-at-login shortcut listener on and off.

Everything goes under HKEY_CURRENT_USER, so no admin rights are needed.
"""
from __future__ import annotations

import subprocess
import sys

from . import config
from .hotkey import launcher_command

# Right-click entry added by earlier versions; uninstall still removes it.
MENU_KEY = r"Software\Classes\*\shell\EasyChange"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "EasyChangeHotkey"


def _quote(parts: list[str]) -> str:
    return " ".join(f'"{p}"' for p in parts)


def install() -> str:
    """Start the Alt+8 listener now and every time the user logs in."""
    import winreg

    cmd = launcher_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, _quote(cmd) + " --hotkey")
    stop_listener()
    subprocess.Popen(cmd + ["--hotkey"], close_fds=True)

    combo = config.load().get("hotkey", config.DEFAULT_HOTKEY).upper()
    return f"Installed. Select a file in File Explorer and press {combo}."


def stop_listener() -> None:
    pid_file = config.pid_file()
    if pid_file.exists():
        try:
            subprocess.run(["taskkill", "/PID", pid_file.read_text().strip(), "/F"],
                           capture_output=True, creationflags=0x08000000)
        except OSError:
            pass
        pid_file.unlink(missing_ok=True)


def uninstall() -> str:
    import winreg

    for key in (MENU_KEY + r"\command", MENU_KEY):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except FileNotFoundError:
            pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, RUN_NAME)
    except FileNotFoundError:
        pass
    stop_listener()
    return "Uninstalled. Your settings are kept in " + str(config.app_dir())


def require_windows() -> None:
    if sys.platform != "win32":
        raise SystemExit("Installing the Explorer integration only works on Windows.")
