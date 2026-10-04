# Experimental resident Vulkan Whisper

Based on upstream master 4f4caa4, not the combined feature branch.
Uses the same pinned whisper.cpp revision and multilingual GGML model, but
bundles whisper-server alongside whisper-cli. The plugin owns a loopback-only
server process, confirms Vulkan initialization before declaring readiness, and
reuses that process/model for subsequent serialized inference requests.
Disable, model changes and plugin unloading release the worker; Linux parent-death
signalling also stops it if the plugin crashes. Startup/inference failures close
the worker and retain the existing faster-whisper CPU fallback.

The pinned whisper.cpp revision and model are unchanged; recognition accuracy
is not guaranteed to match faster-whisper. The model now occupies
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


## Integrated physical test, 2026-10-05 00:52

Installed resident.2, Base multilingual, Auto Detect, WoW Gaming Mode.
AMD Vulkan confirmed at startup; single worker PID 38453 used for all requests.
User reports recordings 1 and 2 correct and fast, 3 incorrect English, 4 repeat
of 3 correct. Logged text may still contain punctuation/minor spelling errors.

| Recording | Audio s | Inference request s | PTT release to insertion start s |
|---|---:|---:|---:|
| 1 | 3.285 | 1.291 | 1.333 |
| 2 | 3.253 | 0.951 | 0.991 |
| 3 | 2.741 | 1.019 | 1.057 |
| 4 | 3.434 | 0.766 | 0.798 |

Median release-to-insertion 1.024 s, range 0.798–1.333 s. Earlier master median
2.460 s with different phrases and English prompt enabled; improvements cannot
be attributed separately to residency and removal of prose prompts.
Third text: "I think it was a perfect amount." Fourth: "Parece que funciona
perfectamente." translateToEnglish=false, so third output was not requested
translation. Auto Detect still unreliable for at least one short recording.
No fallback/error in the four inference entries. Gameplay impact not assessed
in this latest user report. Source log: 2026-10-05 00.52.02.log.

### Explicit Spanish physical repeat test, 00:56–00:57

User spoke “pues parece que funciona perfectamente” three times, including fast
speech, and confirmed all correct and fast. Same AMD Vulkan worker PID 38453.

| Audio s | Request s | Release to insertion start s |
|---:|---:|---:|
| 2.901 | 0.699 | 0.736 |
| 3.157 | 0.664 | 0.681 |
| 2.687 | 0.660 | 0.701 |

Median release-to-insertion 0.701 s; transcripts match words exactly, with
capitalization/punctuation variation only. No GPU/fallback errors observed.
Auto Detect reliability remains unresolved; fixed Spanish works in this sample.
Earlier empty-on-screen attempt recorded 5.695 s, inferred incorrect Greek with
an internal newline; send_to_wow_chat rejects control characters, explaining no
insertion. No code workaround applied; multiline output handling remains noted.

## resident.3: wrapped server output

Physical English tests in Auto Detect returned valid English with embedded
newlines, e.g. “So it seems it's able to transcript something in English\n perfectly.”
The existing insertion validator rejects control characters, explaining why
long dictations appeared to do nothing. Normalise CR/LF wrapping to spaces only
at the Vulkan transcript boundary; preserve other controls for rejection. This
is output formatting and does not resolve wrong-language recognition. Added
regression coverage for a wrapped Unicode transcript and preserved NUL rejection.
