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
