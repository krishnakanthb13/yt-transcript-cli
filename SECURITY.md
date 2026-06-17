# Security Policy

**`ytt`** is a local command-line tool. It runs on your machine, talks only to
YouTube (to fetch captions) and — if you opt in — to Google's Gemini API with
your own key. It has no backend and collects no data.

## Supported Versions

| Version | Supported |
| --- | :---: |
| 1.x (latest) | :white_check_mark: |
| < 1.x | :x: |

## Reporting a Vulnerability

Please report security issues **privately** — do not open a public issue for an
unfixed vulnerability.

- **Preferred:** [GitHub private security advisory](https://github.com/krishnakanthb13/yt-transcript-cli/security/advisories/new)
  (Security → *Report a vulnerability*).
- **Email:** partythoninc@gmail.com — put `SECURITY` in the subject.

Please include the affected version, steps to reproduce or a proof of concept,
and the impact you believe it has.

**What to expect:** acknowledgement within **5 business days**; a status update
(accepted / declined) within **14 days**; accepted issues fixed on `main` as soon
as practical, with credit if you'd like. There is **no bug bounty**, but genuine
reports are appreciated. 🙏

## Scope & notes

- Your **Gemini API key** is read from `--gemini-key` or the `GEMINI_API_KEY`
  environment variable and sent only to Google's API; it is never stored or
  transmitted elsewhere by this tool.
- Out of scope: vulnerabilities in `youtube-transcript-api`, YouTube, Google, or
  Python itself; social engineering; issues requiring a compromised device.
