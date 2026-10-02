# Decisions

The contract for what we build. Newest at the bottom. Status: PROPOSED (awaiting a human "yes"),
ACCEPTED, SUPERSEDED by D-xxx, REVERSED.

**Trace a decision:** `grep -n "D-003" plan/*.md` shows every log entry and dependent decision.
**Reversing one:** set status to REVERSED, then walk its "Downstream" list and any decision that lists
it under "Depends on". Log the reversal in LOG.md.
**Size rule:** above ~400 lines, move SUPERSEDED/REVERSED entries to `plan/archive/DECISIONS-01.md`
and leave a one-line stub here (`D-004 → archived, REVERSED`).

Template:
```
## D-0xx · <title> · <STATUS> · <HH:MM>
- **Decided:** what, in one or two lines
- **Why:** the reason
- **Rejected:** alternative (why not)
- **Depends on:** assumptions, Q-ids, other D-ids
- **Downstream:** files, tasks, decisions that rely on this
```

---

## D-001 · Clio is read-only input · ACCEPTED · 09:50
- **Decided:** Our code only reads from Clio. The HTTP client refuses any non-GET request in code, with a
  test proving it. Anything we store (digests, sharing settings, read receipts) goes in our own SQLite.
- **Why:** Event rule 3 ("read everything, write nothing"). A guard in code is visible proof for the
  repo screen.
- **Rejected:** Storing summaries or provider settings in Clio custom fields (breaks the rule).
- **Depends on:** Event rules (slide 16).
- **Downstream:** `app/` Clio client, ingest, our database schema; D-003.

## D-002 · Work logs live in plan/ · ACCEPTED · 09:50
- **Decided:** `plan/DECISIONS.md`, `plan/LOG.md`, `plan/HANDOFF.md` are the shared memory. Chats are
  disposable.
- **Why:** User request. Lets any chat be cleared or replaced without losing state.
- **Rejected:** Keeping state in chat history (lost on /clear).
- **Depends on:** none.
- **Downstream:** CLAUDE.md read-map; every chat's opening prompt.

## D-003 · One pipeline, one fact store, two views · ACCEPTED (built) · 09:50
- **Decided:** A single ingest and digestion pipeline produces one set of facts, each citing its source.
  The firm view shows everything. The provider view is a filtered slice: nothing shows unless it's on an
  allowlist the attorney can change per provider, and the attorney approves before anything is shared.
- **Why:** Both audiences need the same facts. Building extraction twice risks the two sides
  disagreeing on facts and doubles the work. Notes are full of strategy (e.g. N5–N7, N9 F9 rationale),
  so blocking by default is the safe direction.
- **Rejected:** Separate chats or pipelines per persona (duplication); provider view built by
  removing fields from the firm view (one forgotten field leaks strategy).
- **Depends on:** Q-1, Q-2, Q-4 change the *allowlist contents*, not this structure. Q-3 changes
  the provider view's *form* (portal vs approved digest).
- **Downstream:** schema of the fact store; both views; sharing controls.

## D-004 · Pipeline spike starts before the feature shortlist · ACCEPTED (built) · 09:50
- **Decided:** Build the read-only Clio ingest (all entities + document downloads → SQLite, keyed by Clio
  ids) in parallel with feature planning.
- **Why:** It's needed whatever features we pick, and Clio OAuth is the biggest unknown on the critical
  path.
- **Rejected:** Finishing planning first (wastes about 30 min of build time).
- **Depends on:** Clio account + Sapini loaded + developer app created (see HANDOFF blockers).
- **Downstream:** `app/ingest`, `app/clio_client`; D-006.

## D-005 · Case materials never committed · ACCEPTED · 09:50
- **Decided:** `Sapini Case Materials/` is gitignored (done). The app reads only from Clio; local files are
  for our understanding only.
- **Why:** 85 MB of a real case file; Swans reads the repo; a local copy invites "hardcoded" suspicion.
- **Rejected:** Committing it as test fixtures.
- **Depends on:** none.
- **Downstream:** `.gitignore`; any test fixtures must be synthetic.

## D-006 · Every displayed fact carries its source · ACCEPTED (built) · 09:50
- **Decided:** Every extracted fact stores (Clio record type, Clio id, and document page where relevant)
  and the UI links to it.
- **Why:** Attorney quotes "If a date is on screen, I need to see where it came from" and "click… open
  the note"; trust is the AI judges' first test.
- **Rejected:** Free-text AI summaries without citations.
- **Depends on:** D-004 storing Clio ids.
- **Downstream:** fact store schema; every UI card.

## D-007 · Timeline · PROPOSED · 09:50
- **Decided:** Planning done by 10:15 · checkpoint 12:00 (live Clio data showing in the firm view) ·
  feature freeze 2:30 · video + README 2:30–3:15 · submit 3:30 · hard close 4:00.
- **Why:** Submission order is presentation order; the form takes about 10 min.
- **Rejected:** Submitting at 3:55 (no buffer).
- **Depends on:** none.
- **Downstream:** HANDOFF milestones.

## D-008 · Live Clio is the source of truth; local seed files are reference only · ACCEPTED (built) · 10:01
- **Decided:** Ingest counts and contents are checked against what the seeder loads into Clio, not
  against `sapini-clio-data.json`. After the first ingest, diff live data against `brief/sapini-map.md`
  and record the new documents and expenses.
- **Why:** The seeder (v1.13) loads 31 docs / 14 MB / 14 expenses vs 15 docs / 85 MB / 5 expenses in
  the local JSON. Page indexes and bill findings in the map may not match the live documents.
- **Rejected:** Treating the local JSON as ground truth (screening runs on what's in Clio).
- **Depends on:** D-004 ingest working.
- **Downstream:** ingest done-criteria; `brief/sapini-map.md` (needs a live-data addendum); any
  extraction tuned on local PDFs.

## D-009 · Stack: FastAPI + Jinja + Tailwind + HTMX + Alpine, no build step · ACCEPTED · 11:16
- **Decided:** One Python process (`uv run uvicorn app.web.main:app --reload --port 8000`). Server-rendered
  Jinja templates; Tailwind, HTMX and Alpine served from `app/web/static/` so the demo works offline.
- **Why:** Streamlit is too basic for a product judged on its display (user call). Neither of us knows a
  JS framework; this keeps one language for logic, no npm, and the design agent's HTML lifts straight in.
- **Rejected:** Streamlit (layout limits); React/Next (setup cost, two toolchains, nobody fluent).
- **Depends on:** none.
- **Downstream:** `app/web/**`; `plan/ui-spec.md` component kit = Jinja macros in `components/ui.html`.

## D-010 · Way of working: split by view on one shared core · ACCEPTED · 11:16
- **Decided:** `app/core/` (facts, sharing, config) and `app/web/{main,deps}.py`, `base.html`,
  `components/ui.html` are shared, owned by Yash; change them only by asking. Yash owns the firm view
  (`app/web/firm.py`, `templates/firm/`). Jenith owns the provider view + sharing console
  (`app/web/provider.py`, `templates/provider/`). Provider-facing pages render only a `ProviderPacket`.
  Pull --rebase before every push; joint 2-minute run every 45 min. Only Yash edits DECISIONS/HANDOFF;
  LOG.md is union-merged (`.gitattributes`).
- **Why:** Vertical slices give two demo-able halves early; one core keeps facts consistent (D-003).
- **Rejected:** Backend/frontend split (late integration, drift); separate chats per persona generating
  separate feature lists.
- **Depends on:** D-003, D-009.
- **Downstream:** CLAUDE.md ownership rule, `plan/tasks.md`.

## D-011 · Feature set · PROPOSED · 11:16 (lock after mockup validation with an attorney)
- **Decided (draft):** Must: F1 snapshot, F2 overdue/upcoming/waiting + last client contact, F3 money,
  F4 click-to-source, P1 provider page, P2 sharing controls + preview + approve, P3 firewall.
  Should: F5 changes since last look, F6 injuries/treatment per provider from records (AI, page cites),
  key-events timeline (AI ranks), E1 cached AI digests, P4 "case moved" update drafted for approval,
  P6 attorney shares selected clinical records with a provider. Could: F7 red flags, P5 read receipts.
  Won't: chat box, attendance tracking.
- **Why:** Every slide-9 quote traced to a block (ui-spec §f); fewer things done well (slide 9).
- **Rejected:** Building all 12+ at once.
- **Depends on:** Q-1 (coverage default), Q-3 (link vs pushed update), Q-6 (login needed?), mockup feedback.
- **Downstream:** `plan/tasks.md` rows; both views.
