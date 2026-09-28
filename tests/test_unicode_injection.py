"""Unicode paste and ASCII compatibility at the chat injection boundary."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from wow_voice_chat import WoWVoiceChat


PRESET = {
    "name": "World of Warcraft",
    "chat_open_key": "enter",
    "chat_send_key": "enter",
    "default_channel": "say",
    "channels": {"say": "/s ", "party": "/p ", "type": ""},
}

GENERIC_PRESET = {
    "name": "Generic", "chat_open_key": None, "chat_send_key": None,
    "default_channel": "type", "channels": {"type": ""},
}


@contextmanager
def clipboard_record(text, plugin_dir, seen):
    seen.append(text)
    yield {}


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_unicode_uses_clipboard_and_keeps_channel_and_send(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    with patch("wow_voice_chat.temporary_clipboard", side_effect=lambda t, p: clipboard_record(t, p, seen)):
        svc.send_to_wow_chat("Mañana iré", channel="party")
    assert seen == ["/p Mañana iré"]
    commands = [call.args[0][1:] for call in mock_run.call_args_list]
    assert commands == [
        ["key", "28:1", "28:0"],
        ["key", "29:1", "47:1", "47:0", "29:0"],
        ["key", "28:1", "28:0"],
    ]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_unicode_manual_send_leaves_draft(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True, manual_send=True)
    with patch("wow_voice_chat.temporary_clipboard", side_effect=lambda t, p: clipboard_record(t, p, [])):
        svc.send_to_wow_chat("Lucía", channel="say")
    assert len(mock_run.call_args_list) == 2


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_generic_unicode_only_pastes_without_enter(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=GENERIC_PRESET, lazy_load=True)
    with patch("wow_voice_chat.temporary_clipboard", side_effect=lambda t, p: clipboard_record(t, p, seen)):
        svc.send_to_wow_chat("Français.", channel="type")
    assert seen == ["Français"]  # type channel trims trailing punctuation
    assert [call.args[0][1] for call in mock_run.call_args_list] == ["key"]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_clipboard_failure_does_not_send(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    diagnostic = MagicMock()
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True, diagnostic_reporter=diagnostic)
    with patch("wow_voice_chat.temporary_clipboard", side_effect=RuntimeError("unavailable")):
        svc.send_to_wow_chat("über", channel="say")
    assert len(mock_run.call_args_list) == 1  # only chat open, never send


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_ascii_stays_on_fast_type_path(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    with patch("wow_voice_chat.temporary_clipboard") as clipboard:
        svc.send_to_wow_chat("hello", channel="say")
    clipboard.assert_not_called()
    assert any(call.args[0][1] == "type" for call in mock_run.call_args_list)


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_control_character_is_rejected_before_chat_open(mock_run, _exists):
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    svc.send_to_wow_chat("line\nbreak", channel="say")
    mock_run.assert_not_called()
