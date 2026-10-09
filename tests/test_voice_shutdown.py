import asyncio
import threading
from unittest.mock import MagicMock

import decktation_backend as backend


def test_voice_cleanup_runs_once(monkeypatch):
    voice = MagicMock()
    monkeypatch.setattr(backend.Plugin, "voice_service", voice)
    monkeypatch.setattr(backend.Plugin, "_finish_dictation_trace", MagicMock())
    plugin = backend.Plugin()
    asyncio.run(plugin._shutdown_voice_service())
    asyncio.run(plugin._shutdown_voice_service())
    voice.begin_shutdown.assert_called_once()
    voice.shutdown.assert_called_once()
    assert backend.Plugin.voice_service is None


def test_stuck_audio_cleanup_does_not_block_plugin_stop(monkeypatch):
    release = threading.Event()
    started = threading.Event()
    voice = MagicMock()

    def shutdown():
        started.set()
        release.wait(5)

    voice.shutdown.side_effect = shutdown
    monkeypatch.setattr(backend.Plugin, "voice_service", voice)
    monkeypatch.setattr(backend.Plugin, "_finish_dictation_trace", MagicMock())
    # Advance only the cleanup deadline, without slowing the suite by 3 seconds.
    clock = iter([0, 4])
    monkeypatch.setattr(backend, "time", MagicMock(monotonic=lambda: next(clock)))
    try:
        asyncio.run(backend.Plugin()._shutdown_voice_service())
        assert started.wait(1)
        voice.begin_shutdown.assert_called_once()
        assert backend.Plugin.voice_service is None
    finally:
        release.set()


def test_unload_still_closes_audio_when_overlay_cleanup_fails(monkeypatch):
    voice = MagicMock()
    overlay = MagicMock()
    overlay.stop.side_effect = RuntimeError("overlay failure")
    monkeypatch.setattr(backend.Plugin, "voice_service", voice)
    monkeypatch.setattr(backend.Plugin, "recording_overlay", overlay)
    monkeypatch.setattr(backend.Plugin, "haptic_feedback", None)
    monkeypatch.setattr(backend.Plugin, "stop_controller_listener", MagicMock())
    monkeypatch.setattr(backend.Plugin, "stop_ydotoold", MagicMock())
    monkeypatch.setattr(backend.Plugin, "_finish_dictation_trace", MagicMock())
    asyncio.run(backend.Plugin()._unload())
    voice.shutdown.assert_called_once()
