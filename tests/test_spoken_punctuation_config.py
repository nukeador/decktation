import asyncio
import json
from types import SimpleNamespace

import decktation_backend as backend


def test_spoken_punctuation_defaults_and_persistence(tmp_path, monkeypatch):
    config = tmp_path / "button_config.json"
    monkeypatch.setattr(backend, "BUTTON_CONFIG_FILE", str(config))
    assert backend._read_button_config()["spokenPunctuation"] is False
    # Existing preferences survive enabling the feature.
    config.write_text(json.dumps({"transcriptionLanguage": "en", "manualSend": True}))
    monkeypatch.setattr(backend.Plugin, "voice_service", SimpleNamespace(spoken_punctuation=False))
    plugin = backend.Plugin()
    assert asyncio.run(plugin.set_spoken_punctuation(True))["success"]
    saved = json.loads(config.read_text())
    assert saved["spokenPunctuation"] is True
    assert saved["transcriptionLanguage"] == "en"
    assert saved["manualSend"] is True
    assert backend.Plugin.voice_service.spoken_punctuation is True
    assert backend._read_button_config()["spokenPunctuation"] is True
    assert asyncio.run(plugin.set_spoken_punctuation(False))["success"]
    assert backend._read_button_config()["spokenPunctuation"] is False
    assert backend.Plugin.voice_service.spoken_punctuation is False


def test_spoken_punctuation_can_be_saved_before_service_starts(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "BUTTON_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setattr(backend.Plugin, "voice_service", None)
    plugin = backend.Plugin()
    assert asyncio.run(plugin.set_spoken_punctuation(True))["success"]
    assert backend._read_button_config()["spokenPunctuation"] is True
    assert not asyncio.run(plugin.set_spoken_punctuation("false"))["success"]
    assert backend._read_button_config()["spokenPunctuation"] is True
