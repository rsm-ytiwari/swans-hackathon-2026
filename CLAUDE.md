# Swans Applied AI Hackathon: team repo (Oct 2, 2026)

Two-person team building a working AI automation for one real personal-injury (PI) law firm problem in
~6 hours. Judges: the Swans CTO/engineers ("survives a real firm?") and PI firm executives ("would I pay?").

## Read-before-acting map (read on demand, not all at once)
| When | Read |
|---|---|
| **Start of every chat** | `plan/HANDOFF.md` (where we are), then the `plan/DECISIONS.md` entries it cites |
| After any action | Append to `plan/LOG.md` with its D-id. New decision → PROPOSED entry in `plan/DECISIONS.md`. Milestone → overwrite `plan/HANDOFF.md` (≤60 lines) |
| Sapini case contents / slides detail | `brief/sapini-map.md`, `brief/slides-inventory.md` |
| Brief arrives, or re-scoping | Run `/kickoff` (it loads `brief/`, `docs/event.md`, `docs/domain.md`, then its catalog) |
| Any question about judges, timeline, roles | `docs/event.md` |
| Any PI domain term, money lever, competitor | `docs/domain.md` |
| Choosing a tool or model for a step | `.claude/skills/kickoff/capability-catalog.md` |
| Before writing code | `plan/decision.md` + `plan/tasks.md` (if they don't exist, run `/kickoff` first) |
| 2:30pm freeze, or packaging (submit by 3:30, hard close 4:00) | Run `/submit` |
| Before the demo / pitch | `docs/demo-day.md` |

**Never propose a solution before reading the brief and `plan/decision.md`.**

## Hard rules
1. **Committed decision:** `plan/decision.md` is the contract. Don't expand scope beyond it. Propose cuts,
   not additions. Changes need a human "yes."
2. **No invented facts:** every number not from the brief, the reps, or our eval is labeled `ASSUMED`.
   Never fabricate metrics, quotes, or test results.
3. **Ladder:** deterministic code before AI. A step uses an LLM only if you can say in one sentence why
   code can't do it. Dates, deadlines and money math are always code.
4. **Verify, don't claim:** "done" means you ran it and saw it work. Show the command and its output.
5. **Demo safety:** every LLM call goes through one provider wrapper, caches to `app/cache/`, and the app
   has a replay mode that works with wifi off.
6. **Human gate:** nothing leaves the firm (email/SMS/letter) without an approval step. Synthetic data only;
   never commit `.env` or anything resembling real PHI.
7. **Ownership:** Yash owns `app/`, `plan/`. Partner owns `data/`, `eval/`, `pitch/`. Don't edit the
   other person's folders; ask instead. Commit small, pull often.
8. **The clock is the humans' job; quality is yours.** Don't rush, hedge, or cut corners because of
   time. The humans manage the schedule by cutting *scope* at checkpoints, never quality.
   - If a task turns out bigger than expected, stop and report: what's done, what's left, and 2
     smaller-scope options.
   - Never present a stub, placeholder, or hardcoded output as working. Anything mocked on purpose is
     labeled `MOCK` in code and UI.
   - A smaller thing done properly beats a bigger thing half-done.

## Thinking and delegation routing
| Work | Who | Model / effort |
|---|---|---|
| `/kickoff` | Skill (switches automatically) | Opus · xhigh |
| Orchestrating, small fixes, reviewing results | Main session | Opus · medium (default in `settings.local.json`) |
| Re-scoping, design change, debugging after 2 failed tries | Main session, plan mode for big changes | `/effort high` for that task, then back to medium |
| Well-specified coding task in owned files | `implementer` subagent | Sonnet · medium |
| Codebase or doc lookups | Built-in `Explore` subagent | — |
| 12:00 and 2:30 demo-readiness review | `reviewer` subagent | Opus · high |
| Self-contained module, separate files, clear interface | Codex: `codex exec -s workspace-write -o plan/codex-<task>.md "<task + files + done-criteria>"` | Codex default |
| Bulk synthetic data, app runtime experiments | Local Ollama `gemma4:26b` / free Gemini | free |

- **Delegate only when it pays:** tasks over ~15 minutes, tasks that run in parallel, or tasks that read
  lots of files. Do small fixes inline with no ceremony. Max **3 parallel subagents**.
- A delegation states: goal, files it may touch, what "done" looks like, how to verify. Give it
  **scope, not deadlines.**
- Read subagent and Codex results critically and re-run their verification yourself.

## Context hygiene (the `plan/` files are the memory, not the chat)
- Decisions live in `plan/decision.md` and `plan/tasks.md`, so the chat can be cleared freely.
- `/clear` after `/kickoff` finishes, and after each checkpoint. Then start with "read `plan/` and continue."
- Use `/compact` mid-task if the session gets long. Prefer subagents for anything that reads many files
  or long logs; they return ≤ 10-line summaries.
- Don't paste large outputs or whole files into the chat. Point to the path.
- Local models are for the **app's runtime and data generation**, not for writing our code (too much
  quality loss for a 6-hour build).

## Tools: MCP servers (`.mcp.json`) and skills
| Tool | Use for | Don't use for |
|---|---|---|
| `context7` | Current library docs before writing SDK code (anthropic 1.x, pydantic-ai v2, streamlit 1.64, n8n). APIs changed in 2026; check before guessing | General questions |
| `n8n-mcp` | Designing and validating n8n workflows (node docs and templates). Deploying needs `N8N_API_URL` + `N8N_API_KEY` from local n8n (`docker run -p 5678:5678 n8nio/n8n:2.41.5`) | Core AI logic (keep that in Python behind one HTTP endpoint) |
| `playwright` | Clicking through the Streamlit demo end-to-end before the 12:00 and 2:30 checkpoints; README/submission screenshots | Scraping, or anything in the live demo itself |
| `pdf` / `docx` skills | Filling or generating PDFs and Word letters | — |

**Superpowers skills, time-boxed for a 6-hour build:**
- `/kickoff` replaces `brainstorming`, and `plan/tasks.md` replaces `writing-plans`. Don't run those two.
- Write tests first only for deterministic logic (dates, SOL, money math).
- Use `systematic-debugging` when stuck after 2 tries.
- Use `verification-before-completion` always.

## Stack (default unless /kickoff decides otherwise)
Python 3.13 via `uv` · Streamlit UI · `scripts/check_providers.py` tests Ollama / Gemini / Anthropic ·
keys in `.env` (see `.env.example`).
