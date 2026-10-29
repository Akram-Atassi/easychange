from PIL import Image

from easychange.__main__ import main


def test_convert_several_files_from_a_list(tmp_path, capsys):
    a, b = tmp_path / "a.png", tmp_path / "b.bmp"
    Image.new("RGB", (8, 8)).save(a)
    Image.new("RGB", (8, 8)).save(b)
    lst = tmp_path / "list.txt"
    lst.write_text(f"{a}\n{b}\n", encoding="utf-8")
    assert main(["--convert", "JPEG", "--files-from", str(lst)]) == 0
    assert (tmp_path / "a.jpg").exists() and (tmp_path / "b.jpg").exists()
    assert lst.exists()  # only the listener's own temporary lists are deleted


def test_list_targets(tmp_path, capsys):
    main(["--list", str(tmp_path / "x.xyz")])
    assert "(none)" in capsys.readouterr().out
