# Customizations (piper-speak branch)

This branch is based on upstream commit `c3c88ae`. It holds the version installed at
`~/.local/bin/gnome-ocr-screenshot`. `main` tracks upstream unchanged.

## Changes from upstream

- **Speak button.** Reads the extracted text aloud through Speech Dispatcher (`spd-say`).
  The button changes to Pause and Resume while audio plays, and closing the dialog stops
  playback.
- **Piper voice.** `extras/speech-dispatcher/piper-generic.conf` goes in
  `~/.config/speech-dispatcher/modules/`. It runs Piper (`/opt/piper`) into
  `/tmp/piper_tts.wav` and plays the file with `pw-play`. The Speak button watches that
  process to know when playback ends.
- **Retake delay** raised from 150 ms to 600 ms, so GNOME's window animations finish
  before the next screenshot.
- Larger dialog (600x450), and saved files are named `ocr_HH-MM.txt`.

## Removed compared with upstream

This version was a trimmed rewrite, so it drops these upstream features: QR code
decoding (pyzbar), syslog logging, `--enable-saving`, `--save-location` and
`--no-close-on-action`. Only `--lang` remains.
