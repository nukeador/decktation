# Haptic feedback development and Deck validation

This feature is off by default. It uses the Steam Deck's vendor HID rumble
command, so it does not need the Decktation panel to be mounted. It does not
control external gamepads.

Protocol reference: [Linux `hid-steam.c`](https://github.com/torvalds/linux/blob/master/drivers/hid/hid-steam.c),
specifically `steam_haptic_rumble()` and `steam_send_report_id()`.

## Hardware proof of concept

On the tested Steam Deck (Valve HID `28de:1205`, vendor interface `input2`),
the 0x8f trackpad pulse was felt with the QAM open and with WoW foregrounded,
but remained too subtle for gameplay even at +6 dB. The Deck's evdev devices
reported no force-feedback capability. The 0xeb rumble command was clear and
comfortable in WoW with the QAM closed at speed 45000: one 150 ms burst for
start and two 100 ms bursts for stop. Controller input continued working. The
integrated plugin has not yet been installed or tested on the Deck.

To repeat the standalone manual test, copy only the script to `/tmp`:

```sh
scp scripts/test_deck_rumble.py steamdeck:/tmp/decktation-rumble-test.py
ssh steamdeck 'python3 /tmp/decktation-rumble-test.py start'
ssh steamdeck 'python3 /tmp/decktation-rumble-test.py stop'
```

Run each command once while holding the Deck. The script sends a stop command
in `finally`. It does not alter the installed plugin or settings.

## Opt-in development deployment

The installed stable plugin and this checkout share the same Decky identity.
Do this only after explicitly choosing to replace the installed files for a
development test. The inspected Deck uses the system `plugin_loader.service`
and `/home/deck/homebrew/plugins/decktation`.

Back up the complete stable plugin and settings before copying anything:

```sh
ssh -tt steamdeck 'sudo tar -C /home/deck/homebrew -czf /home/deck/decktation-stable-backup.tar.gz plugins/decktation settings/decktation && sudo chown deck:deck /home/deck/decktation-stable-backup.tar.gz'
```

From the repository root, build the frontend and stage only the changed files:

```sh
npm run build
ssh steamdeck 'mkdir -p /tmp/decktation-dev'
scp backend/src/decktation_backend.py backend/src/wow_voice_chat.py backend/src/haptic_feedback.py dist/index.js steamdeck:/tmp/decktation-dev/
ssh -tt steamdeck 'sudo install -m 0644 /tmp/decktation-dev/decktation_backend.py /home/deck/homebrew/plugins/decktation/bin/decktation_backend.py && sudo install -m 0644 /tmp/decktation-dev/wow_voice_chat.py /home/deck/homebrew/plugins/decktation/bin/wow_voice_chat.py && sudo install -m 0644 /tmp/decktation-dev/haptic_feedback.py /home/deck/homebrew/plugins/decktation/bin/haptic_feedback.py && sudo install -m 0644 /tmp/decktation-dev/index.js /home/deck/homebrew/plugins/decktation/dist/index.js && sudo systemctl restart plugin_loader.service'
```

After Decky returns, enable **Haptic feedback** in Decktation. Test both the
physical push-to-talk binding in WoW with QAM closed and **Test Recording
(3s)** in the QAM. Verify start and stop cues, no duplicate cues, normal
controller input, and no text sent by the test action. Turn the setting off
and repeat to confirm silence. Keep the setting off on unsupported hardware.

Restore stable files and settings from the backup:

```sh
ssh -tt steamdeck 'sudo tar -C /home/deck/homebrew -xzf /home/deck/decktation-stable-backup.tar.gz && sudo rm -f /home/deck/homebrew/plugins/decktation/bin/haptic_feedback.py && sudo systemctl restart plugin_loader.service'
```

The repository's GitHub Actions build workflow produces and validates the
final Decky ZIP. This file-level workflow is only for local development.
