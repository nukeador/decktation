#!/usr/bin/env python3
"""
WoW Voice-to-Chat Service for Steam Deck
Captures voice input, transcribes with faster-whisper, and sends to WoW chat
"""

import ctypes
import gc
import os
import json
import logging
import shutil
import ssl
import sys
import re
import time
import queue
import threading
import subprocess
import tempfile
import urllib.request
import certifi
from pathlib import Path
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import wave
from audio_runtime import ensure_audio_environment
from clipboard_injection import temporary_clipboard
from resident_whisper import ResidentWhisper


def _capitalize_standalone_i(text: str) -> str:
    """Capitalize every standalone English first-person pronoun."""
    return re.sub(r"\bi\b", "I", text)


logger = logging.getLogger(__name__)


def _whisper_cli_path():
    """Resolve the executable in Decky's bin layout or beside this module."""
    configured_root = os.environ.get("DECKY_PLUGIN_DIR")
    candidates = []
    if configured_root:
        candidates.append(Path(configured_root) / "bin" / "whisper-cli")
    candidates.append(Path(__file__).resolve().parent / "whisper-cli")
    return next((path for path in candidates if path.is_file()), candidates[0])


def _download_vulkan_model(url, destination):
    # Decky's frozen Python cannot reliably locate system CA files.
    # certifi is bundled with the faster-whisper HTTP dependencies.
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context, timeout=60) as response:
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def _vulkan_environment():
    """Use host libraries rather than Decky's frozen Python runtime."""
    env = os.environ.copy()
    if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
        original = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if original:
            env["LD_LIBRARY_PATH"] = original
        else:
            env.pop("LD_LIBRARY_PATH", None)
    return env


def _format_casual_message(text: str) -> str:
    """Format text for casual gaming chat."""
    if not text:
        return text

    text = _capitalize_standalone_i(text)

    if text.endswith("."):
        text = text.rstrip(".")

    words = text.split(" ")
    first = words[0]
    if first != "I" and not (len(first) > 1 and first.isupper()):
        words[0] = first[:1].lower() + first[1:]
    return " ".join(words)


class WoWVoiceChat:
    def __init__(self, context_file="wow_context.json", sample_rate=44100, default_channel="say", lazy_load=False, test_mode=False, test_audio_file=None, preset=None, confirm_delay=0, manual_send=False, transcription_language=None, model_size="base", diagnostic_reporter=None, remember_last_channel=False, last_channel=None, channel_rememberer=None, recording_state_callback=None):
        self.preset = preset or {}
        self.diagnostic_reporter = diagnostic_reporter
        self.recording_state_callback = recording_state_callback
        self.context_file = Path(context_file)
        self.sample_rate = sample_rate  # Recording sample rate
        self.whisper_sample_rate = 16000  # Whisper expects 16kHz
        self.default_channel = self.preset.get("default_channel", default_channel)
        self.confirm_delay = confirm_delay  # seconds to wait before auto-sending (0 = disabled)
        self.manual_send = manual_send  # if True, skip final Enter press (user sends manually)
        self.remember_last_channel = remember_last_channel
        self.last_channel = last_channel
        self.channel_rememberer = channel_rememberer
        self.transcription_language = None if transcription_language in (None, "", "auto") else transcription_language
        self.model_size = model_size
        self.pending_text = None
        self._pending_timer = None
        self._pending_lock = threading.Lock()

        # Test mode: use static audio file instead of recording
        self.test_mode = test_mode
        self.test_audio_file = test_audio_file

        # Lazy model loading - only load when needed
        # Guards native model use/teardown; reentrant because nested paths call _load_model.
        self.model_lock = threading.RLock()
        self.model = None
        self.gpu_model = None
        self.gpu_enabled = False
        self.gpu_worker = None
        self.model_loading = False
        self.model_load_error = None

        # Last transcription result (for UI display)
        self.last_transcription = None
        self.last_transcription_time = None

        if not lazy_load:
            self._load_model()

        # Audio recording
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_stream = None
        self.input_channels = 1
        self.recording_lock = threading.Lock()

        # Context cache
        self.context = {}

        # Load language config for channel detection
        self._load_language_config()

        # Chat channel mappings - from preset or loaded config
        self.channel_commands = self.preset.get("channels") or self.default_channel_commands
        if self.last_channel not in self.channel_commands:
            self.last_channel = None
        self.casual_case = bool(self.preset.get("casual_case", False))

    def _report_diagnostic(self, name, error=None):
        if self.diagnostic_reporter:
            self.diagnostic_reporter(name, error)

    def _recording_transition(self, state):
        if self.recording_state_callback:
            try:
                self.recording_state_callback(state)
            except Exception:
                # Feedback must never interrupt recording or transcription.
                pass

    def _load_language_config(self):
        """Load language configuration for multi-language channel detection"""
        # Default fallback configuration
        self.default_channel_commands = {
            "say": "/s ",
            "party": "/p ",
            "raid": "/raid ",
            "guild": "/g ",
            "officer": "/o ",
            "yell": "/y ",
            "instance": "/i ",
            "whisper": "/w ",
            "reply": "/r ",
            "type": "",
        }

        self.channel_triggers = {}  # Maps trigger word -> channel name

        # Try to load language config file
        plugin_root = Path(
            os.environ.get("DECKY_PLUGIN_DIR", Path(__file__).parents[2])
        )
        config_file = plugin_root / "channel_languages.json"
        if not config_file.exists():
            # Decky's builder flattens defaults/ into the installed plugin root.
            config_file = plugin_root / "defaults" / "channel_languages.json"
        if not config_file.exists():
            # Fallback: build English-only triggers
            fallback_channels = self.preset.get("channels") or self.default_channel_commands
            for channel in fallback_channels:
                # Preset keys use underscores where the spoken form uses spaces.
                self.channel_triggers[channel.replace("_", " ")] = channel
            return

        try:
            with open(config_file) as f:
                config = json.load(f)

            # Load channel commands
            self.default_channel_commands = config.get("channel_commands", self.default_channel_commands)

            # Build trigger lookup from all enabled languages
            enabled_languages = config.get("enabled_languages", ["en"])
            languages = config.get("languages", {})

            for lang_code in enabled_languages:
                if lang_code not in languages:
                    continue

                lang_data = languages[lang_code]
                channels = lang_data.get("channels", {})

                # For each channel, map all its triggers to the channel name
                for channel_name, triggers in channels.items():
                    for trigger in triggers:
                        # Store lowercase for case-insensitive matching
                        self.channel_triggers[trigger.lower()] = channel_name

            print(f"Loaded {len(enabled_languages)} languages with {len(self.channel_triggers)} channel triggers")
        except Exception as e:
            print(f"Warning: Could not load language config: {e}")
            # Use default English-only triggers
            fallback_channels = self.preset.get("channels") or self.default_channel_commands
            for channel in fallback_channels:
                self.channel_triggers[channel.replace("_", " ")] = channel

    def _load_model(self):
        """Load the Whisper model (can be called lazily)"""
        with self.model_lock:
            if self.model is not None or self.gpu_enabled:
                return True
            if self.model_loading:
                return False

            self.model_loading = True
            try:
                # Vulkan is deliberately AMD-only for now.  That covers Steam
                # Deck, Steam Machine, and AMD-based SteamOS handhelds, while
                # retaining the known-good CPU path everywhere else.
                if self._load_vulkan_model():
                    self.model_load_error = None
                    return True
                print("Loading Whisper model...")
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                print("Model loaded!")
                self.model_load_error = None
                return True
            except Exception as e:
                print(f"Failed to load model: {e}")
                self.model_load_error = str(e)
                self._report_diagnostic("model.load_failed", e)
                return False
            finally:
                self.model_loading = False

    def unload_model(self):
        """Release Whisper and return free heap pages where the OS supports it."""
        with self.model_lock:
            self.model = None
            if self.gpu_worker:
                self.gpu_worker.close()
                self.gpu_worker = None
            self.gpu_model = None
            self.gpu_enabled = False
            self.model_load_error = None
            # Native allocators may keep freed pages; both steps are best-effort.
            gc.collect()
            try:
                # malloc_trim is glibc-only; unsupported systems still release the model above.
                malloc_trim = ctypes.CDLL("libc.so.6").malloc_trim
            except (AttributeError, OSError):
                return
            malloc_trim.argtypes = [ctypes.c_size_t]
            malloc_trim.restype = ctypes.c_int
            if malloc_trim(0):
                print("Released unused heap pages")

    def is_model_ready(self):
        """Check if model is loaded and ready"""
        return self.model is not None or self.gpu_enabled

    def _load_vulkan_model(self):
        """Prepare bundled whisper.cpp on supported AMD Vulkan hardware.

        Returning false is expected on non-AMD systems or when Vulkan is not
        usable.  The caller then loads faster-whisper's CPU implementation.
        """
        whisper_cli = _whisper_cli_path()
        amd_gpu = False
        for vendor in Path("/sys/class/drm").glob("card*/device/vendor"):
            try:
                if vendor.read_text(errors="ignore").strip().lower() == "0x1002":
                    amd_gpu = True
                    break
            except OSError as error:
                # Sandboxes and unusual DRM permissions should simply select
                # the portable CPU engine, never prevent dictation from loading.
                logger.warning("Cannot read GPU vendor at %s: %s", vendor, error)
                continue
        render_nodes = list(Path("/dev/dri").glob("renderD*"))
        if not amd_gpu or not render_nodes or not whisper_cli.is_file():
            logger.warning(
                "Vulkan skipped: AMD GPU=%s, render devices=%s, whisper-cli=%s (exists=%s)",
                amd_gpu, render_nodes, whisper_cli, whisper_cli.is_file(),
            )
            return False

        model_names = {"base": "ggml-base.bin", "small": "ggml-small.bin", "medium": "ggml-medium.bin"}
        filename = model_names[self.model_size]
        cache_dir = Path(os.environ.get("DECKY_USER_HOME", Path.home())) / ".cache" / "decktation" / "whisper.cpp"
        model = cache_dir / filename
        try:
            if not model.exists():
                cache_dir.mkdir(parents=True, exist_ok=True)
                temporary = model.with_suffix(".download")
                logger.info("Downloading Vulkan Whisper model %s to %s", self.model_size, model)
                url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{filename}"
                _download_vulkan_model(url, temporary)
                temporary.replace(model)
        except Exception as error:
            logger.warning("Vulkan Whisper unavailable; using CPU fallback: %s", error)
            return False

        try:
            self.gpu_worker = ResidentWhisper(whisper_cli.with_name('whisper-server'), model, _vulkan_environment())
        except Exception as error:
            logger.warning('Resident Vulkan startup failed; using CPU fallback: %s', error)
            return False
        self.gpu_model = model
        self.gpu_enabled = True
        logger.info("Using AMD Vulkan Whisper transcription: executable=%s model=%s", whisper_cli.with_name("whisper-server"), model)
        return True

    def _transcribe_vulkan(self, audio_input, initial_prompt, hotwords):
        """Reuse the Vulkan worker; return None when CPU fallback should be used."""
        try:
            with tempfile.TemporaryDirectory(prefix="decktation-whisper-") as directory:
                directory = Path(directory)
                wav_path = directory / "audio.wav"
                self.save_audio_to_wav(audio_input, wav_path, source_rate=self.whisper_sample_rate)
                if not self.gpu_worker:
                    raise RuntimeError('Resident worker is not loaded')
                prompt = '. '.join(part for part in (hotwords, initial_prompt) if part)
                started = time.monotonic()
                text = self.gpu_worker.transcribe(wav_path, self.transcription_language, prompt)
                logger.info('Resident Vulkan inference: pid=%s audio=%.3fs request=%.3fs text=%r',
                            self.gpu_worker.process.pid, len(audio_input)/self.whisper_sample_rate,
                            time.monotonic()-started, text.strip())
                # whisper-server wraps longer output into multiple lines. Chat
                # injection intentionally rejects control characters; convert
                # only presentation line breaks to spaces at this boundary.
                text = re.sub(r"[ \t]*[\r\n]+[ \t]*", " ", text).strip()
                return _capitalize_standalone_i(text)
        except Exception as error:
            # Do not make dictation fail because a Vulkan driver resets or a
            # future AMD device lacks a required extension.  Disable this path
            # for the remainder of the process and immediately use CPU.
            logger.warning("Vulkan Whisper failed; falling back to CPU: %s", error)
            if self.gpu_worker:
                self.gpu_worker.close()
                self.gpu_worker = None
            self.gpu_enabled = False
            self.gpu_model = None
            return None

    def get_last_transcription(self):
        """Get the last transcription result"""
        return {
            "text": self.last_transcription or "",
            "timestamp": self.last_transcription_time or 0
        }

    def set_preset(self, preset: dict):
        """Update the active game preset without restarting the service"""
        self.preset = preset
        self.default_channel = preset.get("default_channel", "say")
        self.channel_commands = preset.get("channels") or {"say": "", "type": ""}
        self.casual_case = bool(preset.get("casual_case", False))
        if self.last_channel not in self.channel_commands:
            self.last_channel = None

    def set_remember_last_channel(self, enabled, last_channel=None):
        """Configure whether unprefixed messages reuse the last spoken channel."""
        self.remember_last_channel = bool(enabled)
        self.last_channel = (
            last_channel if self.remember_last_channel and last_channel in self.channel_commands
            else None
        )

    def _parse_channel_and_text(self, text):
        """Return the parsed channel, message, and whether a channel was spoken."""
        text = text.strip()
        text_lower = text.lower()

        for trigger, channel_name in sorted(
            self.channel_triggers.items(), key=lambda item: len(item[0]), reverse=True
        ):
            prefixes = [f"{trigger}:", f"{trigger},", f"{trigger}.", f"{trigger} "]
            for prefix in prefixes:
                if text_lower.startswith(prefix) and channel_name in self.channel_commands:
                    message = text[len(prefix):].strip()
                    if self.casual_case:
                        message = _format_casual_message(message)
                    return channel_name, message, True

        channel = self.last_channel if (
            self.remember_last_channel and self.last_channel in self.channel_commands
        ) else self.default_channel
        if self.casual_case:
            text = _format_casual_message(text)
        return channel, text, False

    def set_transcription_options(self, language=None):
        """Update faster-whisper transcription options without reloading the model."""
        self.transcription_language = None if language in (None, "", "auto") else language

    def set_model_size(self, model_size):
        """Update the selected model size and reload if a model is already active."""
        with self.model_lock:
            if model_size == self.model_size:
                return True

            self.model_size = model_size
            self.model_load_error = None

            if self.model is None and not self.gpu_enabled:
                return True

            self.model = None
            if self.gpu_worker:
                self.gpu_worker.close()
                self.gpu_worker = None
            self.gpu_model = None
            self.gpu_enabled = False
            return self._load_model()

    def _confirm_delay_for(self, text: str) -> float:
        """Calculate how long to wait based on text length: 3s base + 0.4s per word, max 6s."""
        words = len(text.split())
        return min(3.0 + words * 0.4, 6.0)

    def cancel_pending(self):
        """Cancel a pending send. Returns True if there was text waiting to be sent."""
        with self._pending_lock:
            if self._pending_timer:
                self._pending_timer.cancel()
                self._pending_timer = None
            if self.pending_text:
                self.pending_text = None
                return True
            return False

    def _send_pending(self):
        """Timer callback: auto-send the pending text after the delay."""
        with self._pending_lock:
            text = self.pending_text
            self.pending_text = None
            self._pending_timer = None
        if text:
            self.send_to_wow_chat(text)

    def load_context(self):
        """Load WoW context from addon-generated file"""
        if self.context_file.exists():
            try:
                with open(self.context_file) as f:
                    self.context = json.load(f)
                return True
            except Exception as e:
                print(f"Warning: Could not load context: {e}")
        return False

    def build_prompt_from_context(self):
        """Build initial_prompt and hotwords from context"""
        # Extract preset hotwords if configured. Keep them as a list until the
        # context hotwords have also been added.
        preset_hotwords_raw = self.preset.get("hotwords") if self.preset else None
        if isinstance(preset_hotwords_raw, list):
            hotwords = [str(word).strip() for word in preset_hotwords_raw if str(word).strip()]
        elif isinstance(preset_hotwords_raw, str):
            hotwords = [preset_hotwords_raw.strip()] if preset_hotwords_raw.strip() else []
        else:
            hotwords = []

        # Experimental comparison: do not send prose/example messages, even
        # if a saved preset still contains the old English whisper_prompt.
        # Preserve explicitly configured vocabulary and actual game names.
        if not self.preset.get("context_file"):
            return None, ", ".join(hotwords) or None
        zone = self.context.get("zone", "")
        boss = self.context.get("boss", "")
        target = self.context.get("target", "")

        # Preserve the context-derived hotwords used by existing presets while
        # allowing user profiles to add their own vocabulary.
        for contextual_hotword in (zone, boss, target):
            if contextual_hotword and contextual_hotword not in hotwords:
                hotwords.append(contextual_hotword)

        return None, ", ".join(hotwords) or None

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio recording"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def _input_stream_settings(self):
        """Choose a supported input format, preferring mono when available."""
        device = sd.default.device[0]
        device_info = sd.query_devices(device, "input")
        self.sample_rate = int(device_info["default_samplerate"])
        maximum = int(device_info["max_input_channels"])
        candidates = [1]
        if maximum >= 2:
            candidates.append(2)
        if maximum > 2:
            candidates.append(maximum)

        last_error = None
        for channels in candidates:
            try:
                sd.check_input_settings(
                    device=device,
                    channels=channels,
                    samplerate=self.sample_rate,
                    dtype="int16",
                )
                self.input_channels = channels
                print(
                    f"Using input device {device}: {self.sample_rate} Hz, "
                    f"{channels} channel(s)"
                )
                return {
                    "device": device,
                    "samplerate": self.sample_rate,
                    "channels": channels,
                    "callback": self.audio_callback,
                    "dtype": "int16",
                }
            except Exception as error:
                last_error = error

        raise RuntimeError(
            f"No supported capture format for input device {device} "
            f"at {self.sample_rate} Hz (up to {maximum} channels): {last_error}"
        )

    def _open_input_stream(self):
        return sd.InputStream(**self._input_stream_settings())

    def record_audio(self, duration=5):
        """Record audio for specified duration"""
        print(f"Recording for {duration} seconds...")
        self.audio_queue = queue.Queue()

        with self._open_input_stream():
            time.sleep(duration)

        # Collect all audio
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())

        if not audio_data:
            return None

        return np.concatenate(audio_data, axis=0)

    def save_audio_to_wav(self, audio_data, filename, source_rate=None):
        """Save audio data to WAV file, resampling to 16kHz for Whisper"""
        audio_data = self._prepare_audio(audio_data, self.sample_rate if source_rate is None else source_rate)
        audio_data = np.clip(audio_data * 32768, -32768, 32767).astype(np.int16)

        with wave.open(os.fspath(filename), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.whisper_sample_rate)
            wf.writeframes(audio_data.tobytes())

    def _prepare_audio(self, audio_data, source_rate):
        """Return mono 16 kHz float32 samples for faster-whisper."""
        audio_data = np.asarray(audio_data)

        if audio_data.ndim > 1:
            # Device callbacks are frames x channels.  Mix channels before
            # resampling; flattening would interleave them and distort timing.
            if np.issubdtype(audio_data.dtype, np.integer):
                max_value = float(max(abs(np.iinfo(audio_data.dtype).min), np.iinfo(audio_data.dtype).max))
                audio_data = audio_data.astype(np.float32) / max_value
            else:
                audio_data = audio_data.astype(np.float32)
            audio_data = audio_data.mean(axis=1)
        else:
            audio_data = audio_data.reshape(-1)

        # sounddevice records int16 PCM, while faster-whisper expects float32
        # PCM in [-1, 1]. Normalize before interpolation: np.interp promotes
        # int16 to float64, which previously caused this integer check to be
        # skipped and sent values up to 32768 directly to Whisper.
        if np.issubdtype(audio_data.dtype, np.integer):
            max_value = float(max(abs(np.iinfo(audio_data.dtype).min), np.iinfo(audio_data.dtype).max))
            audio_data = audio_data.astype(np.float32) / max_value
        else:
            audio_data = audio_data.astype(np.float32)

        if source_rate != self.whisper_sample_rate and len(audio_data) > 0:
            new_length = int(len(audio_data) * self.whisper_sample_rate / source_rate)
            indices = np.linspace(0, len(audio_data) - 1, new_length)
            audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data).astype(np.float32)
        return np.clip(audio_data, -1.0, 1.0)

    def _load_wav(self, audio_file):
        """Decode the PCM WAV files used by test and CLI modes."""
        with wave.open(str(audio_file), "rb") as wav_file:
            if wav_file.getsampwidth() != 2:
                raise ValueError("Only 16-bit PCM WAV files are supported")
            channels = wav_file.getnchannels()
            source_rate = wav_file.getframerate()
            audio_data = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
        if channels > 1:
            # Averaging integers promotes them to floating point, so normalize
            # here before _prepare_audio treats them as already-normalized PCM.
            audio_data = audio_data.reshape(-1, channels).astype(np.float32)
            audio_data = audio_data.mean(axis=1) / 32768.0
        return self._prepare_audio(audio_data, source_rate)

    def transcribe_audio(self, audio_input):
        with self.model_lock:
            return self._transcribe_audio(audio_input)

    def _transcribe_audio(self, audio_input):
        """Transcribe PCM samples or a 16-bit PCM WAV file."""
        # Ensure model is loaded
        if not self._load_model():
            print("Model not ready, cannot transcribe")
            return ""

        # Load context and build prompts
        self.load_context()
        initial_prompt, hotwords = self.build_prompt_from_context()

        print(f"Context: {initial_prompt}")
        print(f"Hotwords: {hotwords}")

        if isinstance(audio_input, (str, os.PathLike, Path)):
            audio_input = self._load_wav(audio_input)
        else:
            audio_input = self._prepare_audio(audio_input, self.sample_rate)

        if len(audio_input) == 0:
            print("No audio samples to transcribe")
            return ""

        if self.gpu_enabled:
            transcript = self._transcribe_vulkan(audio_input, initial_prompt, hotwords)
            if transcript is not None:
                return transcript
            # A GPU failure after loading is handled as a normal CPU fallback.
            try:
                print("Loading CPU Whisper fallback...")
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as error:
                self.model_load_error = str(error)
                self._report_diagnostic("model.load_failed", error)
                return ""

        peak = float(np.max(np.abs(audio_input)))
        rms = float(np.sqrt(np.mean(np.square(audio_input))))
        duration = len(audio_input) / self.whisper_sample_rate
        print(
            f"Prepared audio: duration={duration:.3f}s, "
            f"peak={peak:.4f}, rms={rms:.4f}, dtype={audio_input.dtype}"
        )

        # Passing decoded samples avoids shipping PyAV and its full FFmpeg
        # codec bundle for the WAV-only Decktation recording path.
        try:
            segments, info = self.model.transcribe(
                audio_input,
                beam_size=5,
                initial_prompt=initial_prompt,
                hotwords=hotwords,
                language=self.transcription_language,
                task="transcribe",
                vad_filter=True,
                condition_on_previous_text=False,
            )

            # Segment generation is lazy and can fail during iteration.
            full_text = []
            for segment in segments:
                full_text.append(segment.text)
            return _capitalize_standalone_i("".join(full_text).strip())
        except Exception as e:
            self._report_diagnostic("transcription.failed", e)
            raise

    def parse_channel_and_text(self, text):
        """
        Parse channel prefix from text using multi-language triggers
        Supports formats like:
        - "party let's go" -> (party, "let's go")
        - "groupe allons-y" -> (party, "allons-y")
        - "party: pull boss" -> (party, "pull boss")
        - "Party, I need mana" -> (party, "I need mana")
        - "hello world" -> (default_channel, "hello world")
        """
        channel, message, _ = self._parse_channel_and_text(text)
        return channel, message

    def auto_detect_channel(self):
        """Auto-detect best channel based on context"""
        # If in raid, default to raid chat
        if self.context.get("party") and len(self.context.get("party", [])) > 5:
            return "raid"
        # If in party, default to party chat
        elif self.context.get("party") and len(self.context.get("party", [])) > 1:
            return "party"
        # Otherwise use say
        else:
            return "say"

    def send_to_wow_chat(self, text, channel=None):
        """Paste a transcription into the focused game using the clipboard."""
        if not text:
            return

        # Parse channel from text if not explicitly provided.
        if channel is None:
            channel, text, explicitly_selected = self._parse_channel_and_text(text)
            if explicitly_selected and self.remember_last_channel:
                self.last_channel = channel
                if self.channel_rememberer:
                    self.channel_rememberer(channel)

        channel_cmd = self.channel_commands.get(channel, "/s ")

        full_message = f"{channel_cmd}{text}"
        if any(ord(char) < 32 or ord(char) == 127 for char in full_message):
            self._report_diagnostic("text_injection.failed")
            return

        import logging

        logger = logging.getLogger()
        logger.info("Injecting transcription into the %s channel", channel)

        plugin_dir = os.environ.get(
            "DECKY_PLUGIN_DIR", os.path.dirname(os.path.abspath(__file__))
        )
        bundled_ydotool = os.path.join(plugin_dir, "bin", "ydotool")
        ydotool_paths = [
            bundled_ydotool,
            "/usr/bin/ydotool",
            "/usr/local/bin/ydotool",
        ]

        ydotool = next((path for path in ydotool_paths if os.path.exists(path)), None)
        if not ydotool:
            import shutil

            ydotool = shutil.which("ydotool")
        if not ydotool:
            logger.error("ydotool not found; text injection was not attempted")
            self._report_diagnostic("text_injection.failed")
            return

        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = "/tmp/decktation-ydotool.sock"

        if channel == "type":
            open_key = None
            send_key = None
        else:
            open_key = self.preset.get("chat_open_key", "enter")
            send_key = self.preset.get("chat_send_key", "enter")
            if self.manual_send:
                send_key = None

        chat_open_delay = float(self.preset.get("chat_open_delay", 0))
        chat_send_delay = float(self.preset.get("chat_send_delay", 0))

        try:
            if open_key == "enter":
                result = subprocess.run(
                    [ydotool, "key", "28:1", "28:0"],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"ydotool chat-open key failed (exit {result.returncode})"
                    )
                if chat_open_delay > 0:
                    time.sleep(chat_open_delay)

            # Paste the whole message, including any game channel prefix, so
            # punctuation is independent of the host keyboard layout.
            with temporary_clipboard(full_message, plugin_dir):
                result = subprocess.run(
                    [ydotool, "key", "29:1", "47:1", "47:0", "29:0"],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"ydotool Ctrl+V failed (exit {result.returncode})"
                    )

            if chat_send_delay > 0:
                time.sleep(chat_send_delay)

            # Only submit after the clipboard write and Ctrl+V command succeed.
            # This records command success, not confirmation that the game
            # actually consumed or displayed the pasted text.
            if send_key == "enter":
                result = subprocess.run(
                    [ydotool, "key", "28:1", "28:0"],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"ydotool chat-send key failed (exit {result.returncode})"
                    )
        except Exception as exc:
            logger.error("Text injection failed (%s)", type(exc).__name__)
            self._report_diagnostic("text_injection.failed", exc)

    def run_once(self, duration=5):
        """Record, transcribe, and send to chat once"""
        # Record audio
        audio_data = self.record_audio(duration)
        if audio_data is None:
            print("No audio recorded")
            return

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            self.save_audio_to_wav(audio_data, temp_file)

        try:
            # Transcribe
            print("Transcribing...")
            text = self.transcribe_audio(temp_file)
            print(f"Transcribed: {text}")

            # Send to chat
            if text:
                self.send_to_wow_chat(text)
        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)

    def run_continuous(self, duration=5, pause=1):
        """Run continuously, recording and transcribing"""
        print("Starting continuous voice-to-chat service...")
        print(f"Recording {duration}s clips with {pause}s pause between")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.run_once(duration)
                time.sleep(pause)
        except KeyboardInterrupt:
            print("\nStopping service...")

    def start_recording(self):
        """Start recording audio (for push-to-talk)"""
        ensure_audio_environment(sd, os.environ.get("DECKY_USER_HOME"))
        with self.recording_lock:
            if self.is_recording:
                return

            # TEST MODE: Skip actual recording
            if self.test_mode:
                self.is_recording = True
                self._recording_transition("started")
                print(f"[TEST MODE] Recording started (will use {self.test_audio_file})")
                return

            print("Recording started...")
            self.audio_queue = queue.Queue()

            stream = self._open_input_stream()
            try:
                stream.start()
            except Exception:
                stream.close()
                raise
            self.recording_stream = stream
            self.is_recording = True
            self._recording_transition("started")

    def stop_recording(self, send=True):
        """Stop recording and process audio (for push-to-talk)"""
        with self.recording_lock:
            if not self.is_recording:
                return

            self.is_recording = False

            # TEST MODE: Use static audio file instead of recorded audio
            if self.test_mode:
                self._recording_transition("stopped")
                print(f"[TEST MODE] Recording stopped, using {self.test_audio_file}")
                if self.test_audio_file and Path(self.test_audio_file).exists():
                    try:
                        print("[TEST MODE] Transcribing...")
                        text = self.transcribe_audio(self.test_audio_file)
                        print(f"[TEST MODE] Transcribed: {text}")
                        if text and send:
                            if self.confirm_delay > 0:
                                with self._pending_lock:
                                    self.pending_text = text
                                    self._pending_timer = threading.Timer(self._confirm_delay_for(text), self._send_pending)
                                    self._pending_timer.start()
                            else:
                                self.send_to_wow_chat(text)
                    except Exception as e:
                        print(f"[TEST MODE] Error: {e}")
                        self._report_diagnostic("transcription.failed", e)
                else:
                    print(f"[TEST MODE] Test audio file not found: {self.test_audio_file}")
                return

            print("Recording stopped...")

            # Stop audio stream
            if self.recording_stream:
                self.recording_stream.stop()
                self.recording_stream.close()
                self.recording_stream = None

            self._recording_transition("stopped")

            # Collect all audio
            audio_data = []
            while not self.audio_queue.empty():
                audio_data.append(self.audio_queue.get())

            if not audio_data:
                print("No audio recorded")
                return

            audio = np.concatenate(audio_data, axis=0)

            print("Transcribing...")
            text = self.transcribe_audio(audio)
            print(f"Transcribed: {text}")

            # Store last transcription result
            self.last_transcription = text
            self.last_transcription_time = time.time()

            if text and send:
                if self.confirm_delay > 0:
                    with self._pending_lock:
                        self.pending_text = text
                        self._pending_timer = threading.Timer(self._confirm_delay_for(text), self._send_pending)
                        self._pending_timer.start()
                else:
                    self.send_to_wow_chat(text)

    def abort_recording(self):
        """Stop recording and discard audio instead of transcribing or sending it."""
        with self.recording_lock:
            was_recording = self.is_recording
            self.is_recording = False

            stream = self.recording_stream
            self.recording_stream = None
            if stream:
                try:
                    stream.stop()
                finally:
                    stream.close()

            # Drop captured audio promptly so disabling does not start a
            # transcription after the model has been released.
            self.audio_queue = queue.Queue()

        self.cancel_pending()
        if was_recording:
            print("Recording aborted")
        return was_recording

    def run_push_to_talk_keyboard(self, ptt_key='`'):
        """Run in push-to-talk mode with keyboard key"""
        print(f"Push-to-talk mode: Hold '{ptt_key}' to record, release to transcribe")
        print("Press Ctrl+C to stop")

        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == ptt_key:
                    self.start_recording()
            except AttributeError:
                pass

        def on_release(key):
            try:
                if hasattr(key, 'char') and key.char == ptt_key:
                    self.stop_recording()
            except AttributeError:
                pass

        with Listener(on_press=on_press, on_release=on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nStopping service...")

    def run_daemon_mode(self, control_file="wow_voice_control.json"):
        """Run as daemon, controlled by external file (for Decky integration)"""
        control_path = Path(control_file)
        print(f"Daemon mode: Watching {control_file} for commands")
        print("Commands: {\"recording\": true/false}")
        print("Press Ctrl+C to stop")

        last_state = False

        try:
            while True:
                if control_path.exists():
                    try:
                        with open(control_path) as f:
                            control = json.load(f)
                            recording = control.get("recording", False)

                            if recording and not last_state:
                                # Start recording
                                self.start_recording()
                                last_state = True
                            elif not recording and last_state:
                                # Stop recording
                                self.stop_recording()
                                last_state = False
                    except Exception as e:
                        print(f"Error reading control file: {e}")

                time.sleep(0.1)  # Check 10 times per second
        except KeyboardInterrupt:
            print("\nStopping service...")
            if self.is_recording:
                self.stop_recording()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WoW Voice-to-Chat Service")
    parser.add_argument("--context", default="wow_context.json",
                       help="Path to WoW context JSON file")
    parser.add_argument("--mode", choices=["once", "continuous", "push-to-talk", "daemon"],
                       default="once",
                       help="Recording mode (default: once)")
    parser.add_argument("--channel", choices=["say", "party", "raid", "guild", "officer", "yell", "instance", "whisper", "reply", "auto"],
                       default="say",
                       help="Default chat channel (default: say). Use 'auto' to detect from context or voice prefix")
    parser.add_argument("--duration", type=int, default=5,
                       help="Recording duration in seconds for 'once' and 'continuous' modes (default: 5)")
    parser.add_argument("--pause", type=int, default=1,
                       help="Pause between recordings in continuous mode (default: 1)")
    parser.add_argument("--ptt-key", default="`",
                       help="Push-to-talk key for 'push-to-talk' mode (default: `)")
    parser.add_argument("--control-file", default="wow_voice_control.json",
                       help="Control file path for 'daemon' mode (default: wow_voice_control.json)")

    args = parser.parse_args()

    # Handle auto-detection
    default_channel = args.channel
    if default_channel == "auto":
        # Will auto-detect per-message based on context
        default_channel = "say"  # Fallback

    service = WoWVoiceChat(context_file=args.context, default_channel=default_channel)

    if args.mode == "once":
        service.run_once(duration=args.duration)
    elif args.mode == "continuous":
        service.run_continuous(duration=args.duration, pause=args.pause)
    elif args.mode == "push-to-talk":
        service.run_push_to_talk_keyboard(ptt_key=args.ptt_key)
    elif args.mode == "daemon":
        service.run_daemon_mode(control_file=args.control_file)
