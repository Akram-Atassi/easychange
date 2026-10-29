"""EasyChange command line.

  EasyChange <file>             show the wheel for a file (used by the shortcut)
  EasyChange --hotkey           run the background shortcut listener (Alt+8)
  EasyChange --install          turn on the shortcut listener (and start it at login)
  EasyChange --uninstall        remove them
  EasyChange --list <file>      print the types a file can be changed to
  EasyChange --convert <file> <ext>   convert without the wheel
  EasyChange --message <text>   show the small message bar
"""
from __future__ import annotations

import argparse
import sys

from . import config


def say(text: str) -> None:
    """Print if there's a console; otherwise (windowed .exe) show a message box."""
    if sys.stdout is not None:
        print(text)
    elif sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, "EasyChange", 0x40)


def main(argv: list[str] | None = None) -> int:
    config.setup_logging()
    p = argparse.ArgumentParser(prog="EasyChange", description="Change a file's type.")
    p.add_argument("file", nargs="?")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--hotkey", action="store_true")
    g.add_argument("--install", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--list", action="store_true")
    g.add_argument("--convert", metavar="EXT")
    g.add_argument("--message", metavar="TEXT")
    a = p.parse_args(argv)

    if a.install or a.uninstall:
        from . import install
        install.require_windows()
        say(install.uninstall() if a.uninstall else install.install())
        return 0
    if a.hotkey:
        from . import hotkey
        return hotkey.run()
    if a.message:
        from . import wheel
        wheel.message(a.message)
        return 0
    if not a.file:
        p.print_help() if sys.stdout else say(__doc__)
        return 2

    from . import converters
    if a.list:
        say(", ".join(converters.targets_for(a.file)) or "(none)")
        return 0
    if a.convert:
        try:
            say(f"Saved {converters.convert(a.file, a.convert)}")
            return 0
        except converters.ConversionError as e:
            say(f"Error: {e}")
            return 1

    from . import wheel
    wheel.open_for(a.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
