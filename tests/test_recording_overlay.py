from types import SimpleNamespace
from unittest.mock import MagicMock
import json

import decktation_backend
import recording_overlay_manager
from recording_overlay_manager import RecordingOverlay


def test_resolves_decky_user_home_owner_without_assuming_account_name(monkeypatch):
    user = SimpleNamespace(
        pw_uid=2345,
        pw_gid=2345,
        pw_dir="/home/gamer",
        pw_name="gamer",
    )
    monkeypatch.setattr(recording_overlay_manager.os, "stat", lambda _path: SimpleNamespace(st_uid=2345))
    monkeypatch.setattr(recording_overlay_manager.pwd, "getpwuid", lambda uid: user if uid == 2345 else None)

    overlay = RecordingOverlay("/plugin", MagicMock(), "/home/gamer", enabled=False)

    assert overlay.session_user is user
    assert overlay._env(":1")["XDG_RUNTIME_DIR"] == "/run/user/2345"


def test_show_schedules_discovery_without_running_probe_inline(monkeypatch):
    overlay = RecordingOverlay("/plugin", MagicMock(), enabled=False)
    overlay.enabled = True
    overlay.session_user = SimpleNamespace(pw_uid=1000, pw_gid=1000)
    scheduled = MagicMock()
    monkeypatch.setattr(overlay, "_start_display_discovery", scheduled)
    monkeypatch.setattr(overlay, "_find_display", MagicMock(side_effect=AssertionError("inline probe")))

    overlay.show("compact")

    scheduled.assert_called_once_with()
    assert overlay.desired_state == "compact"


def test_discovery_uses_latest_visible_state(monkeypatch):
    overlay = RecordingOverlay("/plugin", MagicMock(), enabled=False)
    overlay.enabled = True
    overlay.session_user = SimpleNamespace(pw_uid=1000, pw_gid=1000)
    overlay.desired_state = "transcribing"
    monkeypatch.setattr(overlay, "_find_display", lambda: ":1")
    show_ready = MagicMock()
    monkeypatch.setattr(overlay, "_show_ready", show_ready)

    overlay._discover_display()

    assert overlay.display == ":1"
    show_ready.assert_called_once_with("transcribing")


def test_hide_prevents_late_discovery_from_showing_stale_state(monkeypatch):
    overlay = RecordingOverlay("/plugin", MagicMock(), enabled=False)
    overlay.enabled = True
    overlay.session_user = SimpleNamespace(pw_uid=1000, pw_gid=1000)
    overlay.desired_state = "hidden"
    monkeypatch.setattr(overlay, "_find_display", lambda: ":1")
    show_ready = MagicMock()
    monkeypatch.setattr(overlay, "_show_ready", show_ready)

    overlay._discover_display()

    assert overlay.display == ":1"
    show_ready.assert_not_called()


def test_legacy_notification_setting_migrates_to_recording_cue(tmp_path, monkeypatch):
    config_file = tmp_path / "button_config.json"
    config_file.write_text(json.dumps({"showNotifications": False}))
    monkeypatch.setattr(decktation_backend, "BUTTON_CONFIG_FILE", str(config_file))

    config = decktation_backend._read_button_config()

    assert config["recordingIndicator"] == "none"


def test_overlay_mode_keeps_legacy_notifications_flag_compatible(tmp_path, monkeypatch):
    config_file = tmp_path / "button_config.json"
    monkeypatch.setattr(decktation_backend, "BUTTON_CONFIG_FILE", str(config_file))

    written = decktation_backend._write_button_config({"recordingIndicator": "overlay"})

    assert written["recordingIndicator"] == "overlay"
    assert written["showNotifications"] is True
