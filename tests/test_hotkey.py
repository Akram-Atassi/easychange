import pytest

from easychange.hotkey import parse_hotkey


def test_parse_default():
    assert parse_hotkey("alt+8") == (0x1, 0x38)


def test_parse_combo_and_function_key():
    assert parse_hotkey("Ctrl + Shift + F2") == (0x2 | 0x4, 0x71)


@pytest.mark.parametrize("bad", ["8", "hyper+8", "alt+space"])
def test_parse_rejects(bad):
    with pytest.raises(ValueError):
        parse_hotkey(bad)
