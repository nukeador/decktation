# Unicode text injection: issue #25

## Findings

`ydotool type` in the bundled revision uses a 128-entry ASCII-to-keycode
table. It cannot represent UTF-8 characters and returns success even when a
character is skipped. The existing `ydotool key` command can still emit the
Enter and Ctrl+V keycodes used around chat input.

The active SteamOS Gaming Mode game display on the tested Deck was Xwayland
`:1` with a `us` layout; Steam was on `:0`. `xkbcli how-to-type --layout us`
did not find direct chords for `é`, `ñ`, `ü`, `Á`, `¿`, or `漢`. Dotool's
keymap/dead-key approach requires a layout matching the game's interpretation,
and the tested US layout cannot generate the accented phrase directly. Dotool
is GPL licensed, so its code was not copied into Decktation's MIT sources.

Gamescope's clipboard issue #916 was closed, but it does not establish WoW
compatibility. Standalone tests on SteamOS Gaming Mode with WoW foregrounded
and the QAM closed showed that X11 clipboard text on `:1` can be pasted into
WoW. The full requested Spanish/French/Portuguese/German sample was readable
in the edit box and sent chat. Lowercase and uppercase Latin accent samples
and `漢字` were also readable in sent chat. Emoji displayed as boxes in sent
WoW chat, so game character support is a separate limitation.

The implementation keeps `ydotool type` for ASCII and uses a temporary X11
clipboard plus Ctrl+V for non-ASCII. `xclip` is a separate GPL-2.0 program
bundled with its license; no xclip source is copied into MIT-licensed Python.
The prior text clipboard is restored after paste, unless another application
changed it meanwhile. A clipboard offering non-text formats is left untouched
and the message is not sent. A missing display or xclip similarly prevents a
send rather than silently dropping characters. Control characters are rejected.

## Remaining validation before release

The standalone probe used `xdotool` to press Ctrl+V. The integrated code uses
Decktation's private root-owned `ydotool` daemon. A clean v0.3.17 plus Unicode
build was installed on the Deck and tested in Gaming Mode with WoW foregrounded
and the QAM closed. Several real dictated accented messages appeared correctly
in sent chat, once per recording, and controls remained normal. No injection
error was logged. Clipboard access from the Decky root backend uses the `deck`
user. The helper was separately smoke-tested on the Deck, including text
restoration. Other games and keyboard layouts remain unverified.

The standalone probe can be repeated without changing Decktation. Stage
`xclip` in `/tmp` from the SteamOS package mirror, then run the script:

```sh
ssh steamdeck 'curl -fsSL -o /tmp/decktation-xclip.pkg.tar.zst https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.8/os/x86_64/xclip-0.13-6-x86_64.pkg.tar.zst && mkdir -p /tmp/decktation-xclip-probe && bsdtar -xf /tmp/decktation-xclip.pkg.tar.zst -C /tmp/decktation-xclip-probe usr/bin/xclip'
ssh steamdeck 'bash -s' < tests/manual/clipboard_probe.sh
```

The probe opens chat and pastes into a draft without sending by default. Set
`DECKTATION_PROBE_SEND=1` in the remote command only when sending a visible
test message is intended. It restores prior plain-text clipboard content.

## Backup and restore for an approved development deployment

Create the backup as the `deck` user; this does not need sudo:

```sh
ssh steamdeck 'tar -C /home/deck/homebrew -czf /home/deck/decktation-pre-unicode-issue25.tar.gz plugins/decktation settings/decktation && tar -tzf /home/deck/decktation-pre-unicode-issue25.tar.gz >/dev/null'
```

If development files must be rolled back, restore the backed-up plugin and
settings, then restart Decky (sudo is required because the installed plugin
is root-owned):

```sh
ssh -t steamdeck 'sudo tar -C /home/deck/homebrew -xzf /home/deck/decktation-pre-unicode-issue25.tar.gz && sudo systemctl restart plugin_loader.service'
```

## Physical test plan

1. In Gaming Mode with WoW foregrounded and the QAM closed, use the WoW preset
   to dictate `¡Mañana iré a la misión con Lucía! ¿Vienes tú? Français,
   português, über.` Check the edit box and sent chat for exact accents and
   punctuation.
2. Repeat with `ÁÉÍÓÚ Ñ Ç`, ordinary ASCII, and `漢字`. Confirm each cue
   opens and sends once. Emoji may render as boxes in WoW; record this
   limitation rather than interpreting it as a Decktation typing failure.
3. Turn on manual send. Confirm a Unicode transcription remains in the draft
   until the user sends it. Try party and other channel prefixes.
4. Test the Generic preset in a focused text field: one ASCII phrase, one
   accented phrase, and one failure case with a non-text clipboard. Confirm
   Generic never presses Enter and the prior clipboard content is restored.
5. Where practical, change the Deck keyboard layout and repeat. The Unicode
   clipboard route should not depend on Whisper language or keyboard layout.
   Verify controller input works normally afterwards.

## Proposed pull request

**Title:** Preserve Unicode dictation in game text input (fixes #25)

**Description:** Use a temporary X11 clipboard paste for non-ASCII
transcriptions while preserving the existing fast `ydotool type` path for
ASCII. Keep channel prefixes, game presets and manual send behavior, restore
prior text clipboard contents, and report injection failures. Add focused
Unicode and clipboard tests. Physically tested standalone paste in SteamOS
Gaming Mode with WoW: the requested accented sample, uppercase accents and
CJK characters appeared in sent chat; WoW renders emoji as boxes. Integrated
Decktation dictation in WoW was also physically validated: accented messages
appeared correctly, once per recording, and controls remained normal. Generic
preset and other keyboard layouts remain untested.
