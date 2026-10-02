# Event, judges, team

## Event: Swans Applied AI Hackathon @ Law-Di-Gras
Rancho Bernardo Inn, San Diego · **Fri Oct 2, 2026** · ~60 builders · $5K prize pool

| Time | What |
|---|---|
| 8:00–8:15 | Check-in (closes 8:15) |
| 8:25 | Kickoff: client brief + supporting docs |
| 9:00–12:00 | Build session 1 |
| 12:00–1:00 | Lunch (eat in shifts, keep building) |
| 1:00–4:00 | Build session 2 |
| **4:00** | **Submissions due. Judges pick the top 7 from submissions alone** |
| 5:00–5:45 | Top 7 pitch (~5 min each) |
| 6:00 | Winners. Top 3 demo on the concert stage at 7:00 |

**Ask at check-in:**
1. Is a starter template / pre-event setup allowed? (Disclose it in the README either way.)
2. What does the submission need: repo, video, live link?
3. Will data be provided, and can we talk to the firm's people during the day?

## Judges: two panels (format from Swans' Lisbon event, hackathon.swans.co)
- **Swans CTO + engineers:** "technical implementation, system design, and whether what you built would
  actually survive contact with a real firm." CTO Martin Kravchenko previously ran product/ops at a PI firm
  (scaled it from 4 to 40+ staff). He cares about speed-to-lead, conversion, clean structured data
  (dropdowns, not free text), and CRMs that stay in sync with case management.
- **PI firm owners / C-suite:** "solves a real problem, communicates clearly, and feels like something
  they'd write a check for."
- **Legal-AI company founders:** they know what EvenUp/Eve/Supio already do.

**What Swans is:** an "in-house AI department" for PI firms. Firms own what Swans builds; it runs on their
existing stack (n8n/Make/Zapier + HubSpot/Salesforce/Clio/Lawmatics/Filevine, LLMs incl. Anthropic).
Swans' homepage says: "We don't build voice AI agents. We build automations…" Its headline metrics are
~65% of admin tasks automated and 40%+ less time on desk.
**Implication:** say *automation that runs inside the tools staff already use*, not *autonomous agent swarm*.

## What wins here
1. One narrow slice of the given problem, working end-to-end, on realistic messy synthetic data
2. Measured before/after framed in contingency-fee terms (see `docs/domain.md` → money levers)
3. *If* the design uses AI: visible handling of uncertainty (confidence, source citations, human review).
   A no-AI or mostly-code design is fine. Never add AI just to have uncertainty to show
4. Output that lands where staff work (a CRM-shaped record, a task, a draft for approval)
5. A one-sentence value line with a number, at the top of the submission
6. A quote from the firm's rep ("I'd use this Monday") beats any chart

## Team and ownership
| | Yash (Claude Max + Codex) | Partner ($20 plan) |
|---|---|---|
| Owns folders | `app/`, `plan/` | `data/`, `eval/`, `pitch/` |
| Work | Pipeline, UI, integrations | Rep interviews, synthetic data, labels, baseline timing, eval script, diagram, deck, video, submission text |
| AI tools | Claude Code (main), Codex for side tasks | Own Claude/ChatGPT; free Gemini key for data generation |

## Timeline (hard checkpoints)
| Time | Checkpoint |
|---|---|
| **9:10** | Kickoff committed (`/kickoff`). No re-litigating |
| ~9:45 | Thin end-to-end path runs with stubs |
| 10:30 | Show the rep the thin path; adjust if they wince |
| **12:00** | One demo case runs for real end-to-end, or cut scope now |
| **2:30** | Feature freeze. Cache real outputs, record the backup video |
| **3:00–4:00** | Submission block (`/submit`), owned by the partner; Yash supports |
| 3:45 | Submit. Check every link in an incognito window |
| 4:00–5:00 | Rehearse the 5-minute pitch twice |
