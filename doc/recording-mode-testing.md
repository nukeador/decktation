# Hold or toggle recording

Select the recording mode in Advanced → Recording binding → Mode.

- **Hold to record** is the default. Recording starts on press and ends on release.
- **Tap to start/stop**: tap the binding to begin, speak without holding it, then tap again to stop and transcribe. Holding it for 250 ms or longer still stops on release for quick messages.

The toggle option improves accessibility for people who find it difficult, tiring or uncomfortable to hold a button combination for an entire dictation. Transcription still follows the configured sending/review mode.

## Physical checks

1. Confirm the default hold mode records once and stops on release.
2. Select tap mode. A short tap must keep recording after release; a second tap must stop once.
3. In tap mode, hold for a longer message and release. Recording must stop on release.
4. Check recording indicators and start/stop haptics stay on the initiating controller.
5. While recording after a tap, disconnect that controller or disable Decktation. Recording must be cancelled, without sending a partial transcript.
6. In Review before sending, confirm tap-to-send and hold-to-cancel still work and do not start another recording.
7. Switch modes and reload the plugin. The saved mode must persist.
8. Confirm button presses during transcription do not start a delayed recording afterward.

The earlier combined branch's mode was tested on a Steam Deck. This independent version on current master needs fresh hardware validation.
