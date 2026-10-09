# Steam Deck baseline before resident Vulkan experiment

Measured 2026-10-05, upstream master 4f4caa4f0c06cdfc81e47ab3f8e956de6ae79528,
installed 0.3.19-dev.4f4caa4. WoW, Gaming Mode, Base multilingual,
Auto Detect. Backend startup selected AMD Vulkan; no fallback errors observed.

Latency measured from logged physical L1+R1 COMBO release to logged start of
text insertion (includes polling/audio preparation/inference, excludes paste completion).

| Release | Start of insertion | Seconds |
|---|---|---:|
| 00:15:37.811 | 00:15:42.113 | 4.302 |
| 00:15:51.705 | 00:15:54.314 | 2.609 |
| 00:16:02.949 | 00:16:05.260 | 2.311 |
| 00:16:38.345 | 00:16:39.502 | 1.157 |

Median 2.460 s; range 1.157–4.302 s. Audio durations and exact texts not
captured for these baseline recordings. User reported needing to speak close
to the microphone. This is not a controlled CPU/GPU comparison, and phrases
varied. For comparison repeat identical phrases at the same distance/language,
model and game load, distinguishing first use from subsequent requests.

Source: /home/deck/homebrew/logs/decktation/2026-10-05 00.15.00.log
