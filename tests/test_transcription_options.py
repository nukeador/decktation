import wow_voice_chat
from wow_voice_chat import WoWVoiceChat


class FakeWorker:
    def __init__(self, text="hello"):
        self.text = text
        self.calls = []
        self.process = type("Process", (), {"pid": 123})()

    def transcribe(self, audio, language, prompt):
        self.calls.append({"language": language, "prompt": prompt})
        return self.text


class FakeAudio(list):
    dtype = "float32"


def resident_service(text="hello", **kwargs):
    service = WoWVoiceChat(lazy_load=True, **kwargs)
    service.whisper_worker = FakeWorker(text)
    service.inference_device = "cpu"
    service.save_audio_to_wav = lambda *args, **kwargs: None
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])
    return service


def test_transcription_defaults_auto_detect_and_transcribe():
    service = resident_service()

    assert service.transcribe_audio([0.0, 0.1]) == "hello"
    assert service.whisper_worker.calls == [{"language": None, "prompt": ""}]


def test_transcription_capitalizes_standalone_i():
    service = resident_service("party i think i'm ready, i really do")

    assert service.transcribe_audio([0.0, 0.1]) == (
        "party I think I'm ready, I really do"
    )


def test_transcription_does_not_change_i_inside_words():
    service = resident_service("i use an iPhone in wiki raids")

    assert service.transcribe_audio([0.0, 0.1]) == "I use an iPhone in wiki raids"


def test_transcription_can_preselect_language():
    service = resident_service(transcription_language="fr")

    assert service.transcribe_audio([0.0, 0.1]) == "hello"
    assert service.whisper_worker.calls == [{"language": "fr", "prompt": ""}]


def test_non_english_transcription_skips_english_prompt_but_keeps_hotwords():
    service = resident_service(
        transcription_language="fa",
        preset={
            "whisper_prompt": "English-only prompt",
            "hotwords": ["Sylvanas"],
            "context_file": "wow_context.json",
        },
    )
    service.load_context = lambda: True
    service.context = {"zone": "Azeroth", "boss": "Illidan"}

    assert service.transcribe_audio([0.0, 0.1]) == "hello"

    assert service.whisper_worker.calls == [
        {"language": "fa", "prompt": "Sylvanas, Azeroth, Illidan"}
    ]


def test_setting_auto_language_restores_configured_prompt():
    service = WoWVoiceChat(
        lazy_load=True,
        transcription_language="es",
        preset={"whisper_prompt": "Game chat"},
    )

    service.set_transcription_options("auto")

    assert service.transcription_language is None
    assert service.build_prompt_from_context() == ("Game chat", None)


def test_explicit_english_uses_configured_prompt():
    service = WoWVoiceChat(
        lazy_load=True,
        transcription_language="en",
        preset={"whisper_prompt": "Game chat"},
    )

    assert service.build_prompt_from_context() == ("Game chat", None)


def test_model_load_uses_selected_model_size(monkeypatch, tmp_path):
    server = tmp_path / "whisper-server"
    server.touch()
    calls = []
    monkeypatch.setattr(wow_voice_chat, "_whisper_server_path", lambda: server)
    monkeypatch.setattr(WoWVoiceChat, "_vulkan_available", lambda self: False)
    monkeypatch.setattr(
        WoWVoiceChat, "_ensure_whisper_model",
        lambda self: tmp_path / f"ggml-{self.model_size}.bin",
    )
    monkeypatch.setattr(
        wow_voice_chat, "ResidentWhisper",
        lambda binary, model, environment, use_gpu: calls.append(
            (binary, model, use_gpu)
        ) or FakeWorker(),
    )
    service = WoWVoiceChat(lazy_load=True, model_size="small")

    assert service._load_model() is True
    assert calls == [(server, tmp_path / "ggml-small.bin", False)]
    assert service.inference_device == "cpu"


def test_model_load_falls_back_to_cpu_when_vulkan_startup_fails(monkeypatch, tmp_path):
    server = tmp_path / "whisper-server"
    server.touch()
    model = tmp_path / "ggml-base.bin"
    calls = []
    monkeypatch.setattr(wow_voice_chat, "_whisper_server_path", lambda: server)
    monkeypatch.setattr(WoWVoiceChat, "_vulkan_available", lambda self: True)
    monkeypatch.setattr(WoWVoiceChat, "_ensure_whisper_model", lambda self: model)

    def create_worker(binary, selected_model, environment, use_gpu):
        calls.append(use_gpu)
        if use_gpu:
            raise RuntimeError("Vulkan initialization failed")
        return FakeWorker()

    monkeypatch.setattr(wow_voice_chat, "ResidentWhisper", create_worker)
    service = WoWVoiceChat(lazy_load=True)

    assert service._load_model() is True
    assert calls == [True, False]
    assert service.inference_device == "cpu"


def test_set_model_size_reloads_loaded_model(monkeypatch, tmp_path):
    server = tmp_path / "whisper-server"
    server.touch()
    workers = []
    monkeypatch.setattr(wow_voice_chat, "_whisper_server_path", lambda: server)
    monkeypatch.setattr(WoWVoiceChat, "_vulkan_available", lambda self: False)
    monkeypatch.setattr(
        WoWVoiceChat, "_ensure_whisper_model",
        lambda self: tmp_path / f"ggml-{self.model_size}.bin",
    )
    def create_worker(binary, model, environment, use_gpu):
        worker = FakeWorker()
        worker.model = model
        worker.close = lambda: None
        workers.append(worker)
        return worker
    monkeypatch.setattr(wow_voice_chat, "ResidentWhisper", create_worker)
    service = WoWVoiceChat(lazy_load=True, model_size="base")

    assert service._load_model() is True
    assert service.set_model_size("medium") is True

    assert [worker.model.name for worker in workers] == [
        "ggml-base.bin", "ggml-medium.bin"
    ]
