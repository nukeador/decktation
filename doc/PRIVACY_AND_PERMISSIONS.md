# Privacy and permissions

## Local processing

Audio recording, transcription, chat parsing, and text entry run on the Steam Deck. Decktation does not upload audio, transcripts, or WoW context. The first use of a selected Whisper model downloads model files from Hugging Face; after download, transcription runs locally while the model is cached on the device.

## Optional diagnostics

**Diagnostics → Share** is off by default. When enabled, Decktation sends scrubbed error and performance data to Sentry to help diagnose problems. The data can include the plugin release, error category/type, selected game preset, whether dictation succeeded, and limited controller details such as controller family, vendor/product IDs, connection type, input backend, configured buttons, input-source count, lifecycle events, and numeric input errors.

Diagnostics exclude audio, transcript text, WoW context, credentials, controller names, serial numbers, Bluetooth addresses, individual button-press streams, IP addresses, and paths containing the local username. You can turn sharing off at any time in **Diagnostics → Share**. Sentry is not initialized while sharing is off.

## Decky permission

Decktation declares Decky’s `_root` permission for controller input and text entry:

- It reads Valve raw controller reports from `/dev/hidraw*` so Steam Deck buttons and grips work independently of a game’s Steam Input layout.
- It reads gamepad events from `/dev/input/event*` for other controllers. It does not exclusively grab devices or change their mappings.
- Its bundled `ydotoold` helper uses `/dev/uinput` to enter the transcription in the active window. The helper uses a private, owner-only socket in `/tmp` and stops when the plugin unloads.
- Transcribed text is passed to the helper as data; it is never evaluated as a shell command.

Decktation does not install system packages, modify the system filesystem, or create system services.
