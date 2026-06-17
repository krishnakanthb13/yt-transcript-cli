#!/usr/bin/env python3
"""
ytt.py — YouTube Transcript fetcher (CLI companion to Transcript Studio).

Fetch a transcript by URL or video ID — in any language, translated, cleaned,
merged into paragraphs — and print / copy / save it as TXT, timestamped TXT,
SRT, VTT, Markdown, CSV or JSON. Optionally summarize it with Google Gemini.

Examples
--------
    python ytt.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
    python ytt.py dQw4w9WgXcQ --lang en --format srt --out ./transcripts
    python ytt.py dQw4w9WgXcQ --translate es --format md
    python ytt.py dQw4w9WgXcQ --clean --paragraphs --format txt
    python ytt.py dQw4w9WgXcQ --list                     # list languages
    python ytt.py URL1 URL2 URL3 --format srt            # batch
    python ytt.py --batch-file urls.txt --out ./out
    python ytt.py dQw4w9WgXcQ --ai summary               # needs a Gemini key

AI key: pass --gemini-key or set the GEMINI_API_KEY environment variable.

Dependencies (auto-installed by ytt.bat / ytt.sh, or: pip install ...):
    youtube-transcript-api      required
    pyperclip                   optional (clipboard); silently skipped if absent
(AI uses only the Python standard library — no extra dependency.)
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


def _urlopen(req, timeout=30, tries=3):
    """urlopen with simple backoff on 429 (rate limiting) for batch-friendliness."""
    for i in range(tries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2 * (i + 1))
                continue
            raise

# Public, long-standing YouTube web key — used for the InnerTube player call.
INNERTUBE_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    sys.exit("Missing dependency. Run:  pip install youtube-transcript-api")

try:
    import pyperclip
except ImportError:
    pyperclip = None

# Windows consoles default to cp1252 and crash on non-ASCII (transcripts, emoji).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_AI_MODEL = "gemini-3.5-flash"


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def extract_video_id(value: str) -> str:
    """Accept a bare ID or any common YouTube URL shape and return the ID."""
    value = value.strip()
    patterns = [
        r"(?:v=|/watch\?.*v=)([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"/shorts/([A-Za-z0-9_-]{11})",
        r"/embed/([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, value)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    raise ValueError(f"Could not find a video ID in: {value!r}")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def hms(seconds: float, sep: str) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def clock(seconds: float) -> str:
    s = int(seconds)
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


# --------------------------------------------------------------------------- #
# View transforms (mirror the extension's lib/captions.js)
# --------------------------------------------------------------------------- #
def strip_sound_cues(snips):
    out = []
    for s in snips:
        txt = clean(re.sub(r"\[[^\]]*\]", " ", s["text"]).replace("♪", " ").replace("\U0001f3b5", " "))
        if txt:
            out.append({**s, "text": txt})
    return out


def merge_paragraphs(snips, max_gap=2.5, max_chars=300):
    out, cur = [], None
    for s in snips:
        if cur is None:
            cur = {"start": s["start"], "duration": s.get("duration", 0), "text": clean(s["text"])}
            continue
        gap = s["start"] - (cur["start"] + cur["duration"])
        fits = len(cur["text"]) + len(s["text"]) + 1 <= max_chars
        sentence_end = bool(re.search(r"[.!?][\"')\]]?$", cur["text"]))
        if gap <= max_gap and fits and not sentence_end:
            cur["text"] = clean(cur["text"] + " " + s["text"])
            cur["duration"] = (s["start"] + s.get("duration", 0)) - cur["start"]
        else:
            out.append(cur)
            cur = {"start": s["start"], "duration": s.get("duration", 0), "text": clean(s["text"])}
    if cur:
        out.append(cur)
    return out


# --------------------------------------------------------------------------- #
# Formatters
# --------------------------------------------------------------------------- #
def _end(snips, i):
    s = snips[i]
    if s.get("duration"):
        return s["start"] + s["duration"]
    return snips[i + 1]["start"] if i + 1 < len(snips) else s["start"] + 2


def to_txt(snips, _vid=None):
    return clean(" ".join(s["text"] for s in snips))


def to_timestamped(snips, _vid=None):
    return "\n".join(f"[{clock(s['start'])}] {clean(s['text'])}" for s in snips)


def to_srt(snips, _vid=None):
    return "\n".join(
        f"{i + 1}\n{hms(s['start'], ',')} --> {hms(_end(snips, i), ',')}\n{clean(s['text'])}\n"
        for i, s in enumerate(snips)
    )


def to_vtt(snips, _vid=None):
    body = "\n\n".join(
        f"{hms(s['start'], '.')} --> {hms(_end(snips, i), '.')}\n{clean(s['text'])}"
        for i, s in enumerate(snips)
    )
    return f"WEBVTT\n\n{body}\n"


def to_md(snips, vid=None):
    lines = []
    for s in snips:
        ts = clock(s["start"])
        if vid:
            lines.append(f"- [`{ts}`](https://youtu.be/{vid}?t={int(s['start'])}s) {clean(s['text'])}")
        else:
            lines.append(f"- `{ts}` {clean(s['text'])}")
    return "\n".join(lines) + "\n"


def to_csv(snips, _vid=None):
    def esc(v):
        return '"' + str(v).replace('"', '""') + '"'
    rows = ["start_seconds,timecode,text"]
    for s in snips:
        rows.append(f'{s["start"]:.2f},{clock(s["start"])},{esc(clean(s["text"]))}')
    return "\n".join(rows) + "\n"


def to_json(snips, _vid=None):
    return json.dumps(
        [{"start": round(s["start"], 3), "dur": round(s.get("duration", 0), 3), "text": clean(s["text"])}
         for s in snips],
        ensure_ascii=False, indent=2,
    )


FORMATTERS = {"txt": to_txt, "time": to_timestamped, "srt": to_srt, "vtt": to_vtt,
              "md": to_md, "csv": to_csv, "json": to_json}
EXTS = {"txt": "txt", "time": "txt", "srt": "srt", "vtt": "vtt", "md": "md", "csv": "csv", "json": "json"}


def render(fmt, snips, vid):
    return FORMATTERS[fmt](snips, vid)


def stats(snips):
    text = to_txt(snips)
    words = len(text.split()) if text else 0
    duration = _end(snips, len(snips) - 1) if snips else 0
    return {"lines": len(snips), "words": words, "chars": len(text),
            "duration": clock(duration), "read_min": max(1, round(words / 200))}


# --------------------------------------------------------------------------- #
# Transcript API (works across youtube-transcript-api versions)
# --------------------------------------------------------------------------- #
def _listing(video_id):
    try:                                            # v1.x instance API
        return YouTubeTranscriptApi().list(video_id)
    except (AttributeError, TypeError):             # older static API
        return YouTubeTranscriptApi.list_transcripts(video_id)


def list_languages(video_id):
    rows = []
    for tr in _listing(video_id):
        kind = "auto" if getattr(tr, "is_generated", False) else "manual"
        extra = " [translatable]" if getattr(tr, "is_translatable", False) else ""
        rows.append((tr.language_code, tr.language, kind + extra))
    return rows


def _yta_fetch(video_id, lang=None, translate=None):
    """Fallback path via youtube-transcript-api (translation may be unavailable)."""
    listing = _listing(video_id)
    tr = None
    if lang:
        try:
            tr = listing.find_transcript([lang])
        except Exception:
            tr = None
    if tr is None:
        for t in listing:               # first available
            tr = t
            break
    if tr is None:
        raise RuntimeError("no transcripts available")
    if translate:
        try:
            tr = tr.translate(translate)
        except Exception as e:
            raise RuntimeError(f"cannot translate to '{translate}': {e}")
    data = tr.fetch()
    return data.to_raw_data() if hasattr(data, "to_raw_data") else list(data)


# ---- InnerTube engine (same approach as the browser extension) ------------- #
def _innertube_player(video_id, client):
    body = json.dumps({"context": {"client": client}, "videoId": video_id}).encode("utf-8")
    url = f"https://www.youtube.com/youtubei/v1/player?key={INNERTUBE_KEY}&prettyPrint=false"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, method="POST")
    with _urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def _fetch_timedtext_json3(base_url, translate=None):
    url = re.sub(r"([?&])fmt=[^&]*&?", r"\1", base_url).rstrip("?&").replace("?&", "?")
    url += ("&" if "?" in url else "?") + "fmt=json3"
    if translate:
        url += "&tlang=" + urllib.parse.quote(translate)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _urlopen(req) as r:
        return r.read().decode("utf-8", "replace")


def parse_json3(text):
    data = json.loads(text)
    out = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        txt = clean("".join(s.get("utf8", "") for s in segs))
        if txt:
            out.append({"text": txt, "start": ev.get("tStartMs", 0) / 1000,
                        "duration": ev.get("dDurationMs", 0) / 1000})
    return out


def innertube_fetch(video_id, lang=None, translate=None):
    """Non-web InnerTube client → caption URL that isn't PoToken-gated → json3."""
    clients = [
        {"clientName": "ANDROID", "clientVersion": "20.10.38", "androidSdkVersion": 30, "hl": "en"},
        {"clientName": "IOS", "clientVersion": "20.10.4", "hl": "en"},
    ]
    last = "innertube failed"
    for client in clients:
        try:
            pr = _innertube_player(video_id, client)
        except Exception as e:
            last = f"{client['clientName']}: {e}"
            continue
        ct = ((pr.get("captions") or {}).get("playerCaptionsTracklistRenderer") or {}).get("captionTracks") or []
        if not ct:
            last = f"{client['clientName']}: no caption tracks"
            continue
        track = (next((t for t in ct if t.get("languageCode") == lang), None) if lang else None) or ct[0]
        try:
            text = _fetch_timedtext_json3(track["baseUrl"], translate)
        except Exception as e:
            last = f"{client['clientName']}: {e}"
            continue
        if text and text.lstrip().startswith("{"):
            snips = parse_json3(text)
            if snips:
                return snips
        last = f"{client['clientName']}: empty/invalid caption data"
    raise RuntimeError(last)


def fetch_snippets(video_id, lang=None, translate=None):
    # Primary: InnerTube (matches the extension; supports translation reliably).
    try:
        return innertube_fetch(video_id, lang, translate)
    except Exception as primary:
        try:
            return _yta_fetch(video_id, lang, translate)   # fallback
        except Exception as fallback:
            raise RuntimeError(f"{primary}  |  fallback: {fallback}")


# --------------------------------------------------------------------------- #
# AI summary (Google Gemini, standard-library HTTP only)
# --------------------------------------------------------------------------- #
AI_PROMPTS = {
    "summary": 'Write a tight 2-3 sentence overview, then a "Key points" list of 5-8 Markdown bullets.',
    "bullets": "Produce a clean bullet outline of everything covered, grouped under short Markdown headings.",
    "chapters": 'Infer logical chapters. Output a Markdown list of "[mm:ss] Chapter title" using the timestamps present.',
    "takeaways": "Extract concrete action items, takeaways and any tools/links mentioned, as a Markdown checklist.",
}


def ai_summarize(snips, title, mode, key, model):
    use_ts = mode == "chapters"
    transcript = (to_timestamped(snips) if use_ts else to_txt(snips))[:120000]
    prompt = (f'You are summarizing the transcript of the YouTube video "{title}".\n'
              f"{AI_PROMPTS[mode]}\n\nTranscript:\n{transcript}")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with _urlopen(req, timeout=120, tries=2) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        raise RuntimeError(f"Gemini API error: {msg}")
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    out = "".join(p.get("text", "") for p in parts).strip()
    if not out:
        raise RuntimeError("Gemini returned an empty response")
    return out


# --------------------------------------------------------------------------- #
# One video
# --------------------------------------------------------------------------- #
def process(raw, args, ai_key):
    video_id = extract_video_id(raw)
    print(f"\n> {video_id}")

    if args.list:
        for code, name, kind in list_languages(video_id):
            print(f"  {code:<8} {name} ({kind})")
        return

    snips = fetch_snippets(video_id, args.lang, args.translate)
    if not snips:
        print("  ! transcript was empty")
        return
    if args.clean:
        snips = strip_sound_cues(snips)
    if args.paragraphs:
        snips = merge_paragraphs(snips)

    st = stats(snips)
    print(f"  {st['lines']} lines · {st['words']} words · {st['duration']} · ~{st['read_min']} min read")

    content = render(args.format, snips, video_id)

    if not args.no_copy and pyperclip and not args.batch_multi:
        try:
            pyperclip.copy(content)
            print("  - copied to clipboard")
        except Exception:
            pass

    if not args.no_save:
        out_dir = os.path.abspath(args.out)
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(out_dir, f"{video_id}_{stamp}.{EXTS[args.format]}")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  - saved {path}")

    # AI summary
    if args.ai:
        if not ai_key:
            print("  ! --ai needs a key: pass --gemini-key or set GEMINI_API_KEY")
        else:
            print(f"  ... summarizing with {args.ai_model} ({args.ai}) ...")
            try:
                summary = ai_summarize(snips, video_id, args.ai, ai_key, args.ai_model)
                print("\n----- AI summary -----\n" + summary + "\n----------------------")
                if not args.no_save:
                    sp = os.path.join(os.path.abspath(args.out), f"{video_id}_{stamp}_summary.md")
                    with open(sp, "w", encoding="utf-8") as fh:
                        fh.write(f"# {video_id} — Summary\n\n{summary}\n")
                    print(f"  - saved {sp}")
            except Exception as e:
                print(f"  ! {e}")

    if args.no_save:
        print("\n" + content if args.batch_multi is False else "")


# --------------------------------------------------------------------------- #
# Interactive wizard (used when run with no video, e.g. double-clicking ytt.bat)
# --------------------------------------------------------------------------- #
def _ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    return input(f"{prompt}{suffix}: ").strip() or default


def _ask_choice(prompt, choices, default):
    while True:
        v = _ask(f"{prompt} ({'/'.join(choices)})", default)
        if v in choices:
            return v
        print(f"   please choose one of: {', '.join(choices)}")


def _ask_bool(prompt, default=False):
    return _ask(f"{prompt} (y/n)", "y" if default else "n").lower().startswith("y")


def wizard(args):
    """Ask for every option, in order, each with a sensible default."""
    print("YouTube Transcript Fetcher — interactive mode")
    print("(press Enter to accept the [default])\n")

    url = ""
    while not url:
        url = _ask("1. YouTube URL or video ID")

    args.format = _ask_choice("2. Output format", list(FORMATTERS), args.format)
    args.lang = _ask("3. Caption language code (blank = auto / first available)", args.lang or "") or None
    args.translate = _ask("4. Translate to language code (blank = no translation)", args.translate or "") or None
    args.clean = _ask_bool("5. Remove [Music]/[Applause] sound cues?", args.clean)
    args.paragraphs = _ask_bool("6. Merge into readable paragraphs?", args.paragraphs)

    if _ask_bool("7. Save to a file?", not args.no_save):
        args.no_save = False
        args.out = _ask("   Save into which folder?", args.out)
    else:
        args.no_save = True

    ai = _ask_choice("8. AI summary?", ["none"] + list(AI_PROMPTS), args.ai or "none")
    args.ai = None if ai == "none" else ai
    if args.ai and not (args.gemini_key or os.environ.get("GEMINI_API_KEY")):
        args.gemini_key = _ask("   Gemini API key (blank = skip AI)", "") or None
        if not args.gemini_key:
            args.ai = None
    print()
    return [url]


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(
        description="Fetch YouTube transcripts from the command line (Transcript Studio CLI).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("video", nargs="*", help="one or more YouTube URLs or 11-char IDs")
    p.add_argument("--batch-file", help="read URLs/IDs from a file (one per line)")
    p.add_argument("--lang", "-l", help="preferred caption language code, e.g. en, es, hi")
    p.add_argument("--translate", "-t", help="translate the transcript to this language code")
    p.add_argument("--format", "-f", choices=FORMATTERS, default="txt",
                   help="output format: txt (default), time, srt, vtt, md, csv, json")
    p.add_argument("--clean", action="store_true", help="strip [Music]/[Applause]/♪ sound cues")
    p.add_argument("--paragraphs", "-p", action="store_true", help="merge fragments into readable paragraphs")
    p.add_argument("--out", "-o", default=".", help="folder to save into (default: current folder)")
    p.add_argument("--list", action="store_true", help="list available caption languages and exit")
    p.add_argument("--no-save", action="store_true", help="print only, do not write a file")
    p.add_argument("--no-copy", action="store_true", help="do not copy to the clipboard")
    p.add_argument("--ai", choices=list(AI_PROMPTS), help="generate an AI summary of this kind")
    p.add_argument("--ai-model", default=DEFAULT_AI_MODEL, help=f"Gemini model (default: {DEFAULT_AI_MODEL})")
    p.add_argument("--gemini-key", help="Google Gemini API key (or set GEMINI_API_KEY)")
    p.add_argument("--interactive", "-i", action="store_true", help="ask for every option step by step")
    args = p.parse_args()

    targets = list(args.video)
    if args.batch_file:
        try:
            with open(args.batch_file, encoding="utf-8") as fh:
                targets += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
        except OSError as e:
            sys.exit(f"Could not read --batch-file: {e}")

    # No video given (e.g. double-clicked ytt.bat), or asked for it: run the wizard.
    if (args.interactive or not targets) and not args.batch_file:
        if sys.stdin.isatty():
            targets = wizard(args)
        elif not targets:
            one = input("Enter YouTube URL or video ID: ").strip()
            if not one:
                sys.exit("No video provided.")
            targets = [one]

    args.batch_multi = len(targets) > 1
    ai_key = args.gemini_key or os.environ.get("GEMINI_API_KEY", "")

    ok = 0
    for raw in targets:
        try:
            process(raw, args, ai_key)
            ok += 1
        except ValueError as e:
            print(f"  ! {e}")
        except Exception as e:
            print(f"  ! failed: {e}")

    if args.batch_multi:
        print(f"\nDone: {ok}/{len(targets)} succeeded.")


if __name__ == "__main__":
    main()
