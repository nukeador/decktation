import ast
import asyncio
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from companion import runtime
from companion.protocol import ProtocolError, decode_packet, encode_context
from wow_voice_chat import WoWVoiceChat
from test_transcription_options import FakeAudio, FakeModel, FakeNumpy

CONTEXT = {"player": "Álvaro", "target": "Archivist Spearblossom", "zone": "The Waking Shores",
           "subzone": "Wingrest Embassy", "nearby": ["Мария", "Álvaro", "Archivist Spearblossom"],
           "nearby_total": 3}


def cache(now=None):
    clock = now if now is not None else [0.0]
    c = runtime.Companion("/missing", "/missing", clock=lambda: clock[0])
    c.enabled = c.dictation = True
    c.ingest(decode_packet(encode_context(CONTEXT, 1)))
    return c, clock


def test_unicode_vocabulary_prioritizes_and_deduplicates():
    assert runtime.vocabulary(CONTEXT) == ["Archivist Spearblossom", "Álvaro", "Мария", "The Waking Shores", "Wingrest Embassy"]
    huge = {"target": "界" * 160, "player": "a" * 100, "nearby": [str(n) for n in range(30)]}
    terms = runtime.vocabulary(huge)
    assert terms[0] == huge["target"]
    assert len(terms) <= 12 and len(", ".join(terms).encode()) <= 512


def test_heartbeats_duplicates_frozen_frames_and_snapshot_isolation():
    c, now = cache()
    snapshot = c.snapshot(); snapshot["nearby"].clear()
    assert c.snapshot()["nearby"]
    now[0] = 14
    c.ingest(decode_packet(encode_context(CONTEXT, 1)))
    now[0] = 15
    assert c.snapshot() is None and c.status()["state"] == "Stale"
    c.ingest(decode_packet(encode_context(CONTEXT, 2)))
    assert c.status()["state"] == "Live" and c.snapshot()
    assert not any(name in json.dumps(c.status()) for name in CONTEXT["nearby"])


def test_disable_and_preset_switch_clear_immediately(monkeypatch):
    c, _ = cache()
    c.thread = SimpleNamespace(is_alive=lambda: True)  # no capture thread required for cache tests
    c.configure(True, True, "generic")
    assert c.snapshot() is None and c.status()["state"] == "Disabled"
    c.failed = True
    c.configure(False, True, "wow")
    c.configure(True, True, "wow")
    assert not c.failed


def test_old_generation_cannot_repopulate_cache():
    c, _ = cache()
    c.generation += 1; c.clear()
    c.ingest(decode_packet(encode_context(CONTEXT, 2)), c.generation - 1)
    assert c.snapshot() is None


@pytest.mark.parametrize("language", [None, "es", "fr"])
def test_actual_whisper_arguments_use_fresh_game_names(monkeypatch, capsys, language):
    import wow_voice_chat
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    c, now = cache()
    service = WoWVoiceChat(lazy_load=True, transcription_language=language,
                          preset={"whisper_prompt": "World of Warcraft", "context_file": "legacy"})
    service.companion = c
    service.context = {"zone": "Old file location"}
    service.load_context = lambda: pytest.fail("legacy context must not be read")
    service.model = FakeModel()
    service._prepare_audio = lambda audio, rate: FakeAudio([0.0, 0.1])
    assert service.transcribe_audio([0.0, 0.1]) == "hello"
    options = service.model.kwargs
    assert options["hotwords"] == ", ".join(runtime.vocabulary(c.snapshot()))
    assert options["language"] == language
    if language:
        assert options["initial_prompt"] is None
    else:
        assert "The Waking Shores" in options["initial_prompt"]
    assert "Old file location" not in (options["initial_prompt"] or "")
    captured = capsys.readouterr().out
    assert "Álvaro" not in captured and "Archivist" not in captured
    assert service.context == {"zone": "Old file location"}
    now[0] = 16
    service.transcribe_audio([0.0, 0.1])
    assert service.model.kwargs["hotwords"] is None
    assert service.model.kwargs["initial_prompt"] == (None if language else "World of Warcraft")


def test_pipe_bounds_eof_and_incomplete_reads():
    r, w = os.pipe(); stop = threading.Event()
    try:
        os.write(w, b"x")
        with pytest.raises(ValueError): runtime.read_exact(r, 4, stop, timeout=0.01)
        stop.set()
        with pytest.raises(InterruptedError): runtime.read_exact(r, 1, stop)
        stop.clear(); os.close(w); w = -1
        with pytest.raises(EOFError): runtime.read_exact(r, 1, stop)
    finally:
        os.close(r)
        if w >= 0: os.close(w)


@pytest.mark.parametrize("magic,width,height", [(b"NOPE", 1, 1), (b"DCPF", 1089, 1), (b"DCPF", 1, 129)])
def test_reject_malformed_frame(magic, width, height):
    r, w = os.pipe()
    try:
        os.write(w, runtime.HEADER.pack(magic, width, height, time.monotonic_ns()))
        with pytest.raises(ValueError): runtime.read_frame(r, threading.Event())
    finally:
        os.close(r); os.close(w)


@pytest.mark.parametrize("process_name", ["WoW.exe", "WowB.exe", "WOWB.EXE", "WoWClassic.exe", "WoWClassic_T.exe"])
def test_process_detection_uses_desktop_uid(tmp_path, process_name):
    p = tmp_path / "123"; p.mkdir(); (p / "comm").write_text(process_name + "\n")
    assert runtime.wow_running(os.getuid(), tmp_path)
    assert not runtime.wow_running(os.getuid() + 100, tmp_path)
    (p / "comm").write_text("Other.exe")
    assert not runtime.wow_running(os.getuid(), tmp_path)


def test_helper_launch_drops_identity_and_uses_session(monkeypatch, tmp_path):
    binary = tmp_path / "capture"; binary.write_text(""); binary.chmod(0o755)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(runtime.os, "geteuid", lambda: 0)
    calls = []
    def spawn(*a, **k):
        calls.append((a, k))
        child = MagicMock(); child.wait.return_value = 0
        return child
    monkeypatch.setattr(runtime.subprocess, "Popen", spawn)
    monkeypatch.setattr(runtime.os, "set_blocking", lambda *args: None)
    account = SimpleNamespace(pw_uid=1000, pw_gid=1000, pw_dir="/home/deck", pw_name="deck")
    runtime.launch_helper(binary, account)
    assert calls[0][0][0][-1] == "--check-runtime"
    assert len(calls) == 2
    args, options = calls[1]
    assert options["user"] == options["group"] == 1000 and options["extra_groups"] == []
    assert options["env"]["DBUS_SESSION_BUS_ADDRESS"] == "unix:path=/run/user/1000/bus"
    assert "LD_PRELOAD" not in options["env"]
    assert options["stderr"] == runtime.subprocess.DEVNULL


def test_shutdown_waits_before_forcing_helper():
    c, _ = cache()
    process = MagicMock(); process.poll.return_value = None
    c.process = process
    c._terminate()
    process.send_signal.assert_called_once_with(signal.SIGTERM)
    process.wait.assert_called_once_with(timeout=15)
    process.kill.assert_not_called()
    assert c.process is None


def test_failure_latches_and_clears_context():
    c, _ = cache()
    c._fail("Error", "Capture stopped")
    assert c.failed and c.snapshot() is None


def test_persisted_toggle_and_status_rpc(tmp_path, monkeypatch):
    # Import the real backend with Decky/audio dependencies isolated.
    decky = SimpleNamespace(logger=MagicMock(), DECKY_USER_HOME=str(tmp_path),
                            DECKY_SETTINGS_DIR=str(tmp_path))
    monkeypatch.setitem(sys.modules, "decky", decky)
    monkeypatch.setenv("DECKY_PLUGIN_DIR", str(Path(__file__).parents[1]))
    monkeypatch.setattr(runtime, "desktop_account", lambda home: (_ for _ in ()).throw(ValueError()))
    spec = importlib.util.spec_from_file_location("companion_backend_test", Path(__file__).parents[1] / "backend/src/decktation_backend.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module._read_button_config()["wowCompanionEnabled"] is False
    module._write_button_config({"wowCompanionEnabled": "false"})
    assert module._read_button_config()["wowCompanionEnabled"] is False
    fake = MagicMock(); module.Plugin.companion = fake
    plugin = module.Plugin()
    assert asyncio.run(plugin.set_wow_companion_enabled(True))["success"]
    assert module._read_button_config()["wowCompanionEnabled"] is True
    fake.configure.assert_called_with(True, module.Plugin.controller_enabled, "wow")
    assert not asyncio.run(plugin.set_wow_companion_enabled("yes"))["success"]


def test_synthetic_scaled_screenshot_and_checksum():
    from companion.protocol import bytes_to_cells, decode_image
    from companion.png import Image
    import random
    packet = encode_context(CONTEXT, 42)
    width, height = 800, 128
    image = Image(width, height, bytearray([24, 29, 34]) * (width * height))
    size, ox, oy = 3.28125, 1, 39
    noise = random.Random(1)
    for index, cell in enumerate(bytes_to_cells(packet)):
        col, row = index % 128, index // 128
        for y in range(round(oy + row * size), round(oy + (row + 1) * size)):
            for x in range(round(ox + col * size), round(ox + (col + 1) * size)):
                offset = (y * width + x) * 3
                for channel, bit in enumerate((4, 2, 1)):
                    value = (225 if cell & bit else 10) + noise.randint(-8, 8)
                    image.data[offset + channel] = value
    decoded = decode_image(image)
    assert decoded.status == "valid"
    assert decoded.frame.context == decode_packet(packet).context
    damaged = bytearray(packet); damaged[-1] ^= 1
    with pytest.raises(ProtocolError, match="checksum"): decode_packet(bytes(damaged))
    with pytest.raises(ProtocolError, match="incomplete"): decode_packet(packet[:-3])


def test_missing_helper_fails_without_spawn(tmp_path):
    account = SimpleNamespace(pw_uid=1000, pw_gid=1000, pw_dir="/home/deck", pw_name="deck")
    with pytest.raises(FileNotFoundError): runtime.launch_helper(tmp_path / "missing", account)


def test_automatic_lifecycle_and_failure_does_not_retry(monkeypatch, tmp_path):
    account = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid(), pw_dir=str(tmp_path), pw_name="test")
    monkeypatch.setattr(runtime, "desktop_account", lambda home: account)
    ticks, checks, launches = [0.0], [], []
    present = [False]
    class Child:
        stdin = None
        stdout = None
        returncode = 127
        def poll(self): return self.returncode
    def launcher(*args):
        launches.append(args)
        return Child()
    def check(uid):
        checks.append(ticks[0])
        return present[0]
    c = runtime.Companion(tmp_path / "helper", str(tmp_path), clock=lambda: ticks[0],
                          launcher=launcher, game_check=check)
    # Exercise the real loop synchronously with deterministic polling waits.
    class Stop:
        def is_set(self): return ticks[0] >= 20
        def wait(self, seconds):
            ticks[0] += seconds
            if ticks[0] >= 5: present[0] = True
    c.stop_event = Stop(); c.enabled = c.dictation = True
    c._loop()
    assert len(launches) == 1 and c.failed
    assert checks[0] == 0 and checks[1] >= 5
    assert c.status()["state"] == "Unavailable"


def test_game_exit_and_return_stop_and_start_new_session(monkeypatch, tmp_path):
    account = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid(), pw_dir=str(tmp_path), pw_name="test")
    monkeypatch.setattr(runtime, "desktop_account", lambda home: account)
    ticks, launched = [0.0], []
    c = runtime.Companion(tmp_path / "capture", str(tmp_path), clock=lambda: ticks[0],
                          game_check=lambda uid: ticks[0] < 5 or ticks[0] >= 10)
    c.enabled = c.dictation = True
    class Child:
        def __init__(self):
            self.stdin = None
            self.stdout = MagicMock(); self.stdout.fileno.return_value = 100
            self.terminated = False
        def poll(self): return 0 if self.terminated else None
        def send_signal(self, sig): self.terminated = True
        def wait(self, timeout): return 0
    def launch(*args):
        child = Child(); launched.append(child); return child
    c.launcher = launch
    class Stop:
        def is_set(self): return ticks[0] >= 12
        def wait(self, seconds): ticks[0] += seconds
    c.stop_event = Stop()
    def select_fake(*args):
        ticks[0] += 0.2
        return ([], [], [])
    monkeypatch.setattr(runtime.select, "select", select_fake)
    c._loop(); c._terminate()
    assert len(launched) == 2 and all(child.terminated for child in launched)


def test_feature_off_never_launches_and_close_clears(monkeypatch):
    c, _ = cache()
    c.enabled = False
    calls = []
    c.launcher = lambda *a: calls.append(a)
    original = c.stop_event
    class Stop:
        count = 0
        def is_set(self): return self.count >= 2
        def wait(self, seconds): self.count += 1
    c.stop_event = Stop(); c._loop()
    assert not calls
    c.stop_event = original; c.close()
    assert c.snapshot() is None and c.state == "Disabled"


def test_json_escaped_lone_surrogate_is_rejected():
    from companion.protocol import encode_packet
    payload = json.dumps({"player": chr(0xD800)}).encode("ascii")
    with pytest.raises(ProtocolError, match="UTF-8"):
        decode_packet(encode_packet(1, payload))
