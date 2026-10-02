#!/bin/sh
# Installs test dependencies only inside a disposable container, never SteamOS.
set -eu
companion_test_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
docker build --platform linux/amd64 --target companion-builder \
    -t decktation-companion-builder:local "$companion_test_root/backend"
docker run --rm --platform linux/amd64 \
    -v "$companion_test_root/tests/native:/tests:ro" \
    -v "$companion_test_root/backend/native/companion:/src:ro" \
    decktation-companion-builder:local sh -c '
    set -eu
    gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src -o /tmp/test-crop \
        /tests/test_crop.c $(pkg-config --cflags --libs libpipewire-0.3)
    /tmp/test-crop
    if /companion-build/companion-capture --check-runtime; then exit 1; else test $? -eq 2; fi
    apt-get update -qq
    apt-get install -y -qq python3-gi dbus pipewire >/dev/null
    echo "test:x:1000:1000::/tmp:/bin/sh" >> /etc/passwd
    python3 -c "import os; os.environ[\"HOME\"]=\"/tmp\"; os.makedirs(\"/tmp/desktop-runtime\", mode=0o700); os.chown(\"/tmp/desktop-runtime\", 1000, 1000); os.environ[\"XDG_RUNTIME_DIR\"]=\"/tmp/desktop-runtime\"; os.setgroups([]); os.setgid(1000); os.setuid(1000); os.execvp(\"dbus-run-session\", [\"dbus-run-session\", \"--\", \"python3\", \"/tests/mock_portal.py\", \"/companion-build/companion-capture\"])"
'
