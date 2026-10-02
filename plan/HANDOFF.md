# Handoff · updated 11:18

Overwrite at every milestone and before context fills. **Hard cap: 60 lines.** Only Yash's chats edit this.

## Strategy
- One product, two audiences, one Sapini matter read live from Clio (read-only, D-001).
- Firm view: understand the case in 90 seconds; every fact links to its source (D-006).
- Provider view: deny-by-default slice of the same facts, per provider, attorney previews + approves (D-003).
- Stack: FastAPI + Jinja + Tailwind/HTMX/Alpine, offline-safe (D-009). Split by view on one core (D-010).
- Feature set drafted (D-011, PROPOSED): lock after showing mockups to an attorney.

## Run it
`uv run python -m app.ingest --matter 1811198093` → `uv run uvicorn app.web.main:app --reload --port 8000`
→ http://127.0.0.1:8000 · tests: `uv run pytest app/tests` (24 pass) · `APP_TODAY=2026-10-02` pins dates.

## Done
- Live ingest (D-004); calendar-entry prune bug fixed 11:05 (string ids)
- Shared core `app/core/` (facts, sharing + firewall, config) and app shell; thin firm view, sharing
  console, provider preview, approve → link `/p/<token>`, view receipts, doc access limited to packet

## In progress
- Design agent → `plan/ui-spec.md` + `prototype/{firm,provider}.html` (gitignored) for validation
- Jenith: setup (T3), then T7/T8
- Q-1, Q-3, Q-6 to attorneys / Swans

## Next
- Show mockups to 1 attorney + 1 Swans engineer → lock D-011
- Yash: T6 firm view to spec, T9 LLM wrapper + cache, T10/T11 AI digests
- 12:45 checkpoint: both views on live data in one app · 2:30 freeze · 3:30 submit · **4:00 hard close**

## Open questions (answers → LOG.md, then the decision that depends on them)
Default in [brackets] is what we build if there's no answer.
- Q-1 Attorney: "Which money numbers would you let a treating provider see: policy limits, settlement
  offers, other providers' bills, or none?" → sharing defaults [own bill + case stage only]
- Q-3 Attorney: "Would you give providers a live link, or approve an update you send each time the case
  moves?" → provider view form [approval → read-only link]
- Q-6 Swans: "Does the provider view need its own login for the demo, or is 'preview as provider' fine?"
  → auth scope [no login; link token only]

## Risks
- Provider ↔ document/charge matching is name-based (`app/core/facts.py`); verify on any new data
- Seeded tasks show completed_at = today (seeder artifact); don't present it as history
- Firm routes have no login (MOCK, labeled in code)

## Pointers
Decisions `plan/DECISIONS.md` · Tasks `plan/tasks.md` · Log `plan/LOG.md` · Case data `brief/sapini-map.md`
(record/bill page refs stale, D-008) · Slides `brief/slides-inventory.md` · Rules `CLAUDE.md`

## Opening prompt for a fresh chat
> Read CLAUDE.md, then plan/HANDOFF.md, plan/tasks.md (your rows), and only the DECISIONS.md entries
> cited. Don't re-read brief/ unless needed. Continue from "Next". Log every action in plan/LOG.md with
> its D-id; propose new decisions to Yash; edit only files you own (CLAUDE.md rule 7).
