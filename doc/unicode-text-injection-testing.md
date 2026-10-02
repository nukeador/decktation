# Keyboard-layout-independent text injection: issue #25

## Behavior

Decktation builds the complete message, including a game channel prefix, as one
UTF-8 string and places it on the X11 CLIPBOARD selection. It then uses the
private ydotool daemon to issue Ctrl+V. This applies to ordinary ASCII and
Unicode alike, so punctuation such as slash and apostrophe is not generated
from keyboard-layout-dependent key codes.

ydotool remains responsible for opening chat and, when enabled by the preset,
sending the message. The Generic preset and the WoW type channel do not open
chat or press Enter. Manual-send mode opens chat when configured and leaves
the pasted text as a draft. Preset chat-open and chat-send delays remain in
effect. A successful clipboard write and Ctrl+V command do not prove that the
game accepted or displayed the text.

## Clipboard backup and restoration

Before replacing the clipboard, Decktation makes a best-effort backup of
available plain text. It does not reject a clipboard because it also offers
images, copied files, rich text, or other non-text formats. Those unsupported
formats may be lost when the dictated text takes ownership of CLIPBOARD.
When the previous content exposes a readable plain-text representation,
Decktation attempts to restore that text after the paste. This does not
preserve a copied image or file reference.

Clipboard restoration waits 300 ms because Proton can request clipboard data
asynchronously after Ctrl+V. This is a practical workaround, not a delivery
acknowledgement. Decktation restores only if the clipboard still contains its
own payload; if another application has changed the clipboard, that newer
value is left untouched. Failures to inspect, back up, or restore previous
clipboard contents are warnings and do not fail a successful paste. If no
plain-text backup exists, the dictated text may remain in the clipboard.
Clipboard history software may capture it.

Failure to locate xclip, access the game clipboard, write the new payload, or
issue Ctrl+V is a real injection failure. Decktation does not automatically
press the final chat-send key after one of these failures and does not retry
the message. A failure to issue the chat-open key also aborts injection. The
plugin cannot confirm whether the game consumed a successful paste command.

## Validation evidence

### Earlier physical Steam Deck tests

Before the all-text clipboard change, a physical Steam Deck running SteamOS
Gaming Mode with WoW foregrounded was used to validate standalone clipboard
paste for accented Spanish, French, Portuguese, German, uppercase and
lowercase accents, and CJK text. WoW displayed emoji as boxes, which is a
game-font limitation. The earlier integrated Decktation build successfully
sent accented dictations once per recording with normal controls. Those tests
covered the earlier Unicode-only clipboard path; they do not physically
validate the new policy of pasting ASCII as well.

A contributor later reported that their local modification to always paste
worked with a Norwegian keyboard layout in both XWayland and Wine Wayland.
That report is useful feedback, but is not a physical test of this branch's
new implementation.

### Automated tests for the all-text clipboard path

The test suite exercises ASCII and Unicode through the same clipboard path,
literal channel prefixes and punctuation, Generic and manual-send behavior,
plain-text backup and restoration, image/file clipboard cases, backup and
restoration failures, preservation of a newer clipboard value, and prevention
of a final Enter or duplicate submission after an injection failure. Local verification on 2026-09-29 passed: 159 Python tests, 3 Node tests, the
release-version consistency check, and Python syntax parsing. The GitHub Actions
build will validate the packaged ZIP and publish the branch preview after push.

### Physical validation still recommended

After installing a build of this change on SteamOS Gaming Mode, test an ASCII
phrase containing slash and apostrophe, an accented phrase, and a non-Latin
phrase in WoW. Check the unsent draft and sent message, manual-send mode,
channel prefixes, Generic preset, controller behavior, and clipboard
restoration. With a copied image or file on the clipboard, dictation should
continue; that non-text item may be lost by design.

## Standalone clipboard probe

The earlier standalone probe used xdotool to open chat and paste into a draft
without changing Decktation. It can still be used to confirm basic Gamescope
clipboard access. The integrated feature now uses the private ydotool daemon,
so the probe does not test the full plugin path.

    ssh steamdeck 'curl -fsSL -o /tmp/decktation-xclip.pkg.tar.zst https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.8/os/x86_64/xclip-0.13-6-x86_64.pkg.tar.zst && mkdir -p /tmp/decktation-xclip-probe && bsdtar -xf /tmp/decktation-xclip.pkg.tar.zst -C /tmp/decktation-xclip-probe usr/bin/xclip'
    ssh steamdeck 'bash -s' < tests/manual/clipboard_probe.sh

The probe opens chat and pastes into a draft without sending by default. Set
DECKTATION_PROBE_SEND=1 only when sending a visible test message is intended.
It attempts to restore prior plain text.

## Backup and restore for an approved development deployment

Create a backup as the deck user; this does not need sudo:

    ssh steamdeck 'tar -C /home/deck/homebrew -czf /home/deck/decktation-pre-unicode-issue25.tar.gz plugins/decktation settings/decktation && tar -tzf /home/deck/decktation-pre-unicode-issue25.tar.gz >/dev/null'

Restoring the backed-up plugin and settings requires sudo because the installed
plugin is root-owned:

    ssh -t steamdeck 'sudo tar -C /home/deck/homebrew -xzf /home/deck/decktation-pre-unicode-issue25.tar.gz && sudo systemctl restart plugin_loader.service'

## Physical test plan

1. In Gaming Mode with WoW foregrounded and the QAM closed, dictate
   mañana's slash /s, and check that the draft preserves punctuation and
   accents exactly.
2. Repeat with uppercase accents, a CJK phrase, and ordinary ASCII. Confirm
   each phrase appears once, with normal controls.
3. Test the say and party prefixes, then enable manual send and confirm the
   pasted message remains a draft.
4. Test the Generic preset in a focused text field and confirm that it never
   presses Enter.
5. Copy an image or file, dictate a harmless phrase, and confirm dictation
   proceeds. The non-text clipboard item may be lost.
