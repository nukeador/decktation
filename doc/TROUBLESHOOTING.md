# Troubleshooting

## Find the plugin logs

Decktation writes timestamped logs through Decky. The usual directory is:

```text
/home/deck/homebrew/logs/decktation/
```

Open the newest log for the current session. For example, in Desktop Mode:

```bash
ls -lt /home/deck/homebrew/logs/decktation/*.log
```

Controller-listener output is forwarded into the plugin log. Decktation no longer creates `/tmp/decktation.log`.

## Plugin does not become ready

- Wait for **Initializing service...** to finish.
- If the panel says **Keyboard helper unavailable**, reload the plugin. If it persists, reinstall using a packaged ZIP from the [installation guide](INSTALLATION.md).
- Check the latest Decktation log for backend or model-loading errors.
- The first use of a selected Whisper model downloads its files from Hugging Face; connect the Deck to the internet until the download completes.

## Test recording does not transcribe

Enable Decktation and wait for **Ready**, then select **Test Recording (3s)** and speak clearly while it records. Check that the Steam Deck microphone or connected headset works in another app. The test displays its transcription in the panel and does not type it into the focused app.

## Push-to-talk is not detected

- Open the plugin panel and check **Input**. It should show **OK** and display held buttons while you press them.
- Confirm the configured combination is held on one controller; buttons from different devices cannot be combined.
- Try a different combination, reconnect the controller, and check the latest log for controller-listener errors.
- Some Steam Input keyboard-and-mouse layouts do not expose gamepad controls. Third-party paddles may not appear as distinct buttons.
- If only one controller maps its buttons incorrectly, see [custom controller mappings](ADVANCED_CONFIGURATION.md#custom-controller-mappings).

## Transcription is slow or inaccurate

- Speak clearly and reduce background noise.
- Set **Lang** to the language you are speaking, or leave it on **Auto**.
- Base is fastest, Small is a balanced choice, and Medium is more accurate but slower.
- The WoW addon can add its latest saved context, but it does not reliably stream target or group changes during a session. See the [WoW context guide](WOW_INTEGRATION.md) for the limitation and upstream discussion.

## Text is missing or goes to the wrong place

- Put focus in the intended text field before using push-to-talk.
- Use **Generic** to enter text directly in the focused field. WoW and GW2 presets open their in-game chat and add a channel command.
- If **Manual** is on, Decktation enters the message and waits for you to press Enter.
- Check the panel for **Keyboard helper unavailable** and inspect the latest plugin log for `ydotoold` errors. Reload or reinstall the packaged plugin if the helper did not start.
- Use **Confirm** if you want a brief chance to cancel a game message before it is sent.
