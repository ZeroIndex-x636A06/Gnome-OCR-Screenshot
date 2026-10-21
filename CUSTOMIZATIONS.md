# Customizations (piper-speak branch)

This branch is upstream `main` plus the changes below. Every upstream feature is kept:
QR codes, `--autocopy`, `--preprocess`, `--psm`, `--save-location`, `--enablesaving` and
`--nocloseonaction`. The first version of these changes, built on the older upstream
commit `c3c88ae`, is kept as the tag `piper-speak-c3c88ae`.

## Changes from upstream

- **Speak button.** Reads the extracted text aloud through Speech Dispatcher (`spd-say`).
  It is enabled once OCR finishes. While audio plays it changes to Pause and Resume, and
  closing the dialog stops playback, even while paused.
- **Piper voice.** `extras/speech-dispatcher/piper-generic.conf` goes in
  `~/.config/speech-dispatcher/modules/`, with `piper-generic` set as `DefaultModule` in
  `speechd.conf`. It runs Piper (`/opt/piper`) into `/tmp/piper_tts.wav` and plays the
  file with `pw-play`. The Speak button watches the module's shell (the `TMPWAV=` line)
  to know when an utterance ends, and pauses only the Piper and `pw-play` processes for
  that file. Other audio is not touched.
- **Retake delay** raised from 150 ms to 600 ms, so GNOME's window animations finish
  before the next screenshot.
- Larger dialog (600x450), and saved files are named `ocr_HH-MM.txt`.

## Install

`make install` symlinks `~/.local/bin/gnome-ocr-screenshot` to this checkout.
