import wow_voice_chat
import io
import ssl
import wave
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_packaged_cli_without_decky_environment(monkeypatch, tmp_path):
    backend = tmp_path / "bin"
    backend.mkdir()
    cli = backend / "whisper-cli"
    cli.touch()
    monkeypatch.delenv("DECKY_PLUGIN_DIR", raising=False)
    monkeypatch.setattr(wow_voice_chat, "__file__", str(backend / "wow_voice_chat.py"))
    assert wow_voice_chat._whisper_cli_path() == cli


def test_stale_decky_path_uses_packaged_cli(monkeypatch, tmp_path):
    cli = tmp_path / "whisper-cli"
    cli.touch()
    monkeypatch.setenv("DECKY_PLUGIN_DIR", str(tmp_path / "missing"))
    monkeypatch.setattr(wow_voice_chat, "__file__", str(tmp_path / "wow_voice_chat.py"))
    assert wow_voice_chat._whisper_cli_path() == cli


def test_decky_plugin_root(monkeypatch, tmp_path):
    backend = tmp_path / "bin"
    backend.mkdir()
    cli = backend / "whisper-cli"
    cli.touch()
    monkeypatch.setenv("DECKY_PLUGIN_DIR", str(tmp_path))
    assert wow_voice_chat._whisper_cli_path() == cli


def test_model_download_uses_bundled_ca_and_verifies_tls(monkeypatch, tmp_path):
    original_context = ssl.create_default_context
    contexts = []

    def create_context(*, cafile):
        assert cafile == wow_voice_chat.certifi.where()
        context = original_context(cafile=cafile)
        contexts.append(context)
        return context

    def open_url(url, *, context, timeout):
        assert context is contexts[0]
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname
        assert timeout == 60
        return io.BytesIO(b"model bytes")

    monkeypatch.setattr(wow_voice_chat.ssl, "create_default_context", create_context)
    monkeypatch.setattr(wow_voice_chat.urllib.request, "urlopen", open_url)
    destination = tmp_path / "model.download"
    wow_voice_chat._download_vulkan_model("https://example.com/model", destination)
    assert destination.read_bytes() == b"model bytes"


def test_vulkan_writes_wav_and_keeps_prepared_sample_rate(monkeypatch, tmp_path):
    service = wow_voice_chat.WoWVoiceChat(lazy_load=True)
    service.gpu_enabled = True
    service.gpu_model = tmp_path / "model.bin"
    rates = []
    audio = MagicMock()
    service._prepare_audio = lambda data, rate: rates.append(rate) or audio
    pcm = SimpleNamespace(tobytes=lambda: b"\0\0" * 160)
    monkeypatch.setattr(wow_voice_chat.np, "clip", lambda *args: SimpleNamespace(astype=lambda dtype: pcm))
    worker = MagicMock()
    def transcribe(path, language, prompt):
        with wave.open(str(path), 'rb') as recording:
            assert recording.getframerate() == 16000
            assert recording.getnframes() == 160
        assert language is None and prompt == "Azeroth, Illidan. Game chat"
        return 'hello'
    worker.transcribe.side_effect = transcribe
    service.gpu_worker = worker
    assert service._transcribe_vulkan(audio, "Game chat", "Azeroth, Illidan") == 'hello'
    assert rates == [16000]
    assert service.gpu_enabled


def test_vulkan_passes_explicit_language(monkeypatch, tmp_path):
    service = wow_voice_chat.WoWVoiceChat(lazy_load=True, transcription_language='es')
    service.save_audio_to_wav = MagicMock()
    service.gpu_worker = MagicMock()
    service.gpu_worker.transcribe.return_value = 'hola'
    assert service._transcribe_vulkan(MagicMock(), None, 'Azeroth') == 'hola'
    assert service.gpu_worker.transcribe.call_args.args[1:] == ('es', 'Azeroth')


def test_resident_failure_closes_worker_and_selects_fallback():
    service = wow_voice_chat.WoWVoiceChat(lazy_load=True)
    service.gpu_enabled = True
    service.gpu_worker = worker = MagicMock()
    worker.transcribe.side_effect = RuntimeError('driver failure')
    service.save_audio_to_wav = MagicMock()
    assert service._transcribe_vulkan(MagicMock(), None, None) is None
    worker.close.assert_called_once()
    assert not service.gpu_enabled and service.gpu_worker is None


def test_unload_releases_resident_worker():
    service = wow_voice_chat.WoWVoiceChat(lazy_load=True)
    service.gpu_enabled = True
    service.gpu_worker = worker = MagicMock()
    service.unload_model()
    worker.close.assert_called_once()
    assert not service.gpu_enabled and service.gpu_worker is None


def test_model_change_reloads_resident_worker():
    service = wow_voice_chat.WoWVoiceChat(lazy_load=True)
    service.gpu_enabled = True
    service.gpu_worker = worker = MagicMock()
    service._load_model = MagicMock(return_value=True)
    assert service.set_model_size('small')
    worker.close.assert_called_once()
    service._load_model.assert_called_once()

def test_vulkan_restores_host_library_path(monkeypatch):
    monkeypatch.setattr(wow_voice_chat.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/_MEIdecky")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/host/lib")
    assert wow_voice_chat._vulkan_environment()["LD_LIBRARY_PATH"] == "/host/lib"
    assert wow_voice_chat.os.environ["LD_LIBRARY_PATH"] == "/tmp/_MEIdecky"


def test_vulkan_removes_frozen_library_path_without_original(monkeypatch):
    monkeypatch.setattr(wow_voice_chat.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/_MEIdecky")
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    assert "LD_LIBRARY_PATH" not in wow_voice_chat._vulkan_environment()
