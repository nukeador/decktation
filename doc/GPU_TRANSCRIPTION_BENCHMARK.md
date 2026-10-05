# GPU transcription benchmark

This historical benchmark used a pinned whisper.cpp 1.8.5 `whisper-cli` built
with Vulkan. Production packages now bundle only `whisper-server`; to repeat
the benchmark, supply a separately built CLI from the same pinned revision.
The same executable runs on Vulkan normally and on CPU with `--no-gpu`, so the
comparison uses identical model weights and decoding code.

The benchmark is intentionally separate from Decktation's production
transcription path. It does not change the engine selected by the plugin.

## Prepare the Deck

Install the branch build through Decky, then download a multilingual GGML
model. Base is the first useful comparison:

```bash
mkdir -p /home/deck/.cache/decktation/whisper.cpp
curl -fL \
  -o /home/deck/.cache/decktation/whisper.cpp/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

Copy representative 16-bit PCM WAV recordings to the Deck. For optional word
error rate scoring, place expected text next to each recording. For
`party-chat.wav`, name the reference `party-chat.ref.txt`.

## Run the comparison

From a checkout of this repository on the Deck (the benchmark harness is kept
in source control but is not shipped in the plugin):

```bash
MODEL=/home/deck/.cache/decktation/whisper.cpp/ggml-base.bin
WHISPER_CLI=/path/to/separately-built/whisper-cli

python3 backend/scripts/benchmark_whisper_vulkan.py \
  --whisper-cli "$WHISPER_CLI" \
  --model "$MODEL" \
  --language auto \
  --repeat 10 \
  --warmup 1 \
  --json-out /home/deck/decktation-whisper-benchmark.json \
  /path/to/recordings/*.wav
```

Run once while idle and again with a representative game running. Save each
JSON file under a different name. MangoHud frame-time logging should be enabled
during the in-game run so transcription speed is not considered in isolation
from game responsiveness.

`wall_seconds` includes process startup and model loading. `compute_seconds`
subtracts whisper.cpp's reported model-load time and is the closer estimate of
a future resident-model integration. The harness alternates CPU/GPU order on
successive repetitions to reduce thermal and run-order bias.

The main decision values are GPU speedup, p95 compute latency, word error rate,
degenerate output count, and game frame-time impact. A useful initial threshold
is at least 2x lower p95 transcription latency with no accuracy regression or
degenerate GPU results.

## Initial Steam Deck result

On this Steam Deck's AMD VANGOGH GPU, using the bundled 1.875-second speech
fixture, base model, beam size 5, one warm-up, and five alternating CPU/
GPU repetitions:

| Metric | CPU | Vulkan GPU |
| --- | ---: | ---: |
| Median compute time | 2.767 s | 0.530 s |
| p95 compute time | 2.798 s | 0.543 s |
| Median wall time | 2.919 s | 0.738 s |
| Degenerate output | 0/5 | 0/5 |

That is a 5.22x median compute speedup (3.96x wall-time speedup). This is a
sanity result, not a hardware-wide promise: repeat the benchmark with real
recordings and an in-game run before using it to judge another AMD handheld.
