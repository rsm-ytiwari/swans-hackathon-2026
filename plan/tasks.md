# Tasks

One row per task. Edit only your own rows (owner column). Status: todo · doing · done · cut.
Done means you ran it and saw it work (CLAUDE.md rule 4). Feature ids from D-011.

| # | Task | Owner | Files | Status | Done when |
|---|---|---|---|---|---|
| T1 | Shared core: facts, sharing/firewall, config | Yash | `app/core/` | done | 24 tests pass; routes 200 (LOG 11:16) |
| T2 | App shell, source dialog, component kit v0 | Yash | `app/web/main.py`, `deps.py`, `templates/base.html`, `components/ui.html` | done | firm, share, preview, publish, /p link all work |
| T3 | Jenith setup: pull, .env, auth, ingest, tests, run app | Jenith | — | todo | counts 42/69/14/17/31/14; app opens on :8000 |
| T4 | UI spec + mockups for validation | design agent | `plan/ui-spec.md`, `prototype/` | doing | files exist; shown to 1 attorney + 1 Swans engineer |
| T5 | Ask Q-1, Q-3, Q-6; log answers | Yash/Jenith | `plan/LOG.md` | todo | answers logged |
| T6 | F1–F4 firm view to ui-spec (90-second layer) | Yash | `app/web/firm.py`, `templates/firm/` | todo | first screen answers who/what/injuries/next with sources |
| T7 | P1 provider page to ui-spec | Jenith | `templates/provider/page.html` | todo | preview + /p link render cleanly for every provider |
| T8 | P2 console: per-provider toggles, preview, approve, sent/viewed | Jenith | `app/web/provider.py`, `templates/provider/console.html` | todo | toggle → preview → approve → link → view counted |
| T9 | LLM wrapper with cache + replay (rule 5), cost per case | Yash | `app/core/llm.py` | todo | second run makes 0 model calls |
| T10 | F6 injuries/treatment per provider from records PDFs (page cites) | Yash | `app/core/digest.py` | todo | each injury links to doc + page |
| T11 | Key-events timeline + F5 changes since last look | Yash | `app/core/digest.py`, firm view | todo | pick a date → only later events, ranked |
| T12 | P4 "case moved" update drafted for approval | Jenith | provider | todo | draft shown in console, sent only after approve |
| T13 | 90-second test (fresh person, our app vs Clio) | Jenith | `eval/` | todo | scores recorded, no invented numbers |
| T14 | Video (90 s), README, submission form | both | `README.md` | todo | submitted by 3:30 |
