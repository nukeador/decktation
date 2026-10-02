# Third-party notices

Decktation's store artifact includes unmodified `ydotool` and `ydotoold`
version 1.0.4, built from commit
`57ba7d0af525e82da2de0e275d169477f293b197`.

- Source: <https://github.com/ReimuNotMoe/ydotool/tree/v1.0.4>
- License: GNU Affero General Public License v3.0 or later
- Build recipe: `backend/Dockerfile`
- Packaged license: `bin/licenses/ydotool-AGPL-3.0.txt`

The Python packages included under `bin/python` retain their package metadata,
license classifiers, and license files as provided by their respective wheels.

The store artifact also includes the unmodified SteamOS/Arch Linux PortAudio
shared library used by `sounddevice`:

- Upstream source: <https://github.com/PortAudio/portaudio>
- SteamOS package: `portaudio`
- License: MIT
- Packaged license: `bin/licenses/portaudio-MIT.txt`

## Companion capture runtime

The optional bundled `companion-capture` helper dynamically links the existing
SteamOS GLib/GIO (LGPL-2.1-or-later) and PipeWire (MIT) libraries. Their Debian
copyright/license notices are included under `bin/licenses/companion-*` in the
plugin package. No runtime library installation is performed by the plugin.
The Companion decoder and capture implementation are MIT code adapted from our
standalone POC; the wow-ai and wow-forever-codex projects informed the design,
but their source is not included in this implementation.
