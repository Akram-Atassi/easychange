# Launcher used by the right-click menu and the shortcut when running from source,
# and the entry script PyInstaller builds EasyChange.exe from.
import sys

from easychange.__main__ import main

sys.exit(main())
