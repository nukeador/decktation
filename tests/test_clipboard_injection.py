"""The temporary clipboard must restore prior text and respect newer changes."""

from unittest.mock import patch

import pytest

from clipboard_injection import _previous_text, temporary_clipboard


@patch("clipboard_injection.time.sleep")
@patch("clipboard_injection._clipboard_env", return_value={"DISPLAY": ":1"})
@patch("clipboard_injection._xclip_path", return_value="/bin/xclip")
@patch("clipboard_injection._previous_text", return_value=b"original")
def test_prior_text_restored_even_when_paste_raises(_prior, _path, _env, _sleep):
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return "über".encode()

    with patch("clipboard_injection._clip", side_effect=clip):
        with pytest.raises(ValueError):
            with temporary_clipboard("über", "/plugin"):
                raise ValueError("paste failed")
    assert operations == [
        ("-in", "über".encode()),
        ("-out", None), ("-in", b"original"),
    ]


@patch("clipboard_injection.time.sleep")
@patch("clipboard_injection._clipboard_env", return_value={"DISPLAY": ":1"})
@patch("clipboard_injection._xclip_path", return_value="/bin/xclip")
@patch("clipboard_injection._previous_text", return_value=b"original")
def test_newer_clipboard_value_is_not_overwritten(_prior, _path, _env, _sleep):
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"newer value"

    with patch("clipboard_injection._clip", side_effect=clip):
        with temporary_clipboard("über", "/plugin"):
            pass
    assert operations == [
        ("-in", "über".encode()), ("-out", None),
    ]


def test_non_text_clipboard_is_not_replaced():
    with patch("clipboard_injection.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = b"TARGETS\nUTF8_STRING\nimage/png\n"
        with pytest.raises(RuntimeError, match="non-text"):
            _previous_text("xclip", {"DISPLAY": ":1"})
    assert run.call_count == 1
