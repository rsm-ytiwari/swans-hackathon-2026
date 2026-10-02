# Execution log

Append-only, newest at the bottom. One line per entry, two at most:
`- HH:MM · <who/chat> · <what was done, with evidence or path> · D-xxx`
Use `D-—` when no decision drove it. Record attorney answers here as `Q-n answered (<who>): …`.

**Size rule:** above ~150 lines, move everything except the last 20 entries to
`plan/archive/LOG-01.md` (then LOG-02…) and leave a pointer line at the top.

---

- 08:30 · team · Kickoff briefing; transcript in `raw.md`, slides in `LDG - 8_30 LDG Hackathon.pdf` · D-—
- 09:20 · main · Problem evaluated: two audiences, one case; screening on code, winning on stage · D-—
- 09:30 · main · Case folder scoped: 15 PDFs, ~640 pp; 512 pp of medical records + bills are scans (no text layer); folders 07 Insurance and 09 Settlement are empty · D-—
- 09:30 · main · Inventory-chat prompt written (slides + case map + coverage ledger) · D-—
- 09:36 · main · Approach reviewed: score features on both lenses in one list; split work by layer, not persona; pipeline spike prompt written · D-003, D-004
- 09:50 · inventory chat · `brief/sapini-map.md` (757 lines, has a COVERAGE LEDGER) and `brief/slides-inventory.md` (497 lines) exist; output not yet reviewed by main · D-—
- 09:50 · ? · `Sapini Case Materials/` added to `.gitignore` · D-005
- 09:50 · main · Workflow files created: `plan/DECISIONS.md`, `plan/LOG.md`, `plan/HANDOFF.md`; CLAUDE.md read-map updated · D-002
- 10:01 · inventory chat · Reported: limits only in custom field F6 + notes (notes conflict); ~26 notes + 4 custom fields flagged as strategy; only 3 charge records, all in scans; OCR of 522 scanned pages done (gitignored); 2 overdue / 4 upcoming tasks; data conflicts listed in `brief/sapini-map.md` · D-003
- 10:01 · Yash · Clio trial created and connected to the Swans seeder (steps 1–2). Step 3 (8 matter stages) not done; 0 matters in account · D-004
- 10:01 · main · **Mismatch found:** seeder v1.13 card shows 31 documents / 14.0 MB / 14 expenses; local JSON + guide say 15 docs / 85 MB / 5 expenses. Notes 42, comms 69, tasks 14, events 17 match. Live Clio is the source of truth; inventory must be re-checked after ingest · D-008
- 10:25 · Yash · Switched to the teammate's Clio account (stages created there, not yet verified). Pipeline-spike chat started. Rule: seeder, developer app and ingest must all use this ONE account · D-004
- 10:28 · Yash · Seeder connected to the teammate's account (Jenith); all 8 stages verified by the seeder; account already shows 1 matter before field creation (unknown, check before ingest). Attorney questions cut from 7 to 3 (Q-1 merged money question, Q-3 delivery, Q-6 Swans auth scope), each with a default · D-003
- 10:25 · ingest chat · Step 1 researched: Clio developer docs tell app developers to use a trial account, so a trial can create a developer app (not yet verified in our account); app is created at app.clio.com/settings/developer_applications; tokens last 30 d, refresh tokens don't expire; 600 req/60 s per token · D-004
- 10:45 · ingest chat · Built `app/clio/{auth,client,fields}.py`, `app/store.py`, `app/ingest.py`, `app/seed_diff.py`; GET-only `ReadOnlySession` guard; `uv run pytest app/tests` → 16 passed; `app/data/` gitignored; CLIO_* added to `.env.example` · D-001, D-004, D-006
- 10:45 · ingest chat · **Blocked:** no CLIO_CLIENT_ID/SECRET in `.env` yet (human creates the developer app); live run + count check + seed diff pending · D-004, D-008
- 10:32 · Yash · Sapini loaded in the teammate's Clio as matter 00001-Sapini (Litigation, opened 05/07/2023); it was the '1 matter' seen earlier. Do NOT press Create New Matter again (would duplicate). Custom fields / docs counts not yet checked · D-004, D-008
- 10:55 · Yash · Clio developer app created at developers.clio.com/apps/new (trial account works); Read-only on Activities, Calendars, Communications, Contacts, Custom fields, Documents, Matters, Tasks, Users; keys in `.env`; OAuth Allow done · D-001, D-004
- 11:05 · ingest chat · Fixes from live run: Clio allows only 1 level of `fields` nesting; Custom fields Read was missing (403, now ticked); `web_sites{primary}` invalid; non-billable expenses have `total`=null, amount in `non_billable_total` (now stored) · D-004
- 11:10 · ingest chat · **Live ingest works:** `uv run python -m app.ingest --matter 1811198093` (00001-Sapini, stage Litigation) → notes 42, comms 69, tasks 14, events 17, docs 31, expenses 14, all = seeder; 47 requests, ~67 s; re-run = 16 requests, 7.5 s, no re-downloads, raw rows unchanged (266); all 31 file sizes = Clio sizes (14.7 MB) · D-004, D-008
- 11:10 · ingest chat · **Seed diff (`app.seed_diff`):** live has 18 NEW docs (9 per-provider medical records + 9 per-provider itemized bills, all WITH text layer); the 2 big scanned bundles (doc-19, doc-20) are NOT in live Clio; 13 shared docs byte-identical. No text layer: photo-id (1 p), summons-complaint (8 p), letter-to-judge (1 p). 9 NEW expenses = "DEMO medical charges" per provider, non-billable, $118,400 total; 5 seed firm costs $1,410. `brief/sapini-map.md` page refs for medical records/bills are now stale · D-008
- 10:49 · main · Restored the 3-question list in HANDOFF (pipeline chat's 11:10 rewrite had reverted it to Q-1…Q-7). Behind schedule: shortlist was due 10:15 · D-007
- 11:03 · main · Quote-traceability check of draft features: 4 gaps found (key-events timeline, last client contact, cache digests instead of re-running AI, provider sees other providers' relevant records). Background design agent launched → plan/ui-spec.md + prototype/{firm,provider}.html (gitignored) for attorney validation · D-003, D-006
- 11:05 · main · Bug fixed: calendar entries (string ids from Clio) were pruned on every re-ingest; `app/store.py` prune compares as text; re-ingest twice → 17 entries, 283 records stable · D-004
- 11:16 · main · Stack switched from Streamlit to FastAPI + Jinja + Tailwind/HTMX/Alpine, assets vendored in `app/web/static/` · D-009
- 11:16 · main · Shared core built: `app/core/{config,facts,sharing}.py`; provider bills sum $118,400 = Medical Specials field; firewall tests incl. all-sections-on; 24 tests pass · D-003, D-006
- 11:16 · main · App shell + thin views: `/m/<id>` firm, `/m/<id>/share` console, preview, approve → `/p/<token>`, view receipts; provider doc fetch outside packet → 403 (curl-verified) · D-003, D-010
- 11:18 · main · D-009, D-010 accepted; D-011 feature set proposed; `plan/tasks.md` created; CLAUDE.md ownership + stack updated; `.gitattributes` union-merges LOG.md · D-010
- 11:20 · design agent · plan/ui-spec.md (180 lines) + prototype/{firm,provider}.html built from clio.db by prototype/build.py; new red flag found: SportsCare PT chart shows a discharge 09/14/2023 (p.12) vs 'never discharged' in the case file · D-011
- 11:36 · critique agent · plan/ui-critique.md: firm prototype first screen = 638 words / 42 chips / 11 dollar figures (overloaded, story assembled by hand); live firm page looks like Clio re-skinned; sharing console = 60 checkboxes. Proposed budget: 5 blocks, ~180 words, 'Bottom line' block. 10 vs 9 providers = Dr. Capiola listed as his own provider (individual clinician, no bills) · D-011
- 11:43 · main · plan/v1.md drafted (promise, 6-beat video script, V1 scope, cuts, no-hardcoding guarantees, owners, judge questions); awaiting Yash yes → D-011. Guard test app/tests/test_no_hardcoding.py: 101 case strings derived from the DB, 24 files scanned, passes; planted 'client name' probe correctly fails it · D-011
- 11:44 · implementer · T9 LLM wrapper app/core/llm.py + tests: pytest app/tests 33 passed offline; smoke: ollama gemma4:26b ok 13.3s then cached 0.00s; gemini 503 from Google (key accepted, 404 on bad model id); anthropic untested (no key in .env) · D-009
