# Manual testing checklist

Automated tests (`py -m pytest tests`) and the build's `--selftest` cover the
conversions. The parts below depend on Windows itself (Explorer, the desktop,
Office, the screen), so check them by hand before publishing a release.

Use the build you're about to release, turned on with `EasyChange.exe --install`.

## Opening the wheel

- [ ] Alt+8 with a file selected in an Explorer window opens the wheel **on top
      of the file's icon**, in each view: **Large icons**, **List** and **Details**.
- [ ] With **two Explorer tabs** open (Windows 11), Alt+8 uses the file selected
      in the tab you're looking at.
- [ ] Alt+8 on a file **on the desktop** works.
- [ ] Explorer set to **hide file extensions** still opens the wheel over the icon.
- [ ] Alt+8 with nothing selected, or only a folder, shows **"Select a file first"**.
- [ ] Alt+8 in another app (e.g. Notepad) does nothing, and Alt+8 still works there
      as usual.
- [ ] Alt+**numpad** 8 still types `◘` in Notepad (EasyChange must not take it).
- [ ] On a second monitor, the wheel opens on that monitor and stays fully on screen.

## The wheel

- [ ] It's **round**, with no dark square around it.
- [ ] Hover highlights, scrolling moves the highlight, and the arrow keys and 1–8 work.
- [ ] Esc, right-click, clicking the centre and clicking elsewhere all close it.
- [ ] A file type with nothing to convert to (e.g. `.zip`) shows
      **"No available file types to change to"**.

## Conversions that need Windows apps

- [ ] docx → pdf (Word)
- [ ] pdf → docx (Word)
- [ ] xlsx → pdf (Excel)
- [ ] pptx → pdf (PowerPoint)
- [ ] With Word **already open** on another document, converting doesn't touch it.
- [ ] mp4 → mp3 (only if ffmpeg is installed)

## Several files

- [ ] Selecting 5 photos and choosing JPG converts them all, showing `n/5` progress
      and then "Saved 5 files".
- [ ] Selecting images + a PDF and choosing **1 PDF** makes `Combined.pdf` in
      name order.
- [ ] An iPhone **.heic** photo converts to JPG the right way up.
- [ ] Selecting ~200 files works. The file list is passed in a temporary file,
      so the command line doesn't get too long.

## Install / uninstall

- [ ] After restarting the PC, Alt+8 works without running `--install` again.
- [ ] `--uninstall` stops Alt+8 (no `EasyChange.exe` left in Task Manager).
- [ ] Changing the shortcut in `config.json` and running `--install` uses the
      new shortcut.
