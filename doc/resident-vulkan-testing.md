# Experimental resident Vulkan Whisper

Based on upstream master 4f4caa4, not the combined feature branch.
Uses the same pinned whisper.cpp revision and multilingual GGML model, but
bundles whisper-server alongside whisper-cli. The plugin owns a loopback-only
server process, confirms Vulkan initialization before declaring readiness, and
reuses that process/model for subsequent serialized inference requests.
Disable, model changes and plugin unloading release the worker; Linux parent-death
signalling also stops it if the plugin crashes. Startup/inference failures close
the worker and retain the existing faster-whisper CPU fallback.

No recognition parameters/accuracy promises are changed. The model now occupies
GPU/shared memory while enabled. A missing/broken server selects CPU. Initial
loading still takes time; the intended speedup applies to later dictations.

Compare the same Spanish and English phrases, mic distance, model and game load
against resident-vulkan-baseline.md. Check a single worker PID across recordings,
`Resident Vulkan ready` only once, and audio/request timings. Test disable/enable,
model switch, Auto Detect and explicit Spanish, then check no abandoned worker.
The reported request time excludes audio preparation and text insertion; use
controller release/insertion timestamps for comparison with the saved baseline.

## resident.2 comparison

Suppress preset example/prose prompts for all languages, including Auto Detect,
even when old saved profiles contain them. Preserve explicit vocabulary and
zone/boss/target names. Saved profiles are not edited. The WoW stock preset has
no hotwords; without a context file it now sends an empty prompt.

Same 5-second captured Spanish audio, 2026-10-05:
- resident Auto + stock English examples: 11.854 s, incorrect text;
- CLI Auto + examples: 10.606 s, incorrect text;
- resident Auto without prompt: 1.136 s;
- CLI Auto without prompt: 1.648 s;
- resident Spanish without prompt: 0.797 s;
- CLI Spanish without prompt: 1.242 s.
Both no-prompt paths still rendered mazmorra as “más morra”. These are standalone
request/subprocess times, not real PTT-to-insertion measurements. Hardware plugin
validation of resident.2 is pending. Do not infer that prompts never help English.
