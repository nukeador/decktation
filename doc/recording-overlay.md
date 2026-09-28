# Gaming Mode recording indicator

This branch replaces the short Steam recording toast with a Gamescope overlay. The
existing `showNotifications` preference controls the recording indicator and the
pending-send confirmation alert. Saved preferences keep their current meaning.

The backend starts a separate `/usr/bin/python3` process as the `deck` user on the
first recording. It finds Gamescope's main Xwayland display through
`GAMESCOPE_XWAYLAND_SERVER_ID = 0`, sets `GAMESCOPE_EXTERNAL_OVERLAY = 1` on an
RGBA GTK 3 window, and gives that window an empty input region. The window never
requests focus. The full-display surface is transparent; only a 368 × 80 pixel
pill is drawn near the bottom center. Nine bars animate at 20 frames per second.
A state file switches the indicator between recording, transcribing, and hidden
without relaunching it. Disabling the setting hides it; unloading the plugin
stops the child and removes its temporary state directory. If the plugin process
exits unexpectedly, the child detects its missing parent and exits. Overlay
errors are logged and do not stop recording or transcription.

Runtime dependencies are the SteamOS system Python, PyGObject/GTK 3, PyCairo,
`xprop`, and Gamescope's external overlay support. No microphone or network
access is used by the indicator. `DECKTATION_OVERLAY_DISPLAY` may override
automatic Xwayland selection for development.

## Validation

- Standalone visual prototype displayed over WoW in Gaming Mode with QAM closed.
  The first small window appeared at the top left; a transparent full-display
  window placed the pill at the bottom center.
- The Deck owner confirmed the doubled translucent pill looked good and WoW
  chat, accented dictation, and controller input continued normally.
- A standalone run of the integrated manager on the Deck exercised recording,
  transcribing, hiding, and process cleanup. The integrated plugin still needs
  an in-game installation test before this behavior is considered released.

The design uses proportions studied in [Handy's recording overlay](https://github.com/cjpais/Handy/blob/main/src/overlay/RecordingOverlay.css).
The Gamescope property approach was studied in [OverLaid's backend](https://github.com/TheLogicMaster/OverLaid/blob/main/backend/main.cpp).
No source code from either project was copied.
