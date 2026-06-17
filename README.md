# ytt — YouTube Transcript CLI

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB.svg)

A small, dependency-light command-line tool to fetch a YouTube transcript by URL
or video ID and print / copy / save it in several formats — with translation,
clean-up, batch processing and optional AI summaries. The terminal companion to
the [browser extension (`yt-transcript-studio`)](https://github.com/krishnakanthb13/yt-transcript-studio).

## First time? Start here (no experience needed)

**Windows**
1. Install **Python** from [python.org/downloads](https://www.python.org/downloads/).
   On the first screen, **tick "Add Python to PATH"**, then click Install.
2. Download the project (green **Code → Download ZIP**) and **unzip** it.
3. Open the **`yt-transcript-cli`** folder and **double-click `ytt.bat`**.
4. The first run installs what it needs, then an **interactive wizard** asks you —
   one step at a time — for the link, format, language, translation, clean-up,
   save folder and AI summary. Press Enter to take any default.
5. Your transcript is **copied to the clipboard** and **saved** where you chose. Done!

**macOS / Linux**
1. Check Python 3 is present: `python3 --version` (install from python.org if not).
2. Download & unzip the project, open a Terminal in **`yt-transcript-cli`**.
3. First time only: `chmod +x ytt.sh`
4. Run: `./ytt.sh "https://youtu.be/VIDEOID"`

Once comfortable, use the options below to choose the language, format and
output folder.

## How it fetches (and why it's reliable)

Like the browser extension, the CLI fetches captions through YouTube's
**InnerTube `player` endpoint using a non-web client (ANDROID/IOS)** — whose
caption URLs aren't PoToken-gated — then pulls `json3` from there (this is also
what makes **translation** work). `youtube-transcript-api` is kept as an
automatic fallback. The InnerTube path uses only the Python standard library.

## Requirements

- **Python 3.8+**
- [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) — fallback engine + `--list`
- [`pyperclip`](https://pypi.org/project/pyperclip/) — optional (clipboard)

The `ytt.bat` and `ytt.sh` launchers auto-install these on first run. To install
manually:

```bash
pip install youtube-transcript-api pyperclip
```

## Interactive mode (no flags to remember)

Run with **no video argument** — or pass `--interactive` / `-i`, or just
**double-click `ytt.bat`** — and the tool walks you through every option in
order, each with a default you can accept by pressing Enter:

```text
1. YouTube URL or video ID
2. Output format (txt/time/srt/vtt/md/csv/json)
3. Caption language code (blank = auto)
4. Translate to language code (blank = no)
5. Remove [Music]/[Applause] sound cues? (y/n)
6. Merge into readable paragraphs? (y/n)
7. Save to a file?  →  which folder?
8. AI summary? (none/summary/bullets/chapters/takeaways)  →  Gemini key
```

Power users can skip the wizard entirely by passing flags, documented below.

## Usage

```bash
python ytt.py <url-or-id> [more urls…] [options]
```

The input can be a full URL (`watch`, `youtu.be`, `/shorts/`, `/embed/`) or a
bare 11-character video ID. You can pass **several** at once (batch). Saved files
are named `<videoId>_<timestamp>.<ext>` (AI summaries add `_summary.md`).

### All options

| Option | Description |
|---|---|
| `<video>…` | One or more YouTube URLs/IDs (positional). Omit to be prompted. |
| `--batch-file FILE` | Read URLs/IDs from a file, one per line (`#` lines ignored). |
| `--lang`, `-l CODE` | Preferred caption language (`en`, `es`, `hi`, …). |
| `--translate`, `-t CODE` | Translate the transcript into this language. |
| `--format`, `-f FMT` | `txt` (default), `time`, `srt`, `vtt`, `md`, `csv`, `json`. |
| `--clean` | Strip `[Music]` / `[Applause]` / ♪ sound cues. |
| `--paragraphs`, `-p` | Merge choppy fragments into readable paragraphs. |
| `--out`, `-o DIR` | Folder to save into (default: current folder). |
| `--list` | List the video's available caption languages and exit. |
| `--no-save` | Print only; don't write a file. |
| `--no-copy` | Don't copy to the clipboard. |
| `--ai MODE` | AI summary: `summary`, `bullets`, `chapters`, or `takeaways`. |
| `--ai-model NAME` | Gemini model (default: `gemini-3.5-flash`). |
| `--gemini-key KEY` | Gemini API key (or set `GEMINI_API_KEY`). |
| `--interactive`, `-i` | Ask for every option step by step (see below). |

Every run prints quick **stats** (lines · words · duration · reading time).
In batch mode the clipboard copy and stdout dump are skipped (files are written).

### Output formats

| `--format` | File | Use it for |
|---|---|---|
| `txt` | `.txt` | A clean paragraph for reading/pasting |
| `time` | `.txt` | One line per cue, prefixed with `[m:ss]` |
| `srt` | `.srt` | Subtitles for most editors/players |
| `vtt` | `.vtt` | Subtitles for the web / HTML5 |
| `md` | `.md` | Markdown with clickable `?t=` timestamp links |
| `csv` | `.csv` | Spreadsheets (`start_seconds, timecode, text`) |
| `json` | `.json` | Programmatic use (`start`, `dur`, `text`) |

These match the [browser extension](https://github.com/krishnakanthb13/yt-transcript-studio)'s
exports byte-for-byte.

## Examples

```bash
# Plain text, saved to the current folder and copied to the clipboard
python ytt.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# SRT subtitles in English, into a specific folder
python ytt.py dQw4w9WgXcQ --lang en --format srt --out ./transcripts

# Translate to Spanish, as Markdown with timestamp links
python ytt.py dQw4w9WgXcQ --translate es --format md

# Clean + merge into paragraphs, print only
python ytt.py dQw4w9WgXcQ --clean --paragraphs --no-save --no-copy

# Batch several videos, or a file of URLs
python ytt.py URL1 URL2 URL3 --format srt --out ./out
python ytt.py --batch-file urls.txt --out ./out

# AI summary (needs a Gemini key)
export GEMINI_API_KEY=AIza...            # Windows: set GEMINI_API_KEY=AIza...
python ytt.py dQw4w9WgXcQ --ai summary
python ytt.py dQw4w9WgXcQ --ai chapters --gemini-key AIza...

# What languages are available?
python ytt.py dQw4w9WgXcQ --list
```

### AI summaries

`--ai` calls Google **Gemini** directly (standard-library HTTP — no extra
dependency) using **your own key**. Get a free key at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) and pass it via
`--gemini-key` or the `GEMINI_API_KEY` environment variable. Modes: `summary`
(overview + key points), `bullets` (outline), `chapters` (timestamped), and
`takeaways` (action items). The summary prints and is saved next to the
transcript as `<id>_<timestamp>_summary.md`. Default model: **`gemini-3.5-flash`**.

### Windows

```bat
ytt.bat https://youtu.be/dQw4w9WgXcQ --format srt
```

Double-click `ytt.bat` with no arguments to be prompted for a URL/ID; the window
stays open so you can read the result.

### macOS / Linux

```bash
chmod +x ytt.sh        # first time only
./ytt.sh dQw4w9WgXcQ --format vtt --out ~/transcripts
```

---

## License

**ytt — YouTube Transcript CLI** — Copyright (C) 2026 Krishna Kanth B.
Free software under the **GNU General Public License v3** (or any later version);
distributed WITHOUT ANY WARRANTY. See [LICENSE](LICENSE) or
<https://www.gnu.org/licenses/>.

---

Companion to the [browser extension](https://github.com/krishnakanthb13/yt-transcript-studio).
Free — [support it 💛](https://krishnakanthb13.github.io/S/).
