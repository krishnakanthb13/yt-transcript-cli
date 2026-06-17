# Design Philosophy — ytt (YouTube Transcript CLI)

## 1. The problem

Sometimes you don't want a browser — you want to pull a transcript (or a hundred)
from a script, a server, or a terminal, in the exact format you need. Most
libraries broke when YouTube added PoToken gating in 2025, and most "tools" are
web apps that can't be automated.

## 2. Why this solution

A single, dependency-light Python script that fetches reliably (the same
InnerTube approach the browser extension uses), supports batch and automation,
and produces the **same output formats** as the extension — so a `.srt` from the
CLI and from the extension are identical. It's friendly enough for a non-coder
(an interactive wizard, a double-click `.bat`) and scriptable enough for a power
user (flags, batch files, exit-coded errors).

## 3. Design principles

- **Reliability first.** InnerTube primary, `youtube-transcript-api` fallback,
  429 backoff for batches.
- **Parity with the extension.** Same formats, same clock/SRT/VTT rules, same
  clean/paragraph behavior — one mental model across both tools.
- **Dependency-light & standard-library-first.** AI and fetching use only
  `urllib`; the one hard dependency is the fallback engine.
- **Approachable and scriptable.** A wizard for newcomers; flags, batch and
  stdout for automation.
- **Private.** Runs locally; your Gemini key comes from a flag/env var and goes
  only to Google.

## 4. Target audience & use cases

- **Developers / analysts** — batch-fetch transcripts for a dataset or pipeline.
- **Power users** — a fast terminal grab in any format.
- **Non-technical users** — double-click `ytt.bat`, answer a few prompts, done.
- **Creators** — generate subtitle files (`.srt`/`.vtt`) at the command line.

## 5. Real-world workflow fit

`python ytt.py <url> --format srt` in a build script; `--batch-file urls.txt` for
a backlog; `--ai summary` to triage long videos; the wizard for a one-off when
you don't want to remember flags. Output drops into your editor, repo, or
spreadsheet (`--format csv`).

## 6. Trade-offs & constraints

- **Undocumented InnerTube API.** May change; the layered clients + fallback
  hedge against breakage.
- **`--list` and the fallback need `youtube-transcript-api`.** The primary fetch
  does not, but listing languages relies on it.
- **AI is bring-your-own-key.** Keeps the tool free and private.
- **Caption quality** is YouTube's; `--clean`/`--paragraphs` only tidy it.
