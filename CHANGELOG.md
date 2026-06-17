# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-06-17

Initial public release.

### Added
- Fetch a YouTube transcript by URL or 11-char ID (watch / `youtu.be` / Shorts /
  embed).
- Reliable **InnerTube** engine (standard-library `urllib`, ANDROID/IOS client)
  so fetching **and translation** work; `youtube-transcript-api` kept as a
  fallback, with 429 backoff for batch runs.
- Formats: `txt`, `time`, `srt`, `vtt`, `md`, `csv`, `json` (byte-for-byte
  matched with the browser extension).
- `--translate`, `--clean` (strip `[Music]`/`[Applause]`), `--paragraphs`
  (merge fragments), `--lang`, `--list`.
- **Batch** processing (multiple URLs or `--batch-file`).
- **AI summaries** (`--ai summary|bullets|chapters|takeaways`) via your own
  Google Gemini key (`--gemini-key` / `GEMINI_API_KEY`).
- **Interactive wizard** when run with no arguments (drives the `ytt.bat`
  double-click experience); reading stats; clipboard copy via optional
  `pyperclip`; UTF-8 console output on Windows.
- `ytt.bat` and `ytt.sh` launchers that auto-install dependencies.

[1.0.0]: https://github.com/krishnakanthb13/yt-transcript-cli/releases/tag/v1.0.0
