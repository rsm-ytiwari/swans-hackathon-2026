# Instructions for Codex (and any other coding agent)

Read `CLAUDE.md`. Its hard rules and folder ownership apply to you too. In short:
- Work only in the files your task names. Don't expand scope.
- Dates, deadlines, and money math are plain Python, never an LLM call.
- Every LLM call goes through the project's provider wrapper and caches to `app/cache/`.
- Never invent numbers; label assumptions `ASSUMED`.
- "Done" means you ran the verification command. Write the command and its output in your final message.
- Never commit `.env` or anything resembling real PHI.
