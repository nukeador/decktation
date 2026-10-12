# Privacy and permissions

## Local processing

Audio recording, transcription, chat parsing, and text entry run on the Steam Deck. Decktation does not upload audio, transcripts, or WoW context. The first use of a selected Whisper model downloads model files from Hugging Face; after download, transcription runs locally while the model is cached on the device.

## Optional diagnostics

**Diagnostics → Share** is off by default. When enabled, Decktation sends scrubbed errors, performance samples, and exact application counters to Sentry. Counters record the inference backend used for each request (Vulkan or CPU), failed inference attempts, and explicit draft cancellations by source. Performance samples include audio length, audio preparation time, inference time, and total transcription time. Metrics also include the selected model size and coarse runtime categories: Steam Deck or other device, OS family and major/minor version, and processor architecture.

Diagnostics exclude audio, transcript and chat text, WoW context, credentials, hostnames, serial numbers, Bluetooth addresses, raw hardware model strings, individual button-press streams, IP addresses, full kernel versions, and paths containing the local username. You can turn sharing off at any time in **Diagnostics → Share**. Sentry is not initialized while sharing is off.

## Decky permission

Decktation declares Decky’s `_root` permission for controller input and text entry:

- It reads Valve raw controller reports from `/dev/hidraw*` so Steam Deck buttons and grips work independently of a game’s Steam Input layout.
- It reads gamepad events from `/dev/input/event*` for other controllers. It does not exclusively grab devices or change their mappings.
- Its bundled `ydotoold` helper uses `/dev/uinput` to enter the transcription in the active window. The helper uses a private, owner-only socket in `/tmp` and stops when the plugin unloads.
- Transcribed text is passed to the helper as data; it is never evaluated as a shell command.

Decktation does not install system packages, modify the system filesystem, or create system services.
