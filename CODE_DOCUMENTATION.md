# Code Documentation — ytt (YouTube Transcript CLI)

## 1. File & folder structure

| Path | Description |
|---|---|
| `ytt.py` | The entire tool (Python 3.8+). Parsing, fetching, formatting, AI, wizard, CLI. |
| `ytt.bat` | Windows launcher — ensures deps, then runs `ytt.py`, forwarding all args. |
| `ytt.sh` | macOS/Linux launcher — same role. |
| `requirements.txt` | `youtube-transcript-api` (fallback engine) + optional `pyperclip`. |
| `README.md` | Usage, options, examples, interactive mode. |
| `CONTRIBUTING.md` · `SECURITY.md` · `CHANGELOG.md` | Project meta. |
| `LICENSE` | GNU GPL v3. |

## 2. High-level architecture

One file, three layers:

1. **Pure helpers** — `extract_video_id`, `clean`, `clock`/`hms`, the formatters,
   `strip_sound_cues`, `merge_paragraphs`, `parse_json3`, `stats`. No I/O; easy to
   test.
2. **Fetch engine** — `innertube_fetch` (primary; mirrors the browser extension)
   with `_yta_fetch` (youtube-transcript-api) as a fallback; `_urlopen` adds 429
   backoff.
3. **Driver** — `process` (one video) and `main` (argparse, batch loop) plus the
   `wizard` interactive flow.

## 3. Core functions

| Function | Purpose |
|---|---|
| `extract_video_id(value)` | Bare ID or any YouTube URL (watch/`youtu.be`/shorts/embed) → 11-char ID. |
| `_innertube_player(id, client)` | POST `youtubei/v1/player` with a non-web client; returns player JSON. |
| `_fetch_timedtext_json3(baseUrl, translate)` | Force `fmt=json3` (+ optional `tlang`) and GET the caption data. |
| `parse_json3(text)` | `json3` → `{text, start, duration}[]`. |
| `innertube_fetch(id, lang, translate)` | ANDROID→IOS clients → picked track → json3 → segments. |
| `_yta_fetch(id, lang, translate)` | Fallback via `youtube-transcript-api`. |
| `fetch_snippets(id, lang, translate)` | Try InnerTube, then fallback. |
| `strip_sound_cues` / `merge_paragraphs` | `--clean` / `--paragraphs` transforms. |
| `to_txt/to_timestamped/to_srt/to_vtt/to_md/to_csv/to_json`, `render` | Exports. |
| `ai_summarize(snips, title, mode, key, model)` | Gemini summary (`--ai`). |
| `wizard(args)` | Sequential interactive prompts. |
| `process` / `main` | Per-video flow / argument parsing + batch. |

## 4. Data flow

```
URL/ID ─→ extract_video_id ─→ fetch_snippets
                                 ├─ innertube_fetch:  POST youtubei/v1/player {ANDROID/IOS}
                                 │                     → caption baseUrl → GET &fmt=json3[&tlang]
                                 │                     → parse_json3 → snippets
                                 └─ (fallback) _yta_fetch via youtube-transcript-api
snippets ─→ [strip_sound_cues?] ─→ [merge_paragraphs?] ─→ render(format) ─→ stdout / file / clipboard
                                                          └→ ai_summarize (optional) ─→ print + _summary.md
```

## 5. Dependencies

- **Runtime (required):** `youtube-transcript-api` (fallback engine + `--list`).
- **Runtime (optional):** `pyperclip` (clipboard). AI uses only the standard
  library (`urllib`).
- **Dev:** none beyond Python; CI runs an AST syntax check.

## 6. Execution flow (entry → output)

1. `main` parses args. With no video (or `-i`, or a `ytt.bat` double-click on a
   TTY) it runs `wizard` to collect every option.
2. For each target, `process` fetches snippets, applies `--clean` / `--paragraphs`,
   prints stats, renders the chosen format, copies (single run) and/or saves.
3. With `--ai`, it calls Gemini and prints + saves a `_summary.md`.
4. Batch runs report `N/M succeeded`.
