"""Clipboard backup, paste, and best-effort restoration behavior."""

from unittest.mock import patch

import pytest

from clipboard_injection import _previous_text, temporary_clipboard


TEXT_TARGETS = b"TARGETS\nUTF8_STRING\ntext/plain\n"
IMAGE_TARGETS = b"TARGETS\nimage/png\n"
FILE_TARGETS = b"TARGETS\ntext/uri-list\napplication/x-kde4-urilist\n"


def _clipboard_setup(monkeypatch, previous=b"original"):
    monkeypatch.setattr("clipboard_injection._xclip_path", lambda _plugin: "/bin/xclip")
    monkeypatch.setattr("clipboard_injection._clipboard_env", lambda: {"DISPLAY": ":1"})
    monkeypatch.setattr("clipboard_injection._previous_text", lambda _xclip, _env: previous)


def test_plain_text_clipboard_is_backed_up_and_restored(monkeypatch):
    _clipboard_setup(monkeypatch, previous=b"old text")
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"new phrase" if mode == "-out" else b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)

    with temporary_clipboard("new phrase", "/plugin"):
        pass

    assert operations == [
        ("-in", b"new phrase"),
        ("-out", None),
        ("-in", b"old text"),
    ]


def test_mixed_text_and_image_clipboard_saves_text_without_rejecting_image():
    target_result = type("Result", (), {"returncode": 0, "stdout": TEXT_TARGETS + b"image/png\n"})()
    with patch("clipboard_injection.subprocess.run", return_value=target_result):
        with patch("clipboard_injection._clip", return_value=b"prior text") as clip:
            assert _previous_text("xclip", {"DISPLAY": ":1"}) == b"prior text"
    clip.assert_called_once_with("xclip", {"DISPLAY": ":1"}, "-out")


@pytest.mark.parametrize("targets", [IMAGE_TARGETS, FILE_TARGETS])
def test_non_text_clipboard_targets_have_no_backup_but_do_not_raise(targets):
    target_result = type("Result", (), {"returncode": 0, "stdout": targets})()
    with patch("clipboard_injection.subprocess.run", return_value=target_result):
        with patch("clipboard_injection._clip") as clip:
            assert _previous_text("xclip", {"DISPLAY": ":1"}) is None
    clip.assert_not_called()


def test_failure_to_inspect_targets_does_not_block_paste(monkeypatch, caplog):
    _clipboard_setup(monkeypatch, previous=None)
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"dictated" if mode == "-out" else b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)
    with patch("clipboard_injection.subprocess.run", side_effect=OSError("private value")):
        with temporary_clipboard("dictated", "/plugin"):
            pass

    assert operations == [("-in", b"dictated"), ("-out", None)]
    assert "private value" not in caplog.text


def test_failure_to_read_previous_text_does_not_block_paste(monkeypatch, caplog):
    target_result = type("Result", (), {"returncode": 0, "stdout": TEXT_TARGETS})()
    with patch("clipboard_injection.subprocess.run", return_value=target_result):
        with patch("clipboard_injection._clip", side_effect=RuntimeError("sensitive text")):
            assert _previous_text("xclip", {"DISPLAY": ":1"}) is None
    assert "sensitive text" not in caplog.text


def test_non_text_clipboard_is_overwritten_for_paste_when_backup_is_missing(monkeypatch):
    _clipboard_setup(monkeypatch, previous=None)
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"dictated" if mode == "-out" else b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)

    with temporary_clipboard("dictated", "/plugin"):
        pass

    assert operations == [("-in", b"dictated"), ("-out", None)]


def test_newer_clipboard_value_is_not_overwritten(monkeypatch):
    _clipboard_setup(monkeypatch, previous=b"old text")
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"changed by another app" if mode == "-out" else b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)

    with temporary_clipboard("dictated", "/plugin"):
        pass

    assert operations == [("-in", b"dictated"), ("-out", None)]


def test_restore_failure_is_nonfatal_and_does_not_log_clipboard_text(monkeypatch, caplog):
    _clipboard_setup(monkeypatch, previous=b"private clipboard text")
    calls = []

    def clip(_binary, _env, mode, data=None):
        calls.append((mode, data))
        if mode == "-out":
            return b"private dictated text"
        if data == b"private clipboard text":
            raise RuntimeError("clipboard contents must not appear in logs")
        return b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)

    with temporary_clipboard("private dictated text", "/plugin"):
        pass

    assert calls == [
        ("-in", b"private dictated text"),
        ("-out", None),
        ("-in", b"private clipboard text"),
    ]
    assert "clipboard contents must not appear in logs" not in caplog.text
    assert "private clipboard text" not in caplog.text
    assert "private dictated text" not in caplog.text
    assert "Could not restore previous clipboard text" in caplog.text


def test_restore_is_attempted_even_if_caller_reports_paste_failure(monkeypatch):
    _clipboard_setup(monkeypatch, previous=b"old text")
    operations = []

    def clip(_binary, _env, mode, data=None):
        operations.append((mode, data))
        return b"dictated" if mode == "-out" else b""

    monkeypatch.setattr("clipboard_injection._clip", clip)
    monkeypatch.setattr("clipboard_injection.time.sleep", lambda _duration: None)

    with pytest.raises(ValueError, match="Ctrl-V"):
        with temporary_clipboard("dictated", "/plugin"):
            raise ValueError("Ctrl-V failed")

    assert operations == [
        ("-in", b"dictated"),
        ("-out", None),
        ("-in", b"old text"),
    ]


def test_failure_to_write_new_payload_is_an_injection_error(monkeypatch):
    _clipboard_setup(monkeypatch, previous=b"old text")
    entered = False

    def fail_write(_binary, _env, mode, data=None):
        if mode == "-in":
            raise RuntimeError("clipboard write failed")
        return b""

    monkeypatch.setattr("clipboard_injection._clip", fail_write)
    with pytest.raises(RuntimeError, match="clipboard write failed"):
        with temporary_clipboard("dictated", "/plugin"):
            entered = True
    assert entered is False
