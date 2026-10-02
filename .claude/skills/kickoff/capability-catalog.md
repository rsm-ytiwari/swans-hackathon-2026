# Capability Catalog: node type → tool (researched Oct 1, 2026)

**How to use:** read this only AFTER the solution shape is chosen (/kickoff Step 5). Give each to-be step
one node type, or **N (none fits)**, then consider the tool in its row. This is a reference, not a menu:
if the problem has no triage step, don't add Jev. If something better fits, use it.

**Default rule: climb the ladder only as far as you need to.**
deterministic code → cheap model → strong model → agent loop. Each rung up costs more, adds latency and
adds failure modes, so you have to be able to justify the climb in one sentence.

Verification status: ✅ = checked on a primary source (official docs / pricing / GitHub) · ⚠️ = secondary
source or unconfirmed. Prices are USD per 1M tokens (input/output) unless noted.

---

## Node types at a glance

| Code | Node type | Signal words in the brief | Default tool | Cost / run |
|---|---|---|---|---|
| **D** | Deterministic compute | dates, deadlines, SOL, totals, thresholds, dedupe, "within X days" | Python (dateutil, pandas, rapidfuzz) | $0 |
| **T** | Fuzzy triage / decision | qualify, route, prioritize, "is this…", urgent?, category | Jev / Clef-flash → cheap LLM with logprobs | ~$0.00001 |
| **X** | Extraction from documents | records, bills, police report, "pull out", summarize into fields | Gemini Flash / Claude Sonnet + Pydantic schema + quote check | ~$0.001–0.01 / page |
| **R** | Retrieval across a corpus | "past cases", "firm knowledge", "comparable settlements", playbook | Long-context first; RAG only across many matters | ~$0–0.01 |
| **G** | Generation of text | draft, letter, client update, demand, email | Jinja template for the fixed parts + Sonnet/Opus for prose | ~$0.01–0.05 |
| **A** | Act / integrate | update CRM, send SMS/email, schedule, notify | Direct API / webhook; n8n to show; mock legal CMSs | $0 (trial tiers) |
| **H** | Human gate | approve, review, sign off, exceptions | Streamlit queue (approve / reject / edit) | staff time |
| **W** | Wait / external dependency | "waiting on provider", follow-up, chase, adjuster response | D timer + A follow-up + H escalation | $0 |
| **V** | Voice / conversation | calls, after-hours, intake line | Only if the problem is calls: Retell / Vapi; else faster-whisper on recordings | $0.07–0.31/min |
| **O** | Orchestration | (always present) | Plain Python workflow; agent loop only if the number of steps is unpredictable | — |
| **E** | Evaluation | (always present) | Gold-label CSV + pytest + confusion matrix in Streamlit | $0 |
| **N** | None fits | dashboard of stalled cases, form/checklist redesign, CRM config, status page, delete the step | Describe it plainly; often Streamlit/Airtable/n8n with no AI at all | $0 |

---

## D: Deterministic compute
**Use for:** anything with a parser, a formula or a lookup table. That covers SOL dates, days since the last
treatment (treatment gap), sums of bill line items, "records request > 30 days old", deduplicating
provider names, lien arithmetic and settlement disbursement math.

| Need | Tool |
|---|---|
| Parse and compare dates | `python-dateutil`, `dateparser` |
| Fuzzy-match provider names | `rapidfuzz` |
| Tables and sums | `pandas` |
| Statute of limitations | A cited table (Justia 50-state survey). Flag exceptions: med-mal, government-entity notice, minors |
| Codes | NLM Clinical Tables ICD-10-CM API (free, no key) ✅; RxNorm `/approximateTerm` ✅. **CPT descriptions need an AMA license** ✅. Extract printed codes only |

**Why this matters for the pitch:** Jev's own docs say it is unreliable at dates and arithmetic
("extract components; compare in code") ✅, and LLMs are too. Saying "dates are computed in code because
deadlines must be exact" is a sentence that wins over the CTO.

## T: Fuzzy triage / decision (typed answer + confidence)
**Use for:** a judgment on short unstructured text that returns yes/no, one of N options, or a score.
Examples: is this lead qualified, which document type is this page, is this client message urgent, does it
mention a new injury, who should handle it.

| Option | Cost | Latency | Confidence | Setup | Gotchas | Status |
|---|---|---|---|---|---|---|
| **Jev** (TypeSafe) `pip install typesafe-sdk` | $0.042 in / output free | ~0.1–0.5 s | Native probabilities. Good in-distribution; ECE 0.107 out of distribution in an independent test (choice overconfident, yes/no underconfident) | 10 min with a key | **Signup / credit status unclear** (paused Sep 22, reportedly reopened without the $5 credit ⚠️). Weak on dates, arithmetic, multi-hop and injection. English only. 64k context | Docs ✅ |
| **Jev via Cloudflare Workers AI** (`typesafe/jev`) | same, zero data retention | same | same | 15 min | Fallback if direct signup is blocked | ✅ |
| **Cloudflare Clef-flash / Clef** (`@cf/cloudflare/clef-flash`) | $0.09 / $0.24; free tier ≈1.2M tokens/day | 39 / 209 ms (vendor numbers) | Brier-trained; **not independently tested** (launched Oct 1) | 15 min | Same request shape as Jev. Accepts images. Apache-2.0 weights, but local use needs a big GPU | ✅ |
| **Laya** `pip install laya` (421M, local) | free | ~33 ms | Calibration claimed, unverified | 10 min | Single maintainer; shaky beyond ~4k tokens | ✅ repo |
| GLiClass / ModernBERT-zeroshot / DeBERTa-zeroshot | free, CPU | 10–100 ms | **Uncalibrated** | 15 min | Labels must be phrased as hypotheses | ✅ |
| SetFit (8–16 labels per class) | free | ms | OK once calibrated | 30–60 min | Needs labeled examples | ✅ |
| GPT-6 Luna / gpt-4.1-nano **with logprobs** | ~$0.10 in | 0.5–1.5 s | Good: softmax over a single-token enum | 20 min | Logprobs only when `reasoning_effort: "none"` | ✅ |
| Claude Haiku 4.5 / Gemini Flash-Lite + structured output | $1 / $0.25 in | ~1 s | **No logprobs on Claude.** Use a 5-sample vote, never self-reported confidence (models are overconfident: Xiong et al., ICLR 2024) | 15 min | — | ✅ |
| Ollama local (qwen3.5:9b, gemma4:12b) + JSON schema | free | 0.2–2 s | Logprobs available | 30 min | Quality depends on model size | ✅ |

**Demo default (post-review):** keep the triage step **swappable** behind one function. Put Jev in the
live demo only if the key works AND it scores ≥ Haiku/Gemini on your labeled cases. Otherwise mention it
as a swappable option ("plugs into decision models like Jev or Clef"). Clef launched Oct 1, so never make
it the default.

**Rule:** rules first, then Jev or Clef for many fast typed questions on short English text, then an
open-source classifier when data must stay on the machine, then a cheap LLM when the judgment needs reading
comprehension, long input or a rationale. **Always gate on confidence and send low-confidence items to H.**
Hold out ~20 labels to check calibration.

**Pitch line:** "Triage returns a probability; anything under 0.8 goes to a case manager. The escalation
path is the feature."

## X: Extraction from documents (fields + source)
**Use for:** medical records, itemized bills (UB-04 / CMS-1500), police reports, insurer letters, intake forms.

| Step | Default | Cheap / free | Local / open-source |
|---|---|---|---|
| Has a text layer? | PyMuPDF check | — | — |
| Scan → text | Mistral OCR ($4 / 1k pages; $10/mo free credit) ✅ | Textract text $1.50 / 1k | **Docling + ocrmac** (Mac native, ~0.2 s/page OCR, ~1.3 s/page full pipeline on M3) ✅ |
| Fields → JSON | **Claude Sonnet 5.5 `messages.parse(output_format=Model)`** ✅ (≈$0.006–0.01/page) | **Gemini 3.5 Flash-Lite + response schema** (<$0.001/page; free tier trains on your data, so synthetic only) ✅ | Instructor + Ollama |
| Source grounding | Claude **Citations** (page ranges + `cited_text`) ✅ | **LangExtract** (character offsets + HTML highlight view; works with Gemini, OpenAI or Ollama) ✅ | LangExtract + Ollama |

**Gotchas (✅):**
- Claude **can't combine Citations with structured outputs in one call** (it returns 400).
- Scanned PDFs without a text layer can't be cited, so OCR them first (Docling or `ocrmypdf`).
- Claude limits: 600 pages / 32 MB per request (100 pages when context < 1M). Gemini: 1,000 pages / 50 MB.
- Don't put PHI inside the schema itself (schemas are cached for up to 24 h outside ZDR).

**Recipe (two passes):**
1. Pass 1 extracts with the schema, and every field carries `source_page` + `verbatim_quote`.
2. Pass 2 checks each quote against the OCR text with rapidfuzz. Reject anything it can't locate.
3. Then D checks the math: line items sum to the total, dates fall after the accident date.

**Pitch line:** "Every number links to its page; anything we can't find in the source is rejected, not
guessed." This answers the #1 lawyer fear: hallucination (Stanford found 17–33% in legal tools).

## R: Retrieval
| Situation | Do |
|---|---|
| One client's case file (< ~500K tokens) | **No RAG.** Put it all in Sonnet 5.5 or Opus 5.5 (1M context ✅) with prompt caching |
| Firm-wide corpus: past settlements, playbooks, FAQs, many matters | **Hybrid RAG** (BM25 + vectors; legal text is full of exact codes and numbers). LanceDB (built-in hybrid + RRF) or Chroma; embeddings Qwen3-Embedding-0.6B or EmbeddingGemma-308M; reranker only if the top 5 look wrong |
| Settlement comparables (demo data) | SetCalc API (~4.1K PI verdicts, CC-BY, no auth) ⚠️; CourtListener API (low free limits) |

**Pitch line:** "We didn't build RAG for a single case file, because it fits in context. RAG is only for
the cross-case knowledge base." The CTO will respect the restraint.

## G: Generation
- Put fixed legal boilerplate in **Jinja templates** (deterministic, approved by an attorney). The LLM fills
  only the narrative parts.
- Models: Sonnet 5.5 ($2 / $10) by default; Opus 5.5 ($4 / $20; always uses thinking, so set
  `effort: "low"`) for the final client-facing prose.
- **Always follow G with H** before anything leaves the firm (ABA Formal Op. 512; Rule 1.4 communication;
  no legal advice from client-facing bots, to avoid unauthorized practice of law).

## A: Act / integrate
| Target | Use | Status |
|---|---|---|
| Clio / Filevine / Lawmatics | **Mock behind a thin adapter.** None has a vendor-official MCP server (community only), and sandbox access is uncertain. Pitch: "swaps to Clio's v4 API" | ✅ |
| HubSpot / Slack / Google Workspace / DocuSign / Airtable | Official remote MCP servers exist. Use one only for a "Claude acts inside your tool" moment | ✅ (HubSpot GA date ⚠️) |
| SMS | Twilio trial: verified numbers only (up to 5), 100 SMS, "Sent from a Twilio Trial account" prefix | ✅ |
| Email | Resend free (3,000/mo, 100/day). SendGrid's free plan is gone | ✅ |
| Orchestration visual | **n8n** (cloud 14-day trial or `docker run n8nio/n8n`): webhook → your Python service → CRM / SMS nodes. Swans builds on n8n/Make/Zapier, so this reads as "deployable tomorrow" | ✅ |

**MCP rule:** MCP is a demo multiplier, not plumbing. Use it for (a) Claude acting live inside an official
server, or (b) a FastMCP server exposing *your* pipeline (`case_status`, `missing_records`) so a paralegal
can ask Claude Desktop (30–60 min to build). Inside the pipeline itself, use direct API calls.
Current spec: 2026-07-28 (stateless, Streamable HTTP) ✅. The Claude API can call remote MCP servers via
`mcp_servers` ✅.

## H: Human gate
Use a Streamlit queue: item · AI output · confidence · source highlight · Approve / Edit / Reject.
Log every action (an audit trail). This is a feature, not overhead: it's what the executive panel looks for.

## W: Wait / external dependency
PI leaks value in waits: records requests (HIPAA allows 30 days; reality is 45–90), adjuster responses,
treatment follow-ups.
**Pattern:** D (timer and age rules) → A (automatic follow-up) → H (escalate at threshold).
Show an "open loops" board: everything pending, its age, and the next action.

## V: Voice
Only if the brief is about calls or intake. Use Retell ($10 free credit) or Vapi ($5 credit, 1 free number)
with a webhook to your backend (1–2 h). Otherwise transcribe recordings with `faster-whisper` and skip live
telephony risk.

## O: Orchestration
A **workflow** (fixed steps in Python) by default; most PI ops are standard operating procedures. Use an
**agent loop** (Claude Agent SDK / Pydantic AI) only where the number of steps is unpredictable (e.g.,
chasing missing records across sources). Source: Anthropic, "Building effective agents" ✅.

## E: Evaluation
- 15–20 hand-labeled synthetic cases in a CSV, scored with pytest
- Show field-level accuracy, a confusion matrix for T nodes, escalation rate and cost per case
- Show 2–3 failure cases and how they are routed to a human

**Synthetic data recipe:**
1. Jinja/HTML templates filled by Faker (+ Synthea if you want clinical realism; it needs Java 17 and has no PDFs or notes).
2. Render with WeasyPrint.
3. Add scan noise with `augraphy`.
4. Keep the clean JSON as ground truth.

Blank forms: CMS-1500 (cms.gov), UB-04 (CMS MLN006926), CA CHP 555, TX CR-3.

---

## Runtime provider tiers: local-first, paid as backup
All of these speak the OpenAI-compatible API, so one client with a `base_url` switch covers them
(`scripts/check_providers.py`).

| Tier | Provider | Use | Data rule |
|---|---|---|---|
| 1. Local, no key | Ollama `gemma4:26b` (MoE, ~4B active, fast on the M4 Pro 48 GB) at `localhost:11434/v1` | Triage, short extraction, synthetic data generation | Anything; never leaves the laptop. **Pitch angle: "PHI never leaves the firm"** |
| 2. Free cloud | Gemini via AI Studio (OpenAI-compatible endpoint); Cloudflare Workers AI (Clef/Jev); Groq (8K tokens/min, so short inputs only) | Long PDFs (Gemini reads them natively), development runs | **Synthetic only** (free tiers may train on inputs) |
| 3. Paid backup | Anthropic (Haiku 4.5 / Sonnet 5.5), OpenAI (gpt-6-luna with logprobs) | Highest-accuracy runs, final demo if it wins the bake-off | Commercial terms |

**Decide by bake-off, not ideology:** run the same 6–15 labeled cases through tiers 1–3 and demo on the
winner. Show the comparison table (accuracy · $/case · data leaves the building?). The CTO panel will
value it.

**HIPAA / BAA (the CTO will ask):** Anthropic and OpenAI offer BAAs for API customers with zero data
retention (enterprise arrangement) ⚠️ (confirm wording if asked). Google Cloud signs BAAs for Vertex AI,
**not** for the AI Studio free tier. Local Ollama needs no BAA because no data leaves.
**Say:** "Demo on synthetic data; in production, PHI runs locally or only through BAA-covered,
zero-retention endpoints."

## Model / cost ladder (≈50-document demo)
| Node | Model | ~Cost for 50 docs |
|---|---|---|
| T triage | Jev / Clef-flash (or Haiku 4.5, gpt-6-luna, Flash-Lite) | < $0.15 |
| X extraction | Sonnet 5.5 (Haiku for simple forms; Flash-Lite during development) | ~$1 |
| Long-file reading | Sonnet 5.5 + prompt caching | ~$4 |
| G drafting | Opus 5.5 at medium effort / Sonnet 5.5 | ~$1–2 |
| E LLM-judge (if needed) | Opus 5.5 at low effort, or Batch (50% off) | ~$1 |

One full run ≈ $8, or $15–20 with thinking tokens and retries. Budget $30–80 including development runs.
**Develop on free Gemini or local models with synthetic data; run the final demo on Claude.**

Anthropic prices ✅: Haiku 4.5 $1 / $5 · Sonnet 5.5 $2 / $10 · Opus 5.5 $4 / $20 · Fable 5.1 $10 / $50 ·
Batch −50% · cache read 0.1×.
**The Claude API has no logprobs** ✅.

## Keys and accounts (set up tonight)
| Account | Why | Check / get |
|---|---|---|
| **Anthropic API** | App runtime. **A Claude Max subscription includes NO API credit** ✅, and terms forbid using subscription login as an app backend ✅ | platform.claude.com → Settings → Billing (balance) · Settings → Limits (tier) · API keys. Add $25–50, set a spend limit, run one Haiku test call |
| **Google AI Studio** | Free Gemini key for development (synthetic data only; the free tier trains on inputs ✅) | aistudio.google.com |
| **Cloudflare** | One account gives you **Jev and Clef** on Workers AI | dash.cloudflare.com → Workers AI → account ID + API token |
| TypeSafe (Jev direct) | Try it; access is uncertain ⚠️ | console.typesafe.ai |
| OpenAI API (optional) | Logprobs triage via gpt-6-luna. **ChatGPT/Codex includes no API credit** ✅ | platform.openai.com → Settings → Billing, $5 minimum |
| Ollama (optional) | Offline fallback | `ollama pull qwen3.5:9b` |
| Not available | — | GitHub Models (retired Jul 30, 2026) ✅; OpenAI Decisions API (preview, no docs yet) ✅ |
