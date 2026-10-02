"""Bundled experimental Companion lifecycle. Context never leaves process memory."""
from __future__ import annotations

import copy
import os
import pwd
import select
import signal
import struct
import subprocess
import threading
import time
from pathlib import Path

from .png import Image
from .protocol import decode_image

HEADER = struct.Struct("!4sHHQ")
INTERVAL = 5.0
STALE_AFTER = 15.0


def vocabulary(context):
    terms = []
    values = [context.get("target", ""), context.get("player", "")]
    values += context.get("nearby", [])
    values += [context.get("zone", ""), context.get("subzone", "")]
    for value in values:
        if not isinstance(value, str):
            continue
        value = "".join(" " if ord(c) < 32 else c for c in value).strip()
        if not value or value in terms:
            continue
        candidate = ", ".join(terms + [value])
        if len(candidate.encode("utf-8")) <= 512 and len(terms) < 12:
            terms.append(value)
    return terms


def desktop_account(home):
    account = pwd.getpwuid(os.stat(home).st_uid)
    if account.pw_uid == 0 or Path(account.pw_dir).resolve() != Path(home).resolve():
        raise ValueError("desktop user unavailable")
    return account


def wow_running(uid, proc=Path("/proc")):
    try:
        entries = list(proc.iterdir())
    except OSError:
        return False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid == uid and (entry / "comm").read_text().strip().lower() in {
                "wow.exe", "wowclassic.exe", "wowclassic_t.exe"}:
                return True
        except OSError:
            pass
    return False


def launch_helper(binary, account):
    runtime = Path(f"/run/user/{account.pw_uid}")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise FileNotFoundError("bundled capture helper unavailable")
    if not (runtime / "bus").exists() or not (runtime / "pipewire-0").exists():
        raise FileNotFoundError("desktop capture session unavailable")
    env = {"PATH": "/usr/bin:/bin", "HOME": account.pw_dir, "USER": account.pw_name,
           "LOGNAME": account.pw_name, "XDG_RUNTIME_DIR": str(runtime),
           "PIPEWIRE_RUNTIME_DIR": str(runtime), "XDG_SESSION_TYPE": "wayland",
           "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime}/bus"}
    kwargs = {}
    if os.geteuid() == 0:
        kwargs = {"user": account.pw_uid, "group": account.pw_gid, "extra_groups": []}
    elif os.geteuid() != account.pw_uid:
        raise PermissionError("desktop identity mismatch")
    # Missing linked libraries cause an early exit; stderr is never forwarded
    # into Decky/telemetry. All public errors are fixed, non-sensitive strings.
    common = dict(stderr=subprocess.DEVNULL, env=env, cwd=account.pw_dir,
                  close_fds=True, start_new_session=True, **kwargs)
    check = subprocess.Popen([str(binary), "--check-runtime"],
                             stdout=subprocess.DEVNULL, **common)
    try:
        if check.wait(timeout=3) != 0:
            raise FileNotFoundError("capture runtime libraries unavailable")
    except subprocess.TimeoutExpired:
        check.kill()
        check.wait(timeout=2)
        raise FileNotFoundError("capture runtime check timed out") from None
    return subprocess.Popen([str(binary)], stdout=subprocess.PIPE, **common)


def read_exact(fd, count, stop, timeout=2.0):
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < count:
        if stop.is_set():
            raise InterruptedError("capture stopped")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("incomplete capture frame")
        if not select.select([fd], [], [], min(0.1, remaining))[0]:
            continue
        chunk = os.read(fd, count - len(data))
        if not chunk:
            raise EOFError("capture ended")
        data.extend(chunk)
    return bytes(data)


def read_frame(fd, stop):
    magic, width, height, timestamp = HEADER.unpack(read_exact(fd, HEADER.size, stop))
    if magic != b"DCPF" or not 0 < width <= 1088 or not 0 < height <= 128:
        raise ValueError("invalid capture frame")
    now = time.monotonic_ns()
    if timestamp > now or now - timestamp > 15_000_000_000:
        raise ValueError("expired capture frame")
    return Image(width, height, bytearray(read_exact(fd, width * height * 3, stop)))


class Companion:
    def __init__(self, binary, home, *, clock=time.monotonic, launcher=launch_helper,
                 game_check=wow_running):
        self.binary, self.home = Path(binary), home
        self.clock, self.launcher, self.game_check = clock, launcher, game_check
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.enabled = self.dictation = False
        self.preset = "wow"
        self.failed = False
        self.context = None
        self.sequence = self.advanced = None
        self.state, self.detail = "Disabled", ""
        self.process = None
        self.thread = None
        self.generation = 0
        self.hint = None

    def configure(self, enabled, dictation, preset):
        with self.lock:
            settings = (bool(enabled), bool(dictation), preset)
            if settings != (self.enabled, self.dictation, self.preset):
                self.generation += 1
                self.clear()
            if enabled and not self.enabled:
                self.failed = False
            self.enabled, self.dictation, self.preset = settings
            if not self.active():
                self.state, self.detail = "Disabled", ""
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run, name="wow-companion", daemon=True)
            self.thread.start()

    def active(self):
        return self.enabled and self.dictation and self.preset == "wow"

    def clear(self):
        self.context = self.sequence = self.advanced = None
        self.hint = None

    def ingest(self, frame, generation=None):
        with self.lock:
            if not self.active() or (generation is not None and generation != self.generation):
                return
            if frame.sequence != self.sequence:
                self.sequence = frame.sequence
                self.advanced = self.clock()
                self.context = copy.deepcopy(frame.context)
            self.state, self.detail = "Live", ""

    def snapshot(self):
        with self.lock:
            if not self.active() or self.context is None or self.advanced is None:
                return None
            if self.clock() - self.advanced >= STALE_AFTER:
                return None
            return copy.deepcopy(self.context)

    def status(self):
        with self.lock:
            age = None if self.advanced is None else max(0, self.clock() - self.advanced)
            state = self.state if self.active() else "Disabled"
            if self.active() and age is not None and age >= STALE_AFTER:
                state = "Stale"
            context = self.snapshot()
            return {"state": state, "age_seconds": round(age, 1) if age is not None else None,
                    "vocabulary_count": len(vocabulary(context)) if context else 0,
                    "detail": self.detail}

    def _terminate(self):
        process, self.process = self.process, None
        if process is None:
            return
        if process.poll() is None:
            try:
                process.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if process.stdout:
            process.stdout.close()

    def _fail(self, state, detail, generation=None):
        with self.lock:
            if generation is None or generation == self.generation:
                self.failed = True
                self.clear()
                self.state, self.detail = state, detail
        self._terminate()

    def _run(self):
        try:
            self._loop()
        except Exception:
            # Never forward exception text/frame data into logs or telemetry.
            self._fail("Error", "Capture unavailable. Toggle off/on to retry.")
        finally:
            self._terminate()
            with self.lock:
                self.clear()

    def _loop(self):
        next_check = 0
        game_present = False
        generation = -1
        while not self.stop_event.is_set():
            with self.lock:
                active, failed = self.active(), self.failed
                current_generation = self.generation
            if current_generation != generation:
                self._terminate()
                generation = current_generation
            if not active:
                self._terminate()
                self.stop_event.wait(0.2)
                continue
            if failed:
                self.stop_event.wait(0.2)
                continue
            if self.clock() >= next_check:
                next_check = self.clock() + INTERVAL
                try:
                    account = desktop_account(self.home)
                    game_present = self.game_check(account.pw_uid)
                except (OSError, ValueError, KeyError):
                    self._fail("Unavailable", "Desktop user unavailable.", generation)
                    continue
                if not game_present:
                    self._terminate()
                    with self.lock:
                        self.clear()
                        self.state = "Waiting for WoW"
            if not game_present:
                self.stop_event.wait(0.2)
                continue
            if self.process is None:
                with self.lock:
                    self.state, self.detail = "Connecting", ""
                try:
                    self.process = self.launcher(self.binary, account)
                except (OSError, ValueError):
                    self._fail("Unavailable", "Capture helper, runtime libraries or desktop session unavailable. Toggle off/on to retry.", generation)
                    continue
            if self.process.poll() is not None:
                self._fail("Unavailable" if self.process.returncode == 127 else "Error", "Capture stopped. Check runtime support and portal permission; toggle off/on to retry.", generation)
                continue
            fd = self.process.stdout.fileno()
            if not select.select([fd], [], [], 0.2)[0]:
                continue
            try:
                image = read_frame(fd, self.stop_event)
                result = decode_image(image, hint=self.hint)
                if result.status == "valid" and result.frame:
                    self.hint = (*result.origin, result.cell_size)
                    self.ingest(result.frame, generation)
                elif self.snapshot() is None:
                    with self.lock:
                        self.state = "Stale" if self.advanced is not None else "Connecting"
            except InterruptedError:
                break
            except (OSError, ValueError, EOFError):
                self._fail("Error", "Incomplete or unavailable capture. Toggle off/on to retry.", generation)

    def close(self):
        self.stop_event.set()
        with self.lock:
            self.enabled = self.dictation = False
            self.generation += 1
            self.clear()
            self.state = "Disabled"
        if self.thread:
            self.thread.join(timeout=20)
