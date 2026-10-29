import json
import shutil

import pytest
from PIL import Image

from easychange import converters as c


def test_norm_ext():
    assert c.norm_ext("a/b/Photo.JPEG") == "jpg"
    assert c.norm_ext(".TIF") == "tiff"
    assert c.norm_ext("docx") == "docx"
    assert c.norm_ext("noext") == "noext"


def test_unknown_type_has_no_targets(tmp_path):
    f = tmp_path / "thing.xyz"
    f.write_text("hi")
    assert c.targets_for(f) == []


def test_targets_exclude_self_and_aliases(tmp_path):
    t = c.targets_for(tmp_path / "a.jpeg")
    assert "jpg" not in t and "png" in t and t[0] == "pdf"


def test_unique_output_path(tmp_path):
    src = tmp_path / "r.png"
    src.touch()
    (tmp_path / "r.jpg").touch()
    assert c.unique_output_path(src, "jpg").name == "r (2).jpg"


def test_png_with_alpha_to_jpg_and_pdf(tmp_path):
    src = tmp_path / "logo.png"
    Image.new("RGBA", (40, 30), (255, 0, 0, 0)).save(src)
    out = c.convert(src, "jpg")
    with Image.open(out) as im:
        assert im.format == "JPEG" and im.getpixel((0, 0)) == (255, 255, 255)
    assert c.convert(src, "pdf").read_bytes().startswith(b"%PDF")
    assert c.convert(src, "ico").exists()
    assert src.exists()  # original untouched


def test_csv_json_xlsx_roundtrip(tmp_path):
    src = tmp_path / "t.csv"
    src.write_text("name;age\nAda;36\nLin;7\n", encoding="utf-8")
    j = c.convert(src, "json")
    assert json.loads(j.read_text()) == [{"name": "Ada", "age": "36"}, {"name": "Lin", "age": "7"}]
    x = c.convert(src, "xlsx")
    back = c.convert(x, "csv")
    assert back.name == "t (2).csv"
    assert "Ada,36" in back.read_text(encoding="utf-8-sig")


def test_json_must_be_table(tmp_path):
    src = tmp_path / "x.json"
    src.write_text("[1, 2]")
    with pytest.raises(c.ConversionError, match="list of objects"):
        c.convert(src, "csv")
    assert not (tmp_path / "x.csv").exists()


def test_md_to_html(tmp_path):
    src = tmp_path / "n.md"
    src.write_text("# Hi\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    html = c.convert(src, "html").read_text()
    assert "<h1>Hi</h1>" in html and "<table>" in html


def test_docx_to_txt(tmp_path):
    import docx
    src = tmp_path / "d.docx"
    d = docx.Document()
    d.add_paragraph("Hello wheel")
    d.save(src)
    assert "txt" in c.targets_for(src)
    route = next(r for r in c.ROUTES if r.src == "docx" and r.dst == "txt"
                 and r.backend.name == "python-docx")
    out = tmp_path / "d.txt"
    route.backend.convert(src, out, "txt")
    assert out.read_text().strip() == "Hello wheel"


@pytest.mark.skipif(not c.soffice_path(), reason="LibreOffice not installed")
def test_docx_to_pdf_with_libreoffice(tmp_path):
    import docx
    src = tmp_path / "report.docx"
    d = docx.Document()
    d.add_paragraph("Quarterly report")
    d.save(src)
    assert c.targets_for(src)[0] == "pdf"
    assert c.convert(src, "pdf").read_bytes().startswith(b"%PDF")


@pytest.mark.skipif(not c.ffmpeg_path(), reason="ffmpeg not installed")
def test_wav_to_mp3(tmp_path):
    import subprocess
    src = tmp_path / "beep.wav"
    subprocess.run([c.ffmpeg_path(), "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=d=0.5", str(src)], check=True)
    assert c.convert(src, "mp3").stat().st_size > 0


def _make_pdf(path, pages):
    colors = ["red", "green", "blue", "white"]
    ims = [Image.new("RGB", (60, 80), colors[i % 4]) for i in range(pages)]
    ims[0].save(path, save_all=True, append_images=ims[1:])


def test_pdf_targets(tmp_path):
    t = c.targets_for(tmp_path / "Scan.PDF")
    assert {"png", "jpg", "webp", "txt"} <= set(t)


def test_single_page_pdf_to_png(tmp_path):
    src = tmp_path / "one.pdf"
    _make_pdf(src, 1)
    out = c.convert(src, "png")
    assert out.name == "one.png"
    with Image.open(out) as im:
        assert im.size == (120, 160)  # rendered at 2x
        r, g, b = im.convert("RGB").getpixel((60, 80))
        assert r > 240 and g < 15 and b < 15  # red (PDF stores it as JPEG)


def test_multi_page_pdf_to_jpg_makes_folder(tmp_path):
    src = tmp_path / "three.pdf"
    _make_pdf(src, 3)
    out = c.convert(src, "jpg")
    assert out.is_dir() and out.name == "three (jpg pages)"
    assert sorted(p.name for p in out.iterdir()) == ["page 1.jpg", "page 2.jpg", "page 3.jpg"]
    assert c.convert(src, "jpg").name == "three (jpg pages 2)"


def test_image_only_pdf_to_txt_explains(tmp_path):
    src = tmp_path / "scan.pdf"
    _make_pdf(src, 1)
    with pytest.raises(c.ConversionError, match="No text found"):
        c.convert(src, "txt")
    assert not (tmp_path / "scan.txt").exists()


@pytest.mark.skipif(not c.soffice_path(), reason="LibreOffice not installed")
def test_pdf_text_roundtrip(tmp_path):
    import docx
    src = tmp_path / "letter.docx"
    d = docx.Document()
    d.add_paragraph("Dear wheel, hello from page one.")
    d.save(src)
    pdf = c.convert(src, "pdf")
    assert "Dear wheel, hello from page one." in c.convert(pdf, "txt").read_text()
