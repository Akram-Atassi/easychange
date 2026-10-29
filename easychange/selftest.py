"""`EasyChange --selftest <report>`: checks a build actually works.

GitHub Actions runs this against the built EasyChange.exe before publishing it,
which catches libraries PyInstaller forgot to bundle. It shows no windows or
message boxes; results go to the report file and the exit code (0 = all passed).
"""
from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path


def _checks(tmp: Path):
    from PIL import Image

    from . import converters as c

    def img(name, size=(40, 30), color="red"):
        p = tmp / name
        Image.new("RGB", size, color).save(p)
        return p

    def needs(ok, what):
        if not ok:
            raise RuntimeError(f"{what} is not available")

    def tk_window():
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.update()
        root.destroy()

    def heic():
        needs(c._heic_ok(), "HEIC support")
        p = tmp / "photo.heic"
        Image.new("RGB", (32, 32), "blue").save(p, "HEIF")
        c.convert(p, "jpg")

    def pdf_pages():
        pdf = c.convert(img("page.png"), "pdf")
        c.convert(pdf, "png")

    def combine():
        c.combine_pdf([img("a.png"), img("b.jpg"), c.convert(img("c.png"), "pdf")])

    def csv_xlsx():
        p = tmp / "t.csv"
        p.write_text("a;b\n1;2\n")
        c.convert(c.convert(p, "xlsx"), "csv")

    def markdown():
        p = tmp / "n.md"
        p.write_text("# hi\n")
        c.convert(p, "html")

    def docx_txt():
        import docx
        p = tmp / "d.docx"
        d = docx.Document()
        d.add_paragraph("hello")
        d.save(p)
        needs("txt" in c.targets_for(p), "docx → txt")
        c.convert(p, "txt")

    def windows_apis():
        if sys.platform != "win32":
            return
        import win32com.client  # noqa: F401  (Explorer selection, Office)
        from win32com.shell import shell  # noqa: F401

        from .hotkey import _automation
        _automation()  # UI Automation, used to open the wheel over the icon

    yield "window (Tk)", tk_window
    yield "png → jpg", lambda: c.convert(img("x.png"), "jpg")
    yield "png → avif", lambda: (needs(c._avif_ok(), "AVIF"), c.convert(img("y.png"), "avif"))
    yield "heic → jpg", heic
    yield "png → pdf → png", pdf_pages
    yield "combine into 1 pdf", combine
    yield "csv ↔ xlsx", csv_xlsx
    yield "md → html", markdown
    yield "docx → txt", docx_txt
    yield "Windows APIs", windows_apis


def run(report: str) -> int:
    lines, failed = [], 0
    with tempfile.TemporaryDirectory() as d:
        for name, check in _checks(Path(d)):
            try:
                check()
                lines.append(f"PASS  {name}")
            except Exception:
                failed += 1
                lines.append(f"FAIL  {name}\n{traceback.format_exc()}")
    lines.append(f"\n{failed} failed" if failed else "\nall passed")
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0
