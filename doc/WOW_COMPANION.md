# Experimental WoW Companion context

The **WoW Companion context** option is off by default. With the WoW preset and dictation enabled, Decktation automatically starts its bundled capture helper when a WoW process owned by the desktop user is detected. No separate reader, system Python packages, root capture, or SteamOS installation changes are required. The WoW addon must still be installed manually.

## Addon and setup

Install [WoW Context Bridge](https://github.com/nukeador/wow-context-bridge/releases), Retail tested with unverified Forever beta compatibility. Download the named addon ZIP, extract its `WoWContextBridge` folder into the client's `Interface/AddOns/` (`_retail_` for Retail, typically `_classic_beta_` for Forever), and enable it in WoW. Remove the earlier `CompanionPoC` addon if present. Restart WoW if the new folder is not discovered by `/reload`. Enable appropriate friendly/enemy nameplates in WoW settings. The addon is maintained separately and is not installed automatically by Decktation. The older SavedVariables addon does not supply this pixel stream.

The tested addon emits protocol v2 using opaque 3×3 nominal pixel cells at top-left, with player, target, zone, subzone and a bounded nameplate list. V1 packets are also accepted. Nameplate visibility and Retail restrictions limit coverage; an overhead name alone need not provide a readable token. Up to eight names fit the current payload; the total is the count in a bounded readable scan, not a census of nearby units. No distance or player/NPC classification is promised. This implementation does not automate gameplay or bypass restricted API values. Blizzard has not explicitly approved this communication technique.

Enable the option in Decktation's **WoW Companion (experimental)** section. If the portal requests screen-sharing permission, approve it manually. Keep WoW in the foreground and the pixel strip unobstructed. Status shows freshness and a vocabulary count, never names. Another foreground application may obscure the strip; after 15 seconds without an advancing sequence, its context is ignored. Opening the Quick Access Menu can temporarily obstruct capture.

Capture failure is latched: toggle Companion off/on to retry. There is no automatic failure-reconnect loop. Leaving WoW, disabling dictation, changing preset, disabling Companion or unloading the plugin stops capture and clears its cache (game detection checks are spaced five seconds apart). Native teardown gets up to 15 seconds before forced termination. Missing helper/session/runtime libraries produce an unavailable/error status and never trigger package installation. Disabling the option restores existing legacy-context behavior.

## Vocabulary and privacy

Each transcription snapshots only fresh context. Hotwords prioritize target, player, nearby names, zone and subzone, deduplicate terms, and stay within 12 terms/512 UTF-8 bytes including separators. Terms remain in the game language: English names are supplied even when speech language is Spanish. Explicit language selection still suppresses the English prose game prompt. Automatic language mode keeps the preset prompt and appends fresh location text.

When Companion is enabled, stale/unavailable data falls back to ordinary preset transcription rather than an old SavedVariables file. The new reader doesn't update chat-channel selection or send game actions. Vocabulary hints are advisory; recognition improvement has not been measured.

Frames travel over a private inherited pipe; names stay in backend memory. No screenshot, name-bearing context file, vocabulary log or network transmission is created. Prompt/hotword console logging is removed, including for the legacy path. This does not change the plugin's existing transcription-output behavior or transcript visibility.

## Shared interface

The separate Companion implementation may reuse these components without Decky: `backend/src/companion/{protocol,png}.py` and `backend/native/companion/`. Their code is MIT licensed under this repository's license, derived from our standalone POC. The addon remains separate. Reference projects informed the POC; no source from those projects is included in this change.

Opt-in setting: `wowCompanionEnabled` (boolean, default false). RPC: `set_wow_companion_enabled(enabled)`. `get_status().companion` returns `state`, optional `age_seconds`, `vocabulary_count`, and a fixed sanitized `detail`. States: Disabled, Waiting for WoW, Connecting, Live, Stale, Unavailable, Error. Disabled also covers a non-WoW preset or disabled dictation.

Native stdout carries `DCP2`, width:u16, height:u16, CLOCK_MONOTONIC timestamp:u64, source width:u16, source height:u16, crop x:u16, crop y:u16, then tightly packed RGB bytes; all integers big-endian. Legacy `DCPF` frames remain accepted. Full-frame discovery supports captures up to 8192×4320 and at most 16,777,216 pixels; 3840×2160 is within bounds. Sampling remains every five seconds. Parent stdin carries fixed 16-byte `DCPR` requests (source width/height, crop x/y/width/height as six u16 values). After discovery, only the strip region is copied; a resolution mismatch returns a full frame. A failed decode requests rediscovery without reopening the portal. Discovery searches 2–32-pixel cells with bounded work (two seconds/100,000 candidate checks); successful geometry is reused. Extreme downscaling, obstruction and scene noise can still prevent decoding. Discovery temporarily uses more memory/CPU than cropped operation. Synthetic and native mock checks cover these changes; hardware scaling validation remains required. Reads and writes are bounded. Diagnostic stderr is discarded by Decktation. The addon optical protocol uses magic D3 71, version:u8, sequence:u16, payload byte length:u16, UTF-8 JSON (at most 256 bytes), then Fletcher-16 s1/s2 covering version through payload. V2 adds `nearby` and `nearby_total`; see the decoder for schema validation. Every advancing sequence refreshes freshness, including unchanged-context heartbeats. Duplicate sequences do not.

The native helper implements ScreenCast/CreateSession/SelectSources/Start/OpenPipeWireRemote directly with GIO. It uses a numeric node ID for portals without `pipewire-serial` (including the tested v5 Deck), or `target.object` plus PW_ID_ANY when a serial is returned. It requests MemFd buffers, queues each consumed buffer, disconnects and waits for core sync barriers before releasing the portal session. Sampling every five seconds does not guarantee Gamescope produces buffers at that rate; the earlier POC received many more buffers despite its 2 fps request.

## Build and validation

The plugin Docker build compiles the helper in a Debian Bookworm stage with GCC, GLib/GIO and PipeWire headers. Only the executable, decoder and license notices are added to the runtime package. It dynamically uses SteamOS's existing GLib/GIO/PipeWire libraries, built against a conservative baseline. No GStreamer or PyGObject runtime is needed. Native/helper code is bundled by `backend/entrypoint.sh` with the usual Decky build.

Local checks cover decoding and fractional scaling, Unicode vocabulary and budget, actual mocked Whisper arguments for selected languages, stale/duplicate heartbeat handling, failure latching, identity/environment isolation, process detection, shutdown, bounded incomplete reads, persisted settings and RPC behavior. Native compilation/root refusal and package-stage checks are separate from physical validation.

The integrated helper has decoded live Retail context on a physical Steam Deck in Gaming Mode. Supervised testing reported successful nearby-name dictation without targeting and Spanish speech containing English names; these are observations, not controlled recognition benchmarks. The cleaned WoW Context Bridge addon was also installed and reported working. A 30-second process sample after roughly 28 minutes of capture showed stable helper memory (~18 MiB), essentially flat backend memory (~324 MiB) and no matching recent crash indicators. This short sample cannot rule out slow leaks or establish long-session stability. Earlier native experiments coincided with Gamescope crashes, so broader supervised QA remains necessary.

### Hardware QA checklist

1. With integration off, confirm current dictation behavior. With WoW closed, enable Companion and verify Waiting for WoW.
2. Open Retail with WoW Context Bridge, enable dictation/WoW preset, grant portal permission if requested; confirm Live and a nonzero vocabulary count. Start with 30 seconds, inspect game/Gamescope health and CPU before extending duration.
3. Manually change/clear targets and move between visible nameplates. Compare decoded context using a temporary supervised diagnostic if needed; do not persist names. Change zone and verify the location vocabulary changes.
4. Disable pixel output with `/wcb off`, wait at least 15 seconds, verify Stale and transcription without dynamic hints. Re-enable output and verify recovery within the same session.
5. Switch away from WoW and return, then change resolution/scaling. Verify absence of old hints while stale and restored freshness. Exit/relaunch WoW, change preset, toggle dictation/integration and unload the plugin: check cleanup and absence of orphan helpers. Induce helper failure and confirm it doesn't retry automatically.
6. Compare the same recorded phrases with integration off/on, including Spanish speech containing English NPC/player names. Measure actual word/name accuracy, capture overhead and frame-time impact. Five-second sampling adds up to roughly five seconds plus addon/decoder time; capture-to-decode timings are not event latency.

Retail only is currently the demonstrated addon context source. Forever, Wine Wayland, long-duration stability and recognition improvements remain unverified.

Run the Python suite with `pytest tests/ -q`. Reproduce native/container checks with `sh tests/native/run_in_container.sh` (requires Docker; installs mock-only dependencies inside disposable containers).

### Local results for this implementation

- 191 Python tests passed (existing suite plus Companion/codec tests). One environment warning concerns urllib3 with the Mac Python's LibreSSL.
- Native amd64 build passed with `-Wall -Wextra -Werror`; root execution is rejected.
- Actual Docker native packaging stage passed, including license files. A clean staged package imported its decoder and round-tripped Unicode without the POC directory. A non-root runtime with no session bus exited without capturing.
- A disposable Linux mock portal passed numeric-node, serial-node and permission-cancellation flows, including real Unix-FD transfer and session cleanup. This does not simulate Gamescope. A separate native MemFd fixture also verifies RGB crop framing, bounds and interrupted writes.
- Frontend bundle built successfully; the repository's missing React declarations produce TypeScript warnings. Python compilation, shell syntax and whitespace checks passed.

The complete ML/plugin release archive and integrated physical capture/recognition tests have not been run or deployed. Legacy source-copy scripts now include the Companion module and copy a helper when an existing build provides one; they never compile/install capture dependencies on SteamOS. Use the normal plugin build for a fully bundled install.

## Client detection and Forever beta

Every five seconds Decktation checks `/proc` process ownership and the case-insensitive process name in `comm`. `WoW.exe` (Retail) and `WowB.exe` (Forever beta) are recognised, along with existing Classic executable names. Only processes owned by the resolved desktop user count; Battle.net alone does not start capture. No game memory, window title or network query is used. Executable detection does not establish addon compatibility with Classic.

WoW Context Bridge 0.1.1-experimental includes Retail and `_Camelot` Forever manifests loading the same protocol v2 encoder. Forever interface `16001` and `WowB.exe` follow existing Forever projects. Actual beta loading, readable names, rendering and SteamOS capture need volunteer validation. Later beta executable/interface changes may require an update. Check the beta's addon directory and record its build in QA reports.

## Current transcription engine

This build follows upstream's resident whisper.cpp worker and Vulkan/CPU fallback.
The worker has no separate `hotwords` argument: bounded fresh vocabulary is prepended
to the request's `prompt` field. Each recording supplies its own prompt, so stale
names are not carried into subsequent requests. Explicit non-English languages
receive vocabulary without English prose; configured prompts follow upstream policy.
Recognition effects on physical hardware with this engine remain unverified.
