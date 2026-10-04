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
