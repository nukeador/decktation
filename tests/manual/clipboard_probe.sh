#!/usr/bin/env bash
# Standalone Gamescope/Proton paste probe. Run over SSH with WoW foregrounded.
# Opens chat and pastes into its draft. Sending requires DECKTATION_PROBE_SEND=1.
# Stage xclip 0.13-6 under /tmp first (see doc/unicode-text-injection-testing.md).
set -euo pipefail

export DISPLAY=:1
clip=/tmp/decktation-xclip-probe/usr/bin/xclip
sample=${DECKTATION_PROBE_TEXT:-'¡Mañana iré a la misión con Lucía! ¿Vienes tú? Français, português, über.'}
backup=$(mktemp /tmp/decktation-clipboard.XXXXXX)
chmod 600 "$backup"
had_clipboard=false
if "$clip" -selection clipboard -out > "$backup" 2>/dev/null; then
    had_clipboard=true
fi
restore() {
    if "$had_clipboard"; then
        "$clip" -selection clipboard -in < "$backup"
    else
        "$clip" -selection clipboard -in < /dev/null
    fi
    rm -f "$backup"
}
trap restore EXIT

if [[ ${DECKTATION_PROBE_REPLACE:-0} == 1 ]]; then
    xdotool key --clearmodifiers ctrl+a
else
    xdotool key --clearmodifiers Return
fi
sleep 0.3
printf %s "$sample" | "$clip" -selection clipboard -in
sleep 0.3
xdotool key --clearmodifiers ctrl+v
if [[ ${DECKTATION_PROBE_SEND:-0} == 1 ]]; then
    sleep 0.3
    xdotool key --clearmodifiers Return
fi
sleep 3
printf 'Paste probe finished; clipboard restored.\n'
