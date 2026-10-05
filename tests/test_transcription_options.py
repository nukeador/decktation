from types import SimpleNamespace

import wow_voice_chat
from wow_voice_chat import WoWVoiceChat


class FakeNumpy:
    @staticmethod
    def abs(values):
        return [abs(value) for value in values]

    @staticmethod
    def max(values):
        return max(values)

    @staticmethod
    def square(values):
        return [value * value for value in values]

    @staticmethod
    def mean(values):
        return sum(values) / len(values)

    @staticmethod
    def sqrt(value):
        return value ** 0.5


class FakeModel:
    def __init__(self, text="hello"):
        self.kwargs = None
        self.text = text

    def transcribe(self, audio, **kwargs):
        self.kwargs = kwargs
        return [SimpleNamespace(text=self.text)], SimpleNamespace()


class FakeWhisperCtor:
    def __init__(self):
        self.calls = []

    def __call__(self, model_size, device, compute_type):
        self.calls.append(
            {
                "model_size": model_size,
                "device": device,
                "compute_type": compute_type,
            }
        )
        return FakeModel()


class FakeAudio(list):
    dtype = "float32"


def test_transcription_defaults_auto_detect_and_transcribe(monkeypatch):
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    service = WoWVoiceChat(lazy_load=True)
    service.model = FakeModel()
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])

    assert service.transcribe_audio([0.0, 0.1]) == "hello"

    assert service.model.kwargs["language"] is None
    assert service.model.kwargs["task"] == "transcribe"


def test_transcription_capitalizes_standalone_i(monkeypatch):
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    service = WoWVoiceChat(lazy_load=True)
    service.model = FakeModel("party i think i'm ready, i really do")
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])

    assert service.transcribe_audio([0.0, 0.1]) == (
        "party I think I'm ready, I really do"
    )


def test_transcription_does_not_change_i_inside_words(monkeypatch):
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    service = WoWVoiceChat(lazy_load=True)
    service.model = FakeModel("i use an iPhone in wiki raids")
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])

    assert service.transcribe_audio([0.0, 0.1]) == "I use an iPhone in wiki raids"


def test_transcription_can_preselect_language(monkeypatch):
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    service = WoWVoiceChat(
        lazy_load=True,
        transcription_language="fr",
    )
    service.model = FakeModel()
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])

    assert service.transcribe_audio([0.0, 0.1]) == "hello"

    assert service.model.kwargs["language"] == "fr"
    assert service.model.kwargs["task"] == "transcribe"


def test_non_english_transcription_skips_english_prompt_but_keeps_hotwords(monkeypatch):
    monkeypatch.setattr(wow_voice_chat, "np", FakeNumpy)
    service = WoWVoiceChat(
        lazy_load=True,
        transcription_language="fa",
        preset={
            "whisper_prompt": "English-only prompt",
            "hotwords": ["Sylvanas"],
            "context_file": "wow_context.json",
        },
    )
    service.model = FakeModel()
    service._prepare_audio = lambda audio, sample_rate: FakeAudio([0.0, 0.1])
    service.load_context = lambda: True
    service.context = {"zone": "Azeroth", "boss": "Illidan"}

    assert service.transcribe_audio([0.0, 0.1]) == "hello"

    assert service.model.kwargs["language"] == "fa"
    assert service.model.kwargs["task"] == "transcribe"
    assert service.model.kwargs["initial_prompt"] is None
    assert service.model.kwargs["hotwords"] == "Sylvanas, Azeroth, Illidan"


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


def test_model_load_uses_selected_model_size(monkeypatch):
    fake_ctor = FakeWhisperCtor()
    monkeypatch.setattr(wow_voice_chat, "WhisperModel", fake_ctor)

    service = WoWVoiceChat(lazy_load=True, model_size="small")

    assert service._load_model() is True
    assert fake_ctor.calls == [
        {"model_size": "small", "device": "cpu", "compute_type": "int8"}
    ]


def test_set_model_size_reloads_loaded_model(monkeypatch):
    fake_ctor = FakeWhisperCtor()
    monkeypatch.setattr(wow_voice_chat, "WhisperModel", fake_ctor)

    service = WoWVoiceChat(lazy_load=True, model_size="base")

    assert service._load_model() is True
    assert service.set_model_size("medium") is True

    assert [call["model_size"] for call in fake_ctor.calls] == ["base", "medium"]
