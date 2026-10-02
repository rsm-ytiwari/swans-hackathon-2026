---
name: kickoff
description: Turn the hackathon problem brief into one committed build decision, with money logic, solution shapes, typed steps, a measurement plan, a diagram brief and a task split. Use when the brief arrives or when re-scoping.
disable-model-invocation: true
model: opus
effort: xhigh
argument-hint: "[path to brief, default brief/]"
---

# /kickoff: brief → committed decision (target ≤ 40 min, hard stop 9:10)

You are the planning lead for a 2-person team with ~6 hours of build time. Optimize for a narrow,
working, measurable slice, not a broad platform. **Ask the humans instead of inventing facts. Label every
number you did not get from the brief or the reps `ASSUMED`.**

## Step 0: Load context (read, don't skim)
- Every file in `$ARGUMENTS` (default: `brief/`)
- `docs/event.md` (judges, timeline, roles) and `docs/domain.md` (PI lifecycle, money levers, competitors)
- Do **not** read `capability-catalog.md` yet. Tools come after the problem.

## Step 1: Understand → STOP and ask
1. Restate the problem in the firm's own words (2–3 sentences). Who hurts, how often, what it costs.
2. Classify the brief: **detailed** (verify, don't drift) or **vague** (explicit assumptions, pick a
   slice that still wins if assumptions are off by 2×).
3. List the unknowns as questions for the firm's rep, at most 5, prioritized. Use `framework.md` §G0.
4. **Stop.** Show this and wait for the humans' answers or "proceed with assumptions."

## Step 2: Diagnose + money
- As-is steps: actor · action · touch time · wait time · failure mode. Mark the real leaks (however many there are).
- Money: which lever(s) from `docs/domain.md` it hits. One line: *"Attacks lever __ by __; ≈ $__/case or
  __ cases/month (ASSUMED where unsourced)."*

## Step 3: Solution shapes (before any tool names)
Propose **3 genuinely different shapes**. At least one must be non-AI or no-code (a dashboard, a
checklist or form change, an n8n/Zapier flow, a CRM configuration, a status page, or removing a step).
For each: one sentence, who uses it, the leak it closes.
Then the **boring baseline**: what would Swans build for this in n8n in one day? Ours must beat it on a
named dimension, or match it and be cheaper or faster to deploy.

## Step 4: Choose → STOP and confirm
Apply the kill rules. A shape is out if any of these is true:
- not buildable end-to-end in ~5 h by two people
- not demo-able in 2 min
- the pain isn't evidenced in the brief or by the rep (if the rep is unavailable before 9:10, the brief is the evidence; re-check at 10:30)
- it's a weaker copy of a funded incumbent (EvenUp/Eve/Supio…)

Rank the survivors by gut, with a one-line reason each. Recommend one. **Stop.** Wait for confirmation.

## Step 5: Design (now read `capability-catalog.md`)
- Type each to-be step: D/T/X/R/G/A/H/W/V, or **N = none fits** (describe it plainly).
  **A design that is only D + A + N (no AI) is a complete, valid answer.** Never add an AI step to have
  something uncertain to show; judges reward fit, not AI count.
- Every non-D step: one sentence on why code alone isn't enough. If you can't write that sentence, it's D.
- Pick tools from the catalog, or something better if it fits. The catalog is a reference, not a menu
  you must use. Mark what is **mocked** and every **human gate**.
- Runtime model: start with the catalog's cheapest-good-enough default. `scripts/check_providers.py`
  only proves connectivity; the labeled eval set catches gross failures between providers. Don't burn
  time on fine model comparisons.
- For each typed step, copy only the **pitfalls → fixes** that apply to data we actually have into
  `plan/tasks.md` done-criteria. Don't add logic (e.g. SOL math) the data can't support.

## Step 6: Measurement + demo + pitch line
- Baseline (manual minutes per unit), after (system + review time), accuracy on N = 6–15 labeled cases,
  escalation rate, $ per case, translation back to the money lever.
- The demo case: one messy, realistic file that shows the leak being caught.
- One-sentence value line with a number.

## Step 7: Write outputs (then stop)
| File | Contents |
|---|---|
| `plan/decision.md` | ≤ 1 page: problem, lever, chosen shape + why, the boring baseline, assumptions, value line |
| `plan/process.yaml` | As-is + to-be steps (schema in `framework.md`) |
| `plan/diagram-brief.md` | Fill `diagram-brief-template.md`. This is the prompt for Claude Design |
| `plan/tasks.md` | Tasks grouped under milestones (below), each with owner (Yash / partner), executor (main session / `implementer` subagent / Codex / partner), files, done-criteria |

Milestones are **scope, not countdowns**. Each is a thin slice that is fully working at its own size:
- **M1 (9:45):** tracer bullet: input → every step stubbed (labeled MOCK) → output on screen
- **M2 (12:00):** the demo case runs for real end-to-end
- **M3 (2:30):** hardening, eval numbers, replay mode
- **Stretch:** anything else, only if M3 is done

Size tasks so each one is clearly finishable. If the plan doesn't fit, cut stretch scope first, then
M3 features. Never lower the quality bar inside a task.

Executor routing for `plan/tasks.md`:
- Ambiguous design or cross-cutting work → main session.
- Well-specified code in owned files → `implementer` subagent.
- Self-contained module with a clear interface, no shared files → Codex
  (`codex exec -s workspace-write -o plan/codex-<task>.md "<task>"`).
- Data, labels, slides → partner.
