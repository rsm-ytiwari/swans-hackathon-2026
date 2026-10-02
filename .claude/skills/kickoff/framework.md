# Kickoff framework: reference for /kickoff

Borrowed frameworks, compressed:
- Lean **value stream mapping** (touch vs wait time) → diagnose
- Contingency-fee **unit economics** → money
- **Opportunity solution tree** (outcome → opportunity → solution) → shapes
- **Kill rules** instead of weighted scoring → choose
- **Tracer bullet** (thin end-to-end first) → build
- **SCQA** (Minto) → pitch

Revised after an independent review: lighter, propose-before-tools, submission-first.

## G0: Questions for the firm's rep (in priority order)
1. Who does this today, and how many of them? (role, headcount, caseload)
2. How often and how long? (volume per week, minutes per unit, wait time)
3. What happens when it goes wrong, and what does that cost?
4. Where does the output go? (Clio / Filevine / Lawmatics / HubSpot / email / spreadsheet)
5. What have you tried, or which vendor do you use now?
6. *(Ask the organizers)* What data or examples did you give us? Can we come back to show you a draft at ~10:30?

**Detailed brief:** verify their process and don't drift from it. Judges check requirement adherence.
**Vague brief:** write explicit assumptions and confirm 3 with the rep. Pick the slice that wins even if you're off by 2×.

## Money framing
See `docs/domain.md` → money levers (6 of them, including client experience).
- **Preferred framing:** capacity ("same team, +25% cases") or cycle time ("demand 30 days sooner").
- **Hours saved:** valid when tied to burnout or turnover, or when the hours sit on the critical path.

## Kill rules (choose step)
A candidate is out if any of these is true:
- it can't be built end-to-end in ~5 h
- it can't be demoed in 2 min
- the rep didn't confirm the pain
- it's a weaker copy of a funded incumbent

Among survivors: prefer the one that produces an **action** (task, follow-up, flag in the CRM) over a summary.

## Positioning sentence (pick the one that's true; from memory, ≤ 2 min of search)
- **Different layer:** "They draft the demand; we make the file demand-ready 40 days sooner."
- **Firm-owned / cheaper:** "Runs in the firm's own stack for ~$0.0X per case, no per-demand SaaS fee." (Swans' model)
- **Better:** a quality claim your eval shows.
- **Faster:** only if it maps to capacity or cycle time.

## `plan/process.yaml` schema (fill after committing; drives the diagram and the numbers)
```yaml
problem: "..."
brief_type: detailed | vague
assumptions: ["ASSUMED: 60 cases per case manager", "..."]
money_levers: [2, 3]
as_is:
  - {id: s1, actor: case_manager, action: "Request records", touch_min: 15, wait_days: 45,
     failure: "No follow-up", failure_cost: "Demand delayed ~30 days", leak: true}
to_be:
  - {id: t1, replaces: [s1], lane: our_system, node_type: W, tool: "timer + email (mock fax)",
     why_not_code: null, human_gate: false, on_failure: "Escalate to case manager after 14 days",
     before_min: 15, after_min: 1}
metrics: {baseline_min: null, after_min: null, accuracy: null, n_cases: null,
          escalation_rate: null, cost_per_case_usd: null}
```

## Build discipline
- **~9:45:** tracer bullet. Input → every step stubbed → output on screen.
- **10:30:** show the rep. Adjust if they wince.
- **12:00:** one demo case runs for real, or cut scope.
- **2:30:** freeze. Cache real outputs to `app/cache/`, record the backup video.
- **3:00–4:00:** `/submit`.

## Pitch (SCQA, 5 min)
| Time | Part | Content |
|---|---|---|
| 0:20 | Situation | "A case manager at a firm like yours carries ~80 files…" |
| 0:20 | Complication | The leak, in $ or days |
| 0:05 | Question | "What if every file flagged its own gaps the day they formed?" |
| 3:00 | Answer | Live demo of the demo case → diagram + numbers slide |
| 1:00 | Close | Limits, human gates, compliance line, what it plugs into (their CRM / n8n), the rep's quote |
