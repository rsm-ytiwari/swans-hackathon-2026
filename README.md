# Case brief for personal-injury firms

Open any PI matter and know in 90 seconds what it is, what's blocking it and what's wrong with it, with
every line one click from its source. Then give each treating provider an attorney-approved view of only
what they need.

Built at the Swans Applied AI Hackathon, Oct 2, 2026.

## The problem

A PI case runs for years. Clio holds everything (notes, emails, calls, tasks, calendar, bills, dozens of
medical-record PDFs), but nobody can digest it. Two people pay for that:

- **The attorney or case manager** has to read everything or ask a colleague to learn what is stalling a
  case and what a defence lawyer will find. Stalled cases and contradictions in the file cost the firm money.
- **The treating provider** treats on a lien, so it is paid only when the case settles. It keeps emailing
  the firm to ask whether the case is still alive and what is needed from it, and must never see the
  firm's notes, strategy or case value.

## What it does (four screens)

| Screen | Route | What it answers |
|---|---|---|
| Matters | `/` | Every case, worst first: stage, days overdue, red flags. Searchable. |
| Case brief | `/m/<matter id>` | Who and what happened; where it stands; the one thing blocking it; the case in 3 lines; what to do next; red flags with the two contradicting quotes side by side; what it's worth against the coverage that can pay. Everything else (changes since you last looked, providers, timeline) opens on demand. |
| Share with a provider | `/m/<id>/share` | The attorney picks a provider, chooses what it may see, checks a live preview (hidden parts shown as "Hidden from provider") and approves a read-only link. |
| Provider page | `/p/<token>` | What the provider sees: is the case active, what the firm needs from its office, its bills and records on file. Phone-friendly. |

Every fact on screen opens the Clio record (note, email, task, field or PDF) it came from.

## Where every value comes from

The rule: **dates, deadlines, money and checks are code; AI is used only for reading free text.**

| On screen | Source | Where |
|---|---|---|
| Days overdue, "waiting on X", the BLOCKED banner, do-next order | Code: task due date minus today; party named in the task | `app/core/facts.py` (`tasks`), `app/web/firm.py` (`_blocker`, `_who`) |
| Stage bar, case age, key dates, last client contact | Code: Clio stage, custom-field dates, first document per folder, latest call/email with the client | `facts.stages`, `facts.milestones`, `facts.last_contact_with` |
| Medical billed, "bills match the specials field", liens | Code: sum of provider charges vs. the Specials custom field | `facts.money`, `facts.providers` |
| Coverage | Code: per-person limit parsed from the Policy Limits field, labelled ASSUMED until an attorney confirms (`config.COVERAGE_ASSUMPTION`) | `facts.reachable_coverage` |
| Rule red flags (specials mismatch, coverage below value, no client contact, treatment gaps, SOL, bills without records) | Code, thresholds in config | `app/core/flags.py` (`rule_flags`), `app/core/config.py` |
| Contradiction red flags | AI reads notes, emails, fields and PDF text. A flag is shown **only if both quotes are found in their cited sources** (fuzzy match); everything else is dropped | `flags.contradiction_flags`, `flags._verified` |
| "The case in 3 lines" and injury chips | AI, from this matter's records only; each line cites record ids, and ids the model wasn't shown are dropped | `app/core/digest.py` |
| Provider status sentence | A fixed plain-English sentence per Clio stage, set once per firm | `config.STAGE_PLAIN` |
| Anything missing in Clio | Said explicitly ("not in Clio", "Not in Clio yet for this matter: Estimated Case Value…") instead of a dash | firm and provider templates |

## How "nothing hardcoded" is guaranteed

- The app reads whatever matter is in the local store (`app/data/clio.db`), filled read-only from Clio or
  from a Clio-shaped JSON file. No case data lives in code.
- Firm-specific names (custom-field names, stage wording, thresholds) live in one file, `app/core/config.py`.
- `app/tests/test_no_hardcoding.py` collects every client, contact, document name, custom-field value and
  note subject from all loaded matters and **fails if any of them appear in `app/` code or templates**.
- **Second case to prove it:** `data/synthetic/okafor-synthetic.json` is a fictional case with a different
  stage, injuries and providers, no documents, several fields left empty on purpose and one planted
  contradiction. Load it with `uv run python -m app.seed_load data/synthetic/okafor-synthetic.json`. The
  brief rebuilds itself, says which fields are missing, and the AI finds the planted contradiction.

## Safety and privacy

- **Read-only Clio.** The client refuses any non-GET request (`app/clio/client.py`, tested). Our own state
  (sharing settings, approved links, view counts) lives in a separate local database.
- **Deny by default for providers.** Provider pages render only from an approved `ProviderPacket`. Notes,
  emails/calls and strategy fields (case value, liability, prior injuries, wage loss) can never enter it,
  whatever the settings say. The server ignores forged settings, allows only this matter's clinical
  documents, runs a firewall check before publishing (refuses with 422 on a breach), and a provider can
  open only the files inside its own packet (`app/core/sharing.py`, `app/web/provider.py`).
- **Human gate.** Nothing is sent automatically: the attorney approves each link and sends it.
- **Demo-safe AI.** Every model call goes through one wrapper (`app/core/llm.py`) with a provider fallback
  chain and a disk cache; `LLM_REPLAY=1` runs fully offline from the cache. AI runs in a background job, so
  a page never waits on a model. With no AI provider, every code-computed block still works and the AI
  blocks say "AI off" with the exact fix.

## Tests

`uv run pytest app/tests` (48 tests):

| File | Proves |
|---|---|
| `test_clio_client.py` | Clio access is GET-only (writes refused before any network call); pagination, 429 back-off, token refresh |
| `test_core.py` | Every provider charge counted once; specials field reconciles or is flagged; overdue tasks are in the past; every timeline event links to a real source; the provider firewall holds for every provider and rejects a leaked note |
| `test_flags.py` | A fabricated AI quote is dropped and a verified one kept; AI off returns no flags (not an error); rule flags link to real sources; overdue and coverage rules on a synthetic matter |
| `test_llm.py` | Cache hit makes no second call; offline replay; schema retry; provider fallback order; usage and cost log |
| `test_seed_load.py` | Loading a case from a JSON file: deterministic ids, missing sections |
| `test_sharing_web.py` | Forged sharing settings ignored; bad links 404; files outside the packet 403; no strategy values on a published page |
| `test_no_hardcoding.py` | No loaded case's data appears anywhere in the code |
| `test_bad_data.py` | A case full of bad data (text in money fields, impossible dates, unknown stage, nameless contacts, tasks without due dates) renders every page, shares and publishes without crashing |

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

# B) From a Clio-shaped JSON file (no Clio needed)
uv run python -m app.seed_load data/synthetic/okafor-synthetic.json
uv run python -m app.seed_load path/to/case.json --docs path/to/documents/
```

**Start the app** and open http://127.0.0.1:8000. The home page lists every matter and a system status
(case data, Clio, AI) that says exactly what to add if something is missing.

```bash
uv run uvicorn app.web.main:app --port 8000
```

Optional: set `APP_PASSWORD` in `.env` to put the firm pages behind a password (any username). Provider
links stay open; their unguessable token is their access control.

The first time a matter is opened, the AI analysis runs in the background; the page works straight away and
fills in the AI blocks when ready. To pre-compute: `uv run python -m app.core.jobs --matter <id>`.

## AI provider

Any one of these is enough. Set `LLM_PROVIDER` (and optionally `LLM_FALLBACK`) in `.env`:

| Provider | What it needs |
|---|---|
| `gemini` | `GEMINI_API_KEY` (free at aistudio.google.com), e.g. `GEMINI_MODEL=gemini-3.8-flash` |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `claude_cli` | Claude Code installed and logged in (`claude` on PATH); no key |
| `ollama` | A local Ollama with `OLLAMA_MODEL` pulled |

## Repo map

```
app/clio/       read-only Clio client + OAuth
app/ingest.py   Clio -> local SQLite (app/data/clio.db, not committed)
app/seed_load.py  Clio-shaped JSON file -> the same tables
app/core/       facts (code-computed), flags (rules + verified AI contradictions), digest (AI 3 lines),
                sharing (provider packet + firewall), llm (one wrapper, cache, fallback), config, jobs, status
app/web/        FastAPI routes (main, firm, provider) + Jinja/Tailwind/HTMX/Alpine templates
app/tests/      48 tests (see above)
data/synthetic/ fictional second case for testing on other data
plan/           decisions (DECISIONS.md), timestamped build log (LOG.md), scope (v1.md), video script
```

## Known limits

- Firm pages have no real login (MOCK: optional shared password only). Provider links are token-based.
- Provider ↔ charge/document matching is by name; review it on a new firm's data.
- A case loaded from a JSON file carries no provider charges (the file format has none); live Clio does.
  The page says "no charges in Clio" rather than hiding it.
- Coverage is the per-person limit, labelled ASSUMED until an attorney confirms that rule.

Prepared before the event: the repo skeleton, reference docs (`docs/`), Claude Code configuration
(`.claude/`) and `scripts/check_providers.py`. Everything in `app/`, `data/` and `plan/` was built during the
event. Decisions and a timestamped build log are in `plan/DECISIONS.md` and `plan/LOG.md`.
