"""Temporary X11 clipboard access for text injection in Gamescope games."""

import logging
import os
import shutil
import subprocess
import time
from contextlib import contextmanager


logger = logging.getLogger(__name__)

_TEXT_TARGETS = {
    b"UTF8_STRING",
    b"STRING",
    b"TEXT",
    b"COMPOUND_TEXT",
    b"text/plain",
    b"text/plain;charset=utf-8",
}


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
        raise RuntimeError("No X11 display available for clipboard paste")
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
    """Return prior plain text when safely readable, otherwise None.

    Rich and non-text clipboard targets are not a reason to block dictation.
    If they cannot be represented as text, they may be lost when the clipboard
    is replaced with the dictated message.
    """
    try:
        targets = subprocess.run(
            [xclip, "-selection", "clipboard", "-out", "-target", "TARGETS"],
            capture_output=True, env=env, timeout=3,
            user="deck" if os.geteuid() == 0 else None,
        )
    except Exception as exc:
        logger.warning(
            "Could not inspect existing clipboard targets; proceeding without a backup (%s)",
            type(exc).__name__,
        )
        return None

    if targets.returncode != 0:
        logger.warning(
            "Could not read existing clipboard targets; proceeding without a backup (exit %s)",
            targets.returncode,
        )
        return None

    offered = set(targets.stdout.splitlines())
    if not offered.intersection(_TEXT_TARGETS):
        return None

    try:
        return _clip(xclip, env, "-out")
    except Exception as exc:
        logger.warning(
            "Could not back up existing clipboard text; proceeding without a backup (%s)",
            type(exc).__name__,
        )
        return None


@contextmanager
def temporary_clipboard(text, plugin_dir):
    """Expose UTF-8 text through CLIPBOARD while the caller issues Ctrl+V.

    A readable previous text value is restored after a 300 ms grace period for
    asynchronous Proton clipboard reads. Restoration happens only if the
    clipboard still contains Decktation's payload, so another app's newer value
    is left alone. Unreadable or non-text prior contents do not block paste;
    they may be lost. Clipboard contents and dictated text are never logged.
    """
    xclip = _xclip_path(plugin_dir)
    if not xclip:
        raise RuntimeError("xclip is unavailable for clipboard paste")
    env = _clipboard_env()
    previous = _previous_text(xclip, env)
    payload = text.encode("utf-8")

    # Failure to publish the new payload is an injection failure and must reach
    # the caller so it will not press the final chat-send key.
    _clip(xclip, env, "-in", payload)

    try:
        yield env
    finally:
        try:
            # Proton may request clipboard data asynchronously after Ctrl+V.
            time.sleep(0.3)
        except Exception as exc:
            logger.warning(
                "Clipboard restoration delay failed; previous contents may not be restored (%s)",
                type(exc).__name__,
            )

        try:
            current = _clip(xclip, env, "-out")
        except Exception as exc:
            logger.warning(
                "Could not inspect clipboard after paste; leaving it unchanged (%s)",
                type(exc).__name__,
            )
        else:
            if current == payload and previous is not None:
                try:
                    _clip(xclip, env, "-in", previous)
                except Exception as exc:
                    # Restore failures are nonfatal after the paste command has
                    # succeeded. Never include clipboard or dictated text here.
                    logger.warning(
                        "Could not restore previous clipboard text after paste (%s)",
                        type(exc).__name__,
                    )
