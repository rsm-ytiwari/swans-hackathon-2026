---
name: submit
description: Package the hackathon submission (README value line, numbers table, video script, screenshots checklist, link check). Use at 3:00pm or when asked to prepare the submission.
disable-model-invocation: true
model: sonnet
effort: medium
---

# /submit: the 4pm submission is the first filter (judges pick the top 7 from it)

Read `plan/decision.md`, `plan/process.yaml`, `eval/` results, and `app/` (to describe how to run it).
Never invent a number. If a metric is missing, write `TBD` and tell the humans.

## 1. Rewrite `README.md` in this order
1. **Value line** (one sentence with a number), e.g. "Catches treatment gaps in 3 days instead of ~60, so
   the same case manager carries 25% more files; 92% field accuracy on 12 synthetic cases."
2. **The problem** in the firm's words (3 lines) + which money lever it hits.
3. **Demo**: video link, then a screenshot of the key screen.
4. **Before / after table**: minutes or days per unit, $ per case, accuracy (N = ?), escalation rate.
5. **How it works**: the diagram image (`pitch/diagram.png`) + one line per step type
   (code / AI / human / wait). Why AI only where it's used.
6. **Plugs into**: the firm's stack (CRM / case management / n8n). What is mocked today.
7. **Limits & safeguards**: human approval gates, source citations, synthetic data only, PHI/BAA line,
   no legal advice.
8. **Run it**: `uv sync && uv run streamlit run app/main.py` (adjust to reality), plus replay mode.
9. **Disclosure**: what was prepared before the event (docs, skills, provider check script) vs built today.

## 2. Write `pitch/video-script.md` (≤ 2 min; result visible within 15 s)
| Time | Content |
|---|---|
| 0:00–0:15 | The outcome on screen + the value line |
| 0:15–1:30 | One demo case end-to-end, including a low-confidence item going to human review |
| 1:30–2:00 | Numbers table + diagram + "plugs into your stack" |

## 3. Checklist (print it, tick each box)
- [ ] Video recorded, uploaded, link plays in an incognito window
- [ ] Repo public, or access granted per the organizers' instructions
- [ ] README renders; images load
- [ ] Replay mode works with wifi off (`app/cache/`)
- [ ] No `.env`, keys or real PHI committed (`git log -p | grep -i "api_key\|sk-"` is empty)
- [ ] Submitted by 3:45; confirmation screenshot saved
