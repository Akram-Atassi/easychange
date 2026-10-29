# EasyChange

Change a file's type in two keystrokes. Select a file in File Explorer, press
**Alt+8**, and a small wheel pops up on top of it with the formats it can become.
Click one, and the converted copy is saved right next to the original.

![The wheel](docs/wheel.png)

> **Alt+8 is the only way to open EasyChange.** There's no app window or tray
> icon. It waits quietly in the background until you press the shortcut.

---

## Contents

1. [What you need](#1-what-you-need)
2. [Install](#2-install): [download](#option-a-download-recommended) or [build it yourself](#option-b-build-it-yourself)
3. [Turn it on](#3-turn-it-on)
4. [How to use it](#4-how-to-use-it)
5. [Several files at once](#5-several-files-at-once)
6. [What converts to what](#6-what-converts-to-what)
7. [Optional extras (Word/PDF, audio and video)](#7-optional-extras)
8. [Changing the shortcut](#8-changing-the-shortcut)
9. [Updating, moving and uninstalling](#9-updating-moving-and-uninstalling)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. What you need

* Windows 10 or Windows 11
* About 2 minutes (or 5 if you build it yourself)

You don't need admin rights. Everything is installed for your user account only.

## 2. Install

### Option A: download (recommended)

No Python needed.

1. Go to the [**Releases page**](https://github.com/Akram-Atassi/easychange/releases/latest)
   and download **`EasyChange-windows.zip`**.
2. Tell Windows the download is OK. Otherwise it may block the program:

   ```powershell
   Unblock-File $HOME\Downloads\EasyChange-windows.zip
   ```

3. Unzip it into **`C:\Tools`**. Right-click the zip → **Extract All…** → type
   `C:\Tools` → **Extract**. You now have `C:\Tools\EasyChange\EasyChange.exe`.

   > Pick a permanent spot. EasyChange runs from wherever it is when you turn it
   > on. Avoid the Desktop or Documents if they sync to OneDrive: OneDrive can
   > move files to the cloud, and the shortcut then stops working.

Continue with [step 3](#3-turn-it-on).

### Option B: build it yourself

<details>
<summary>Show the steps</summary>

**Install Python** (skip if `py --version` already prints `Python 3.x.x`):

```powershell
winget install -e --id Python.Python.3.12
```

Or download it from <https://www.python.org/downloads/>. In the installer,
**tick "Add python.exe to PATH"** on the first screen. Then **close PowerShell
and open a new window**.

> **"Program 'python.exe' failed to run: The system cannot find the path
> specified"?** That's the Microsoft Store placeholder, not real Python. Use
> `py` instead of `python`. You can also open Settings, search **"app execution
> aliases"**, and turn off `python.exe` and `python3.exe`.

**Get the code and build it:**

1. Download the code: on the [repository page](https://github.com/Akram-Atassi/easychange),
   click **Code → Download ZIP**. Unzip it into `C:\Tools` and rename the
   `easychange-main` folder to `easychange`.
   You can also clone it with `git clone`.
2. Build it. This takes a minute or two:

   ```powershell
   cd C:\Tools\easychange
   ```

   ```powershell
   powershell -ExecutionPolicy Bypass -File build.ps1
   ```

   It should end with `Build complete!`. Yellow warnings like "...is installed
   in ... which is not on PATH" are harmless.

The program is now at `C:\Tools\easychange\dist\EasyChange\EasyChange.exe`. In
the commands below, use that path instead of `C:\Tools\EasyChange\EasyChange.exe`.

**Updating later:** if you got the code with `git clone`, one command fetches
the latest code, rebuilds and reinstalls:

```powershell
powershell -ExecutionPolicy Bypass -File update.ps1
```

</details>

## 3. Turn it on

```powershell
C:\Tools\EasyChange\EasyChange.exe --install
```

A message box confirms it's installed. From now on:

* Alt+8 works immediately.
* It starts automatically every time you log in to Windows.

## 4. How to use it

1. In File Explorer (or on your desktop), **click a file** to select it.
2. Press **Alt+8**. The wheel opens right on top of the file.
3. Pick a format:

| To... | Do this |
|---|---|
| Highlight a format | Hover over it, scroll the mouse wheel, or use the arrow keys |
| Convert | Click it, or press **Enter** (or **1–8** to pick a slot directly) |
| Cancel | **Esc**, right-click, click the middle of the wheel, or click anywhere else |
| See more formats | If there are more than 8, keep scrolling. The wheel turns, and the counter under the middle (e.g. `10/12`) shows where you are |

The middle of the wheel shows the file's current type and the type you're about
to convert to (e.g. `DOCX → PDF`).

**After converting**

* A green bar shows **"Saved report.pdf"**. Click it to open the folder with
  the new file selected.
* The new file is saved **in the same folder** as the original, with the same
  name and the new extension.
* **The original file is never changed or deleted.**
* If a file with that name already exists, it's saved as `report (2).pdf`
  instead of overwriting it.
* If something goes wrong, a red bar explains why.

**Other messages**

| Message | Meaning |
|---|---|
| **No available file types to change to** | That type of file can't be converted on your PC (see [section 6](#6-what-converts-to-what)). |
| **No file type all of these can change to** | You selected several files, and there's no format they can all become (e.g. a Word file and a photo). |
| **Select a file first** | You pressed Alt+8 in Explorer without a file selected, or with only folders selected. |

**Tips**

* Alt+8 only does something when File Explorer or the desktop is the active
  window. In every other app, Alt+8 behaves normally.
* Only the **8 above the letters** works, not numpad 8. Alt + numpad numbers is
  how Windows types special characters, so EasyChange leaves it alone.
* If the wheel can't find the file's icon on screen (rare), it opens at your
  mouse pointer instead.

## 5. Several files at once

Select several files (Ctrl+click, Shift+click or drag a box around them) and
press **Alt+8**.

* The middle of the wheel shows what you selected, e.g. **`6 PNG`** or
  **`4 FILES`** for a mix.
* The wheel only offers formats that **every** selected file can become.
* Files that are already in the chosen format are skipped. For example, choosing
  JPG with 3 PNGs and 2 JPGs selected converts only the 3 PNGs.
* While it works, the middle shows the progress, e.g. **`3/6`**.
* When it's done, the bar says **"Saved 6 files"**. If some failed, it says
  how many and why, e.g. "Saved 5, 1 failed: scan.png: Not a valid image". The
  rest are still converted.

### Combine into one PDF

When you select **several images and/or PDFs**, the wheel has an extra option,
**`1 PDF`**. It puts everything into a single PDF, called `Combined.pdf`:

* Pages are in **name order**, the same as Explorer sorts them (`scan 2` comes
  before `scan 10`).
* Each image becomes one page. PDFs keep all their pages.
* Great for turning phone photos of a document into one file.

## 6. What converts to what

The wheel only ever shows conversions that will actually work on your PC. If
something you expect is missing, you probably need one of the
[optional extras](#7-optional-extras).

| From | To | Works out of the box? |
|---|---|---|
| **Images:** png, jpg, webp, gif, bmp, tiff, ico, avif | each other, pdf | ✅ Yes |
| **iPhone photos:** heic | png, jpg, webp, avif, gif, bmp, tiff, ico, pdf | ✅ Yes |
| **Several images/PDFs** | one combined PDF | ✅ Yes |
| **PDF:** pdf | png, jpg, webp, txt | ✅ Yes |
| **Spreadsheets:** csv ↔ xlsx | | ✅ Yes |
| **Data:** csv ↔ json | | ✅ Yes |
| **Markdown:** md → html, md ↔ txt | | ✅ Yes |
| **Word:** docx → txt | | ✅ Yes |
| **PDF:** pdf | docx (editable) | Needs Microsoft Word |
| **Documents:** docx, doc, odt, rtf | pdf, txt, html, odt, rtf, doc, docx | Needs Microsoft Word **or** LibreOffice |
| **Spreadsheets:** xlsx, xls, ods, csv | pdf, xlsx, xls, ods, csv | Needs Microsoft Excel **or** LibreOffice |
| **Presentations:** pptx, ppt, odp | pdf, pptx, odp, ppt | Needs Microsoft PowerPoint **or** LibreOffice |
| **Text:** txt | docx, odt, pdf | Needs LibreOffice |
| **Audio:** mp3, wav, flac, ogg, m4a, aac, opus | each other | Needs ffmpeg |
| **Video:** mp4, mkv, mov, avi, webm | each other, gif, mp3, wav | Needs ffmpeg |

Some notes on how conversions behave:

* **"Adobe Acrobat Document" files are PDFs.** That's just the name Explorer
  shows in the *Type* column when Acrobat is your default PDF app. The file
  still ends in `.pdf`, and EasyChange treats it as a PDF. The same goes for
  "Microsoft Edge PDF Document" and similar names.
* **Phone photos come out the right way up.** Photos saved sideways with a
  "rotate me" tag are rotated properly when converted.
* **PDF → images:** a one-page PDF becomes a single image (`report.png`). A
  longer PDF becomes a folder, `report (png pages)`, with one image per page
  (`page 1.png`, `page 2.png`, ...).
* **PDF → txt** only works for PDFs with real text. Scanned PDFs are pictures of
  text, so you'll get a "No text found" message.
* **PDF → docx** uses Word's own PDF converter. Simple documents come out well,
  but complex layouts may shift.
* **Transparent images** (e.g. PNG logos) get a white background when converted
  to formats without transparency (jpg, bmp, pdf).
* **CSV files** separated by `;` or tabs are detected automatically.
* **xlsx → csv** uses the first sheet.
* **json → csv** needs the JSON to be a list of objects (a table). Anything else
  shows an error.
* **Office conversions** run in a hidden, separate copy of Word/Excel/PowerPoint,
  so documents you have open aren't affected. The first one can take a few
  seconds while Office starts up.

## 7. Optional extras

Install these to unlock more formats. EasyChange finds them automatically, with
no setup needed.

**For documents and PDFs** (if you don't have Microsoft Office): install
[LibreOffice](https://www.libreoffice.org/download/download/) (free).

**For audio and video:** install ffmpeg:

```powershell
winget install -e --id Gyan.FFmpeg
```

After installing ffmpeg, restart the background listener so it sees ffmpeg
(or just sign out and back in):

```powershell
C:\Tools\EasyChange\EasyChange.exe --install
```

## 8. Changing the shortcut

If Alt+8 clashes with another app (you'll get a message saying it's already in
use), or you just prefer another key:

1. Open this file in Notepad:

   ```powershell
   notepad $env:LOCALAPPDATA\EasyChange\config.json
   ```

2. Change the value, e.g.

   ```json
   { "hotkey": "ctrl+alt+c" }
   ```

3. Save, then restart the listener:

   ```powershell
   C:\Tools\EasyChange\EasyChange.exe --install
   ```

Shortcuts are written as modifiers + one key, joined by `+`:

* **Modifiers:** `alt`, `ctrl`, `shift` and `win`. At least one is required.
* **Key:** a letter, a digit, or `F1`–`F24`

## 9. Updating, moving and uninstalling

**Update to a new version**

1. Turn off the old one (so its files aren't locked):

   ```powershell
   C:\Tools\EasyChange\EasyChange.exe --uninstall
   ```

2. Delete the `C:\Tools\EasyChange` folder, then download and unzip the new
   version as in [step 2](#option-a-download-recommended).
3. Turn it on again:

   ```powershell
   C:\Tools\EasyChange\EasyChange.exe --install
   ```

Your shortcut setting is kept.

**Move the folder**

Run `--uninstall`, move the folder, then run `--install` from the new location.

**Turn it off / uninstall**

```powershell
C:\Tools\EasyChange\EasyChange.exe --uninstall
```

This stops Alt+8 and stops it from starting with Windows. Then delete the folder
if you want. Your settings stay in `%LOCALAPPDATA%\EasyChange` (delete that
folder too for a full cleanup).

## 10. Troubleshooting

**Nothing happens when I press Alt+8**

* Make sure File Explorer or the desktop is the active window (click on it first)
  and a **file** (not a folder) is selected.
* Use the 8 above the letters, not numpad 8.
* The listener may not be running (e.g. you moved the folder). Run
  `EasyChange.exe --install` again.
* Check Task Manager → **Details** for `EasyChange.exe`. Exactly one should be
  running in the background.

**"The shortcut ALT+8 is already used by another app"**

Another program has claimed Alt+8. Pick a different shortcut, as described in
[section 8](#8-changing-the-shortcut).

**The format I want isn't on the wheel**

It needs a program that isn't installed. Check the table in
[section 6](#6-what-converts-to-what) and install the
[extra](#7-optional-extras) it needs. With several files selected, remember the
wheel only shows formats *all* of them can become.

**A conversion failed (red bar)**

The bar shows a short reason. The full details are in the log file:

```powershell
notepad $env:LOCALAPPDATA\EasyChange\easychange.log
```

Common causes: the file is damaged, password-protected, or still open and locked
by another program.

**"Failed to start embedded python interpreter"**

Some of the program's files are missing, usually because the folder was only
partly deleted or replaced. Delete the whole `EasyChange` folder and unzip it
again (see [Updating](#9-updating-moving-and-uninstalling)).

**Windows Defender or SmartScreen warns about EasyChange.exe**

The program isn't code-signed (that costs money each year), so Windows doesn't
recognise it. Run `Unblock-File` on the zip before extracting it (see
[step 2](#option-a-download-recommended)). The code is all public in this
repository if you want to check it.

**The wheel has a coloured box around it instead of being round**

This can happen with some display or accessibility settings. It doesn't affect
how it works.

---

## For developers

Run straight from source without building:

```powershell
py -m pip install -r requirements.txt
```

```powershell
py easychange.pyw --install
```

Command-line options:

```
EasyChange.exe --install                     turn on Alt+8 (and start at login)
EasyChange.exe --uninstall                   turn everything off
EasyChange.exe --list <file> [<file> ...]    print the formats the file(s) can be converted to
EasyChange.exe --convert pdf <file> [...]    convert without the wheel
EasyChange.exe --selftest <report.txt>       check a build works (writes a report, exit code 0 = OK)
```

Run the tests:

```powershell
py -m pip install pytest
```

```powershell
py -m pytest tests
```

The Windows-only parts (Alt+8, Explorer selection, wheel position, Office) can't
be covered by automated tests. [`docs/TESTING.md`](docs/TESTING.md) has a
checklist to go through by hand before a release.

### Automatic builds and releases

[`.github/workflows/build.yml`](.github/workflows/build.yml) runs on GitHub's
Windows machines:

* **Every push to `main`:** runs the tests, builds `EasyChange.exe`, and runs
  `--selftest` on it. The zip can be downloaded from the run's **Artifacts**
  section in the **Actions** tab, for 30 days.
* **Publishing a release:** does the same, then attaches
  `EasyChange-windows.zip` to the release.

To publish a release:

1. On GitHub, go to **Releases → Draft a new release**.
2. Under **Choose a tag**, type a new version such as `v1.1.0` and pick
   **Create new tag on publish**.
3. Click **Generate release notes** (optional), then **Publish release**.
4. A few minutes later, `EasyChange-windows.zip` appears on the release. Watch
   progress in the **Actions** tab.

### Project layout

| File | What it does |
|---|---|
| `easychange/converters.py` | Every supported conversion, batches, and combining into one PDF |
| `easychange/wheel.py` | The pop-up wheel and message bars |
| `easychange/hotkey.py` | The Alt+8 listener, reading the Explorer selection, finding the icon position |
| `easychange/install.py` | Turning the listener on and off |
| `easychange/config.py` | Settings and log file locations |
| `easychange/selftest.py` | `--selftest`, used by the automatic build |
| `build.ps1` | Builds `dist\EasyChange\EasyChange.exe` with PyInstaller |
