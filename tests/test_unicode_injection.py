"""Clipboard-only text injection and safe chat submission behavior."""

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
    "name": "Generic",
    "chat_open_key": None,
    "chat_send_key": None,
    "default_channel": "type",
    "channels": {"type": ""},
}


@contextmanager
def clipboard_record(text, _plugin_dir, seen):
    seen.append(text)
    yield {}


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_ascii_uses_clipboard_paste_and_preserves_channel_prefix(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    diagnostic = MagicMock()
    svc = WoWVoiceChat(
        preset=PRESET, lazy_load=True, diagnostic_reporter=diagnostic
    )
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("hello", channel="party")

    assert seen == ["/p hello"]
    commands = [call.args[0][1:] for call in mock_run.call_args_list]
    assert commands == [
        ["key", "28:1", "28:0"],
        ["key", "29:1", "47:1", "47:0", "29:0"],
        ["key", "28:1", "28:0"],
    ]
    assert all(command[0] != "type" for command in commands)
    diagnostic.assert_not_called()


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_ascii_punctuation_and_channel_prefix_are_pasted_literally(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("Wait, it's /s? yes!", channel="say")

    assert seen == ["/s Wait, it's /s? yes!"]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_accented_and_non_latin_text_use_the_same_clipboard_path(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("Mañana 中文", channel="party")

    assert seen == ["/p Mañana 中文"]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_manual_send_leaves_ascii_message_as_draft(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True, manual_send=True)
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("hello", channel="say")

    assert seen == ["/s hello"]
    assert len(mock_run.call_args_list) == 2
    assert [call.args[0][1] for call in mock_run.call_args_list] == ["key", "key"]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_generic_ascii_text_pastes_without_pressing_enter(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=GENERIC_PRESET, lazy_load=True)
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("hello /s", channel="type")

    assert seen == ["hello /s"]
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0][1:] == [
        "key", "29:1", "47:1", "47:0", "29:0"
    ]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_generic_type_channel_preserves_trailing_punctuation(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    seen = []
    svc = WoWVoiceChat(preset=GENERIC_PRESET, lazy_load=True)
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("French.", channel="type")

    assert seen == ["French."]


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_clipboard_failure_does_not_paste_or_send(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=0)
    diagnostic = MagicMock()
    svc = WoWVoiceChat(
        preset=PRESET, lazy_load=True, diagnostic_reporter=diagnostic
    )
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=RuntimeError("unavailable"),
    ):
        svc.send_to_wow_chat("hello", channel="say")

    assert len(mock_run.call_args_list) == 1  # chat open only
    diagnostic.assert_called_once()


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_ctrl_v_failure_does_not_press_final_enter_or_retry(mock_run, _exists):
    mock_run.side_effect = [
        MagicMock(returncode=0),
        MagicMock(returncode=1, stderr="key command failed"),
    ]
    diagnostic = MagicMock()
    svc = WoWVoiceChat(
        preset=PRESET, lazy_load=True, diagnostic_reporter=diagnostic
    )
    seen = []
    with patch(
        "wow_voice_chat.temporary_clipboard",
        side_effect=lambda text, plugin: clipboard_record(text, plugin, seen),
    ):
        svc.send_to_wow_chat("hello", channel="say")

    commands = [call.args[0][1:] for call in mock_run.call_args_list]
    assert commands == [
        ["key", "28:1", "28:0"],
        ["key", "29:1", "47:1", "47:0", "29:0"],
    ]
    assert seen == ["/s hello"]
    diagnostic.assert_called_once()


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_chat_open_failure_does_not_paste_or_send(mock_run, _exists):
    mock_run.return_value = MagicMock(returncode=1, stderr="open failed")
    diagnostic = MagicMock()
    svc = WoWVoiceChat(
        preset=PRESET, lazy_load=True, diagnostic_reporter=diagnostic
    )
    with patch("wow_voice_chat.temporary_clipboard") as clipboard:
        svc.send_to_wow_chat("hello", channel="say")

    mock_run.assert_called_once()
    clipboard.assert_not_called()
    diagnostic.assert_called_once()


@patch("os.path.exists", return_value=True)
@patch("subprocess.run")
def test_control_character_is_rejected_before_chat_open(mock_run, _exists):
    svc = WoWVoiceChat(preset=PRESET, lazy_load=True)
    svc.send_to_wow_chat("line\nbreak", channel="say")
    mock_run.assert_not_called()
