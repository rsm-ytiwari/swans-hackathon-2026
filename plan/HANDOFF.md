# Handoff · updated 11:10

Overwrite this file at every milestone and before context fills. **Hard cap: 60 lines.** Detail goes in
DECISIONS.md and LOG.md, not here.

## Strategy (as of 10:01)
- One product, two audiences, one Sapini matter read live from Clio (read-only).
- Firm view: understand the case in 90 seconds; what changed since last visit; every fact links to its source.
- Provider view: a filtered slice of the same facts, adjusted per provider, attorney-approved.
- Screening (top 7) is won in the repo: live Clio reads, nothing hardcoded. Winning is won on stage.
- Feature shortlist **not yet decided**; scored on engineering + product value together.

## Done
- Case data inventoried → `brief/sapini-map.md`, `brief/slides-inventory.md`
- **Live Clio ingest working (D-004):** `uv run python -m app.ingest --matter 1811198093` → `app/data/clio.db`
  (gitignored) + files in `app/data/files/`. Counts = seeder (42/69/14/17/31/14). Idempotent. 16 tests pass
  (`uv run pytest app/tests`), incl. GET-only guard (D-001). Every row keeps clio_type + clio_id (D-006).
- Seed diff: `uv run python -m app.seed_diff --matter 1811198093` (results in LOG 11:10)

## Key data facts (live Clio, D-008)
- Medical records + bills are now **18 per-provider PDFs with text layers**; no OCR needed for them.
- The two scanned bundles from the local seed are not in Clio. Only 3 small docs lack a text layer.
- 9 provider charges are ExpenseEntry, non-billable, amount in `non_billable_total` ($118,400); 5 firm costs ($1,410).
- `brief/sapini-map.md` page refs for records/bills are stale (partner/inventory chat to refresh).

## In progress
- Asking attorneys Q-1, Q-3, Q-6
- Feature shortlist + PROPOSED decisions

## Next
- Pick features; build on `app/data/clio.db` (tables: matters, notes, communications, tasks,
  calendar_entries, activities, documents, contacts, relationships, custom_field_values, …; `raw` has full JSON)
- 12:00 · checkpoint: live Clio data flowing through to the firm view, must-haves working
- 2:30 freeze · 3:30 submit · **4:00 hard close**

## Open questions (answers → LOG.md, then the decision that depends on them)
Ask these three. Default in [brackets] is what we build if there's no answer.
- Q-1 Attorney: "Which money numbers would you let a treating provider see: policy limits, settlement
  offers, other providers' bills, or none?" → D-003 allowlist defaults [own bill + case stage only]
- Q-3 Attorney: "Would you give providers a live link, or approve an update you send each time the case
  moves?" → D-003 provider view form [approval queue that publishes a read-only link]
- Q-6 Swans: "Does the provider view need its own login for the demo, or is 'preview as provider' fine?"
  → scope of auth work [preview-as-provider screen, no separate login]

## Blockers / risks
- Clio token in `app/data/clio_token.json` (30 days, auto-refresh). Re-auth: `uv run python -m app.clio.auth`
- Personal injury scope (damages/medical records/liens endpoints) not granted; not needed so far
- Ingest code not yet committed

## Pointers
Decisions: `plan/DECISIONS.md` · Log: `plan/LOG.md` · Case data: `brief/sapini-map.md` ·
Slides: `brief/slides-inventory.md` · Rules: `CLAUDE.md`

## Opening prompt for a fresh chat
> Read CLAUDE.md, then plan/HANDOFF.md, then only the DECISIONS.md entries it points to. Don't re-read
> brief/ unless the task needs it. Continue from "Next". Log every action in plan/LOG.md with its D-id,
> record new decisions as PROPOSED in DECISIONS.md, and overwrite HANDOFF.md at each milestone.
