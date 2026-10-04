import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "backend" / "scripts" / "benchmark_whisper_vulkan.py"
SPEC = importlib.util.spec_from_file_location("benchmark_whisper_vulkan", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


def test_word_error_rate():
    assert BENCHMARK.word_error_rate("party pull the boss", "party pull boss") == 0.25
    assert BENCHMARK.word_error_rate("Hello, WORLD!", "hello world") == 0


def test_parse_timings_and_summary():
    timings = BENCHMARK.parse_timings(
        "whisper_print_timings: load time = 100.00 ms\n"
        "whisper_print_timings: total time = 500.00 ms\n"
    )
    assert timings == {"load": 100.0, "total": 500.0}

    results = [
        {"backend": "cpu", "wall_seconds": 2.0, "compute_seconds": 1.5, "degenerate": False, "wer": 0.0},
        {"backend": "cpu", "wall_seconds": 4.0, "compute_seconds": 3.0, "degenerate": False, "wer": 0.0},
        {"backend": "gpu", "wall_seconds": 1.0, "compute_seconds": 0.5, "degenerate": False, "wer": 0.0},
        {"backend": "gpu", "wall_seconds": 2.0, "compute_seconds": 1.0, "degenerate": True, "wer": 0.5},
    ]
    summary = BENCHMARK.summarize(results)
    assert summary["gpu"]["degenerate_runs"] == 1
    assert summary["gpu_speedup_wall_median"] == 2.0
    assert summary["gpu_speedup_compute_median"] == 3.0
