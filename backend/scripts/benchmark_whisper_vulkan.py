#!/usr/bin/env python3
"""Compare whisper.cpp CPU and Vulkan transcription on the same Deck."""

import argparse
import json
import math
import re
import statistics
import subprocess
import tempfile
import time
import wave
from pathlib import Path


TIMING_RE = re.compile(
    r"whisper_print_timings:\s+(load|total) time\s*=\s*([0-9.]+) ms"
)


def wav_duration(path):
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def normalized_words(text):
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


def word_error_rate(reference, hypothesis):
    expected = normalized_words(reference)
    actual = normalized_words(hypothesis)
    if not expected:
        return 0.0 if not actual else 1.0
    previous = list(range(len(actual) + 1))
    for row, expected_word in enumerate(expected, 1):
        current = [row]
        for column, actual_word in enumerate(actual, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (expected_word != actual_word),
                )
            )
        previous = current
    return previous[-1] / len(expected)


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def parse_timings(output):
    values = {}
    for name, milliseconds in TIMING_RE.findall(output):
        values[name] = float(milliseconds)
    return values


def run_once(args, backend, audio, output_directory):
    output_base = output_directory / f"{backend}-{time.monotonic_ns()}"
    command = [
        str(args.whisper_cli),
        "--model", str(args.model),
        "--file", str(audio),
        "--language", args.language,
        "--beam-size", str(args.beam_size),
        "--no-timestamps",
        "--output-txt",
        "--output-file", str(output_base),
    ]
    if backend == "cpu":
        command.append("--no-gpu")
    if args.prompt:
        command.extend(["--prompt", args.prompt])
    if args.vad_model:
        command.extend(["--vad", "--vad-model", str(args.vad_model)])

    started = time.perf_counter()
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=args.timeout,
        check=False,
    )
    wall_seconds = time.perf_counter() - started
    combined_output = completed.stdout + "\n" + completed.stderr
    timings = parse_timings(combined_output)
    transcript_path = output_base.with_suffix(".txt")
    transcript = transcript_path.read_text(errors="replace").strip() if transcript_path.exists() else ""
    if completed.returncode != 0:
        raise RuntimeError(
            f"{backend} failed for {audio.name} with exit {completed.returncode}: "
            f"{combined_output[-1000:].strip()}"
        )

    total_ms = timings.get("total")
    load_ms = timings.get("load")
    compute_seconds = None
    if total_ms is not None and load_ms is not None:
        compute_seconds = max(0.0, total_ms - load_ms) / 1000

    reference_path = audio.with_suffix(args.reference_suffix)
    reference = reference_path.read_text(errors="replace").strip() if reference_path.exists() else None
    duration = wav_duration(audio)
    return {
        "backend": backend,
        "audio": str(audio),
        "audio_seconds": duration,
        "wall_seconds": wall_seconds,
        "compute_seconds": compute_seconds,
        "load_seconds": None if load_ms is None else load_ms / 1000,
        "wall_realtime_multiple": duration / wall_seconds,
        "compute_realtime_multiple": (
            None if not compute_seconds else duration / compute_seconds
        ),
        "transcript": transcript,
        "degenerate": not any(character.isalnum() for character in transcript),
        "wer": None if reference is None else word_error_rate(reference, transcript),
    }


def summarize(results):
    summary = {}
    for backend in ("cpu", "gpu"):
        matches = [result for result in results if result["backend"] == backend]
        if not matches:
            continue
        wall = [result["wall_seconds"] for result in matches]
        compute = [
            result["compute_seconds"]
            for result in matches
            if result["compute_seconds"] is not None
        ]
        wers = [result["wer"] for result in matches if result["wer"] is not None]
        summary[backend] = {
            "runs": len(matches),
            "wall_median_seconds": statistics.median(wall),
            "wall_p95_seconds": percentile(wall, 0.95),
            "compute_median_seconds": statistics.median(compute) if compute else None,
            "compute_p95_seconds": percentile(compute, 0.95) if compute else None,
            "degenerate_runs": sum(result["degenerate"] for result in matches),
            "mean_wer": statistics.mean(wers) if wers else None,
        }
    if "cpu" in summary and "gpu" in summary:
        for metric in ("wall_median_seconds", "compute_median_seconds"):
            cpu_value = summary["cpu"].get(metric)
            gpu_value = summary["gpu"].get(metric)
            if cpu_value is not None and gpu_value:
                summary[f"gpu_speedup_{metric.removesuffix('_seconds')}"] = cpu_value / gpu_value
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark one Vulkan whisper.cpp binary in CPU and GPU modes."
    )
    parser.add_argument("audio", nargs="+", type=Path, help="16-bit PCM WAV files")
    parser.add_argument("--whisper-cli", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--vad-model", type=Path)
    parser.add_argument("--language", default="auto")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--prompt")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--reference-suffix", default=".ref.txt")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    for path in (args.whisper_cli, args.model, *args.audio):
        if not path.exists():
            parser.error(f"not found: {path}")
    if args.vad_model and not args.vad_model.exists():
        parser.error(f"not found: {args.vad_model}")
    if args.repeat < 1 or args.warmup < 0:
        parser.error("--repeat must be positive and --warmup cannot be negative")

    results = []
    with tempfile.TemporaryDirectory(prefix="decktation-whisper-benchmark-") as temp:
        output_directory = Path(temp)
        for backend in ("cpu", "gpu"):
            for _ in range(args.warmup):
                run_once(args, backend, args.audio[0], output_directory)

        for repetition in range(args.repeat):
            backends = ("cpu", "gpu") if repetition % 2 == 0 else ("gpu", "cpu")
            for audio in args.audio:
                for backend in backends:
                    result = run_once(args, backend, audio, output_directory)
                    result["repetition"] = repetition + 1
                    results.append(result)
                    compute = result["compute_seconds"]
                    compute_label = "n/a" if compute is None else f"{compute:.3f}s"
                    print(
                        f"{backend:3} {audio.name}: wall={result['wall_seconds']:.3f}s "
                        f"compute={compute_label} degenerate={result['degenerate']}"
                    )

    report = {
        "configuration": {
            "whisper_cli": str(args.whisper_cli),
            "model": str(args.model),
            "vad_model": None if args.vad_model is None else str(args.vad_model),
            "language": args.language,
            "beam_size": args.beam_size,
            "repeat": args.repeat,
            "warmup": args.warmup,
        },
        "summary": summarize(results),
        "runs": results,
    }
    print("\nSummary")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Full report: {args.json_out}")


if __name__ == "__main__":
    main()
