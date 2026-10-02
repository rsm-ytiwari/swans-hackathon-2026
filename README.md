# Case brief for personal-injury firms

Open any PI matter and know in 90 seconds what it is, what's blocking it and what's wrong with it, with
every line one click from its source. Then give each treating provider an attorney-approved view of only
what they need.

Built at the Swans Applied AI Hackathon, Oct 2, 2026.

## Run it

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env          # then fill in what you have (see "AI provider" below)
```

**Load a case**, either way:

```bash
# A) From a Clio Manage account (read-only). Needs CLIO_CLIENT_ID / CLIO_CLIENT_SECRET in .env.
uv run python -m app.clio.auth                    # one-time browser login
uv run python -m app.ingest --all                 # every open matter (or --matter <id>)
# ...or click "Sync from Clio" on the home page once the app is running.

# B) From a seed file shaped like the Sapini file (no Clio needed)
uv run python -m app.seed_load path/to/case.json --docs path/to/documents/
```

**Start the app** and open http://127.0.0.1:8000. The home page lists every loaded matter and a
**System status** box that says what is connected and, if something is missing (Clio login, AI key, no
data), exactly what to add.

```bash
uv run uvicorn app.web.main:app --port 8000
```

The first time a matter is opened, the AI analysis (bottom line and contradiction check) runs in the
background. The page works straight away and fills in the AI blocks when they're ready. To pre-compute
instead: `uv run python -m app.core.jobs --matter <id>`.

**Tests:** `uv run pytest app/tests`

## AI provider

Any one of these is enough. Set `LLM_PROVIDER` (and optionally `LLM_FALLBACK`) in `.env`:

| Provider | What it needs |
|---|---|
| `gemini` | `GEMINI_API_KEY` (free at aistudio.google.com), e.g. `GEMINI_MODEL=gemini-3.8-flash` |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `claude_cli` | Claude Code installed and logged in (`claude` on PATH); no key |
| `ollama` | A local Ollama with `OLLAMA_MODEL` pulled |

With no provider, the app still runs: every block computed in code works, and the AI blocks say "AI off".
Every model call is cached in `app/cache/llm/`; `LLM_REPLAY=1` serves only the cache (offline demo).

## How it works

- **Read-only input.** The Clio client refuses any non-GET request (`app/clio/client.py`, tested).
  Our own state (sharing settings, approved links, view counts, AI results) lives in local SQLite.
- **Nothing hardcoded.** The code reads whatever matter is loaded. Firm-specific names (custom field
  names, stage wording) live in `app/core/config.py`. `app/tests/test_no_hardcoding.py` pulls every
  name and value from the loaded case and fails if any of them appear in the code.
- **Code first, AI only where needed.** Dates, deadlines, money totals and rule checks are code
  (`app/core/facts.py`, `app/core/flags.py`). AI writes the 3-sentence bottom line and finds
  contradictions across notes, emails and medical records.
- **AI output is verified.** A contradiction is shown only if both quoted claims are found in the
  cited records; citations to records the model wasn't given are dropped.
- **Providers see only what the attorney approves.** Provider pages render only from an approved
  packet; notes, emails and strategy fields can never enter it (`app/core/sharing.py`, tested with
  every section switched on).

Prepared before the event: the repo skeleton, reference docs (`docs/`), Claude Code configuration
(`.claude/`) and `scripts/check_providers.py`. Everything in `app/` and `plan/` was built during the
event. Decisions and a timestamped build log are in `plan/DECISIONS.md` and `plan/LOG.md`.
