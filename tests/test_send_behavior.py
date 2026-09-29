"""Preset-specific chat keys, clipboard payloads, and send timing behavior."""

import os
from contextlib import contextmanager

import pytest
from unittest.mock import MagicMock, call, patch

from wow_voice_chat import WoWVoiceChat


ENTER = ["key", "28:1", "28:0"]
PASTE = ["key", "29:1", "47:1", "47:0", "29:0"]
REAL_EXISTS = os.path.exists
PASTED_TEXT = []


@contextmanager
def _capture_clipboard(text, _plugin_dir):
    PASTED_TEXT.append(text)
    yield {}


def _mock_path_exists(path):
    if "ydotool" in str(path):
        return True
    return REAL_EXISTS(path)


@pytest.fixture(autouse=True)
def clipboard_and_ydotool(monkeypatch):
    PASTED_TEXT.clear()
    monkeypatch.setattr("wow_voice_chat.temporary_clipboard", _capture_clipboard)
    monkeypatch.setattr(os.path, "exists", _mock_path_exists)


WOW_PRESET = {
    "name": "World of Warcraft",
    "chat_open_key": "enter",
    "chat_send_key": "enter",
    "default_channel": "say",
    "channels": {"say": "/s ", "party": "/p ", "type": ""},
    "whisper_prompt": "World of Warcraft gameplay.",
}

GENERIC_PRESET = {
    "name": "Generic",
    "chat_open_key": None,
    "chat_send_key": None,
    "default_channel": "type",
    "channels": {"type": ""},
    "whisper_prompt": "",
}

GUILDWARS2_PRESET = {
    "name": "Guild Wars 2",
    "chat_open_key": "enter",
    "chat_send_key": "enter",
    "default_channel": "say",
    "channels": {
        "say": "/s ",
        "map": "/m ",
        "party": "/p ",
        "squad": "/d ",
        "team": "/t ",
        "guild": "/g ",
        "guild_one": "/g1 ",
        "whisper": "/w ",
        "type": "",
    },
}


def make_service(preset):
    return WoWVoiceChat(preset=preset, lazy_load=True)


def commands(mock_run):
    return [entry.args[0][1:] for entry in mock_run.call_args_list]


class TestWoWSendBehavior:
    @patch("subprocess.run")
    def test_say_opens_pastes_and_sends(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("hello world", channel="say")
        assert commands(mock_run) == [ENTER, PASTE, ENTER]
        assert PASTED_TEXT == ["/s hello world"]

    @patch("subprocess.run")
    def test_party_channel_prefix_is_pasted_literally(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("incoming", channel="party")
        assert PASTED_TEXT == ["/p incoming"]
        assert commands(mock_run) == [ENTER, PASTE, ENTER]

    @patch("subprocess.run")
    def test_message_is_never_sent_through_direct_type_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("hello", channel="say")
        assert all(command[0] != "type" for command in commands(mock_run))


class TestChatTiming:
    @patch("time.sleep")
    @patch("subprocess.run")
    def test_chat_open_and_send_delays_are_preserved(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=0)
        preset = {
            **WOW_PRESET,
            "chat_open_delay": 0.25,
            "chat_send_delay": 0.5,
        }
        make_service(preset).send_to_wow_chat("hello", channel="say")
        assert PASTED_TEXT == ["/s hello"]
        assert mock_sleep.call_args_list == [call(0.25), call(0.5)]


class TestGuildWars2SendBehavior:
    @pytest.mark.parametrize(
        ("channel", "command"),
        [
            ("say", "/s "),
            ("map", "/m "),
            ("party", "/p "),
            ("squad", "/d "),
            ("team", "/t "),
            ("guild", "/g "),
            ("guild_one", "/g1 "),
            ("whisper", "/w "),
        ],
    )
    @patch("subprocess.run")
    def test_channel_prefix_is_pasted_and_chat_keys_are_preserved(
        self, mock_run, channel, command
    ):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(GUILDWARS2_PRESET).send_to_wow_chat("hello", channel=channel)
        assert PASTED_TEXT == [f"{command}hello"]
        assert commands(mock_run) == [ENTER, PASTE, ENTER]

    @patch("subprocess.run")
    def test_spoken_squad_prefix_uses_squad_chat(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(GUILDWARS2_PRESET).send_to_wow_chat("squad stack on tag")
        assert PASTED_TEXT == ["/d stack on tag"]

    @patch("subprocess.run")
    def test_long_guild_number_prefix_wins_over_guild(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(GUILDWARS2_PRESET).send_to_wow_chat("guild one hello everyone")
        assert PASTED_TEXT == ["/g1 hello everyone"]


class TestRawTextChannel:
    @patch("subprocess.run")
    def test_type_channel_skips_open_and_send_enter(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("hello", channel="type")
        assert PASTED_TEXT == ["hello"]
        assert commands(mock_run) == [PASTE]

    @patch("subprocess.run")
    def test_type_channel_strips_trailing_punctuation(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("hello world.", channel="type")
        assert PASTED_TEXT == ["hello world"]


class TestGenericPreset:
    @patch("subprocess.run")
    def test_generic_never_presses_enter(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(GENERIC_PRESET).send_to_wow_chat(
            "search for something", channel="type"
        )
        assert commands(mock_run) == [PASTE]
        assert PASTED_TEXT == ["search for something"]

    @patch("subprocess.run")
    def test_generic_default_channel_pastes_without_prefix(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(GENERIC_PRESET).send_to_wow_chat("hello world")
        assert commands(mock_run) == [PASTE]
        assert PASTED_TEXT == ["hello world"]


class TestEmptyText:
    @patch("subprocess.run")
    def test_empty_text_does_not_open_chat(self, mock_run):
        make_service(WOW_PRESET).send_to_wow_chat("")
        mock_run.assert_not_called()
        assert PASTED_TEXT == []

    @patch("subprocess.run")
    def test_spoken_channel_is_parsed_before_paste(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        make_service(WOW_PRESET).send_to_wow_chat("party let's go")
        assert PASTED_TEXT == ["/p let's go"]


class TestManualSendMode:
    @patch("subprocess.run")
    def test_manual_send_opens_and_pastes_without_submit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        svc = make_service(WOW_PRESET)
        svc.manual_send = True
        svc.send_to_wow_chat("hello world", channel="say")
        assert commands(mock_run) == [ENTER, PASTE]
        assert PASTED_TEXT == ["/s hello world"]

    @pytest.mark.parametrize("channel", ["say", "party"])
    @patch("subprocess.run")
    def test_manual_send_preserves_channel_prefix(self, mock_run, channel):
        mock_run.return_value = MagicMock(returncode=0)
        svc = make_service(WOW_PRESET)
        svc.manual_send = True
        svc.send_to_wow_chat("incoming", channel=channel)
        expected = "/p incoming" if channel == "party" else "/s incoming"
        assert PASTED_TEXT == [expected]
        assert commands(mock_run) == [ENTER, PASTE]

    @patch("subprocess.run")
    def test_manual_send_type_channel_does_not_press_enter(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        svc = make_service(WOW_PRESET)
        svc.manual_send = True
        svc.send_to_wow_chat("hello", channel="type")
        assert commands(mock_run) == [PASTE]
