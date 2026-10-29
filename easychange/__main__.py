"""EasyChange command line.

  EasyChange <file> [<file> ...]  show the wheel for the file(s) (used by the shortcut)
  EasyChange --files-from <list>  same, reading paths from a text file (one per line)
  EasyChange --hotkey             run the background shortcut listener (Alt+8)
  EasyChange --install            turn on the shortcut listener (and start it at login)
  EasyChange --uninstall          turn it off
  EasyChange --list <file>        print the types a file can be changed to
  EasyChange --convert <ext> <file> [<file> ...]   convert without the wheel
  EasyChange --message <text>     show the small message bar
  EasyChange --selftest <report>  check the build works (used by GitHub Actions)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    p.add_argument("files", nargs="*")
    p.add_argument("--files-from", metavar="LIST")
    p.add_argument("--at", metavar="X,Y", help="where to open the wheel (screen pixels)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--hotkey", action="store_true")
    g.add_argument("--install", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--list", action="store_true")
    g.add_argument("--convert", metavar="EXT")
    g.add_argument("--message", metavar="TEXT")
    g.add_argument("--selftest", metavar="REPORT")
    a = p.parse_args(argv)
    at = tuple(int(v) for v in a.at.split(",")) if a.at else None

    if a.install or a.uninstall:
        from . import install
        install.require_windows()
        say(install.uninstall() if a.uninstall else install.install())
        return 0
    if a.hotkey:
        from . import hotkey
        return hotkey.run()
    if a.selftest:
        from . import selftest
        return selftest.run(a.selftest)
    if a.message:
        from . import wheel
        wheel.message(a.message, at=at)
        return 0

    files = list(a.files)
    if a.files_from:
        lst = Path(a.files_from)
        files += [ln for ln in lst.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lst.parent == config.app_dir():  # temporary list written by the listener
            lst.unlink(missing_ok=True)
    if not files:
        p.print_help() if sys.stdout else say(__doc__)
        return 2

    from . import converters
    if a.list:
        say(", ".join(converters.shared_targets(files)) or "(none)")
        return 0
    if a.convert:
        outputs, failures = converters.convert_many(files, converters.norm_ext(a.convert))
        say("\n".join([f"Saved {o}" for o in outputs] +
                      [f"Error: {f.name}: {m}" for f, m in failures]))
        return 1 if failures else 0

    from . import wheel
    wheel.open_for(files, at=at)
    return 0


if __name__ == "__main__":
    sys.exit(main())
