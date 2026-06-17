# Contributing

Thanks for your interest in **`ytt`** (YouTube Transcript CLI)! Issues and pull
requests are welcome.

## Development

```bash
git clone https://github.com/krishnakanthb13/yt-transcript-cli
cd yt-transcript-cli
pip install -r requirements.txt
python ytt.py --help
```

The tool is a single file, `ytt.py` (Python 3.8+, standard library plus
`youtube-transcript-api`; `pyperclip` optional for clipboard). The pure helpers
(`extract_video_id`, formatters, `strip_sound_cues`, `merge_paragraphs`,
`parse_json3`) are easy to test in isolation.

CI runs a syntax/AST check on every push and pull request:

```bash
python -c "import ast; ast.parse(open('ytt.py', encoding='utf-8').read())"
```

## Guidelines

- Match the existing style (PEP 8-ish, standard library first).
- Keep behavior **in parity with the [browser extension](https://github.com/krishnakanthb13/yt-transcript-studio)**
  where it makes sense (same formats, same clock/SRT/VTT rules).
- Keep it dependency-light; prefer the standard library.
- Update `README.md` and add a `CHANGELOG.md` entry for user-facing changes.

## Reporting bugs / security

- Bugs / features: open a GitHub issue with the command you ran and the output.
- Security: see [SECURITY.md](SECURITY.md) (please report privately).

By contributing you agree your work is licensed under the [GPLv3 License](LICENSE).
