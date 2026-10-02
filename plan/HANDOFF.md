# Handoff · updated 10:01

Overwrite this file at every milestone and before context fills. **Hard cap: 60 lines.** Detail goes in
DECISIONS.md and LOG.md, not here.

## Strategy (as of 10:01)
- One product, two audiences, one Sapini matter read live from Clio (read-only).
- Firm view: understand the case in 90 seconds; what changed since last visit; every fact links to its source.
- Provider view: a filtered slice of the same facts, adjusted per provider, attorney-approved.
- Screening (top 7) is won in the repo: live Clio reads, nothing hardcoded. Winning is won on stage.
- Feature shortlist **not yet decided**; scored on engineering + product value together.

## Done
- Case data inventoried → `brief/sapini-map.md` (strategy items flagged by id, coverage ledger), `brief/slides-inventory.md`
- Clio trial created + connected to Swans seeder (steps 1–2)
- Case materials gitignored (D-005); work logs set up (D-002)

## In progress
- Seeder step 3: create 8 matter stages in Clio UI (human) → steps 4–5 load Sapini
- Clio developer app for our own read access (human) → pipeline spike chat (D-004)
- Asking attorneys Q-1…Q-7

## Next
- 10:20 · feature shortlist + PROPOSED decisions; execution starts
- 12:00 · checkpoint: live Clio data flowing through to the firm view, must-haves working
- 2:30 freeze · 3:30 submit · **4:00 hard close**

## Open questions (answers → LOG.md, then the decision that depends on them)
- Q-1 Coverage: show providers policy limits, a yes/no, or nothing? → D-003 allowlist
- Q-2 Provider status: stage name only, or also offers / estimated time to settle? → D-003 allowlist
- Q-3 Provider delivery: portal login, or an approved emailed update? → D-003 form
- Q-4 Bills: provider sees only their own bill, or total specials across providers? → D-003 allowlist
- Q-5 Firm side: if we nail only one: "what changed", "overdue/next", or source-linked injuries?
- Q-6 Swans: is a "preview as provider" screen OK in the demo, or must it be a separate login?
- Q-7 Main firm user: attorney, case manager, or paralegal?

## Blockers / risks
- Seeder loads 31 docs / 14 expenses; local JSON has 15 / 5 → live Clio wins (D-008); re-check the map after ingest
- Unknown: can a Clio trial account create a developer app? If not, ask Swans immediately

## Pointers
Decisions: `plan/DECISIONS.md` · Log: `plan/LOG.md` · Case data: `brief/sapini-map.md` ·
Slides: `brief/slides-inventory.md` · Rules: `CLAUDE.md`

## Opening prompt for a fresh chat
> Read CLAUDE.md, then plan/HANDOFF.md, then only the DECISIONS.md entries it points to. Don't re-read
> brief/ unless the task needs it. Continue from "Next". Log every action in plan/LOG.md with its D-id,
> record new decisions as PROPOSED in DECISIONS.md, and overwrite HANDOFF.md at each milestone.
