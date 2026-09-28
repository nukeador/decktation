"""Temporary X11 clipboard access for Unicode input in Gamescope games."""

import os
import shutil
import subprocess
import time
from contextlib import contextmanager


def _xclip_path(plugin_dir):
    bundled = os.path.join(plugin_dir, "bin", "xclip")
    return bundled if os.path.isfile(bundled) else shutil.which("xclip")


def _clipboard_env():
    env = os.environ.copy()
    # Gaming Mode keeps Steam on :0 and the foreground game on :1. Decky may
    # inherit :0 or no DISPLAY; target the game's Xwayland socket when present.
    if os.path.exists("/run/user/1000/gamescope-0") and os.path.exists("/tmp/.X11-unix/X1"):
        env["DISPLAY"] = ":1"
    elif not env.get("DISPLAY"):
        raise RuntimeError("No X11 display available for Unicode paste")
    return env


def _clip(xclip, env, mode, data=None):
    args = [xclip, "-selection", "clipboard", mode]
    result = subprocess.run(
        args, input=data, capture_output=True, env=env, timeout=3,
        user="deck" if os.geteuid() == 0 else None,
    )
    if result.returncode != 0:
        raise RuntimeError("X11 clipboard operation failed")
    return result.stdout


def _previous_text(xclip, env):
    targets = subprocess.run(
        [xclip, "-selection", "clipboard", "-out", "-target", "TARGETS"],
        capture_output=True, env=env, timeout=3,
        user="deck" if os.geteuid() == 0 else None,
    )
    if targets.returncode != 0:
        return b""  # no clipboard owner
    supported = {
        b"TARGETS", b"UTF8_STRING", b"STRING", b"TEXT", b"COMPOUND_TEXT",
        b"TIMESTAMP", b"MULTIPLE", b"SAVE_TARGETS", b"text/plain",
        b"text/plain;charset=utf-8",
    }
    offered = set(targets.stdout.splitlines())
    if offered - supported:
        raise RuntimeError("Clipboard contains non-text formats; Unicode paste skipped")
    return _clip(xclip, env, "-out")


@contextmanager
def temporary_clipboard(text, plugin_dir):
    """Serve UTF-8 text until the caller pastes it, then restore prior text.

    If another application changes the clipboard during the operation, leave
    that newer value alone. Clipboard content is never logged or written to disk.
    """
    xclip = _xclip_path(plugin_dir)
    if not xclip:
        raise RuntimeError("xclip is unavailable for Unicode paste")
    env = _clipboard_env()
    previous = _previous_text(xclip, env)
    payload = text.encode("utf-8")
    _clip(xclip, env, "-in", payload)
    try:
        yield env
    finally:
        # Proton requests clipboard data asynchronously after Ctrl+V.
        time.sleep(0.3)
        try:
            current = _clip(xclip, env, "-out")
            if current == payload:
                _clip(xclip, env, "-in", previous)
        except RuntimeError:
            # An unavailable clipboard cannot be safely restored here.
            pass
