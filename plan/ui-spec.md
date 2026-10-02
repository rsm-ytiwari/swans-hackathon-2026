# UI spec: Sapini case digest (firm view + provider sharing) · draft 11:20 · PROPOSED

Stack: FastAPI + Jinja2 + Tailwind (local, no build) + HTMX + Alpine.js. Wireframes: `prototype/firm.html`,
`prototype/provider.html` (gitignored; rebuild with `python3 prototype/build.py`, all values computed from
`app/data/clio.db`). Markup is plain Tailwind; each block is marked `<!-- macro: name(params) -->` to lift into Jinja.
Laptop target: 1440×900. "Code" = deterministic Python; "AI" = LLM via the one wrapper, cached per ingest run.

## a. Design principles
1. **Story before numbers (inverted pyramid).** Three cited sentences sit above any KPI. Answers raw L48 on CasePeer
   ("I'm not sure what exactly happened") and L29 ("who the person is, what happened, what are the injuries").
2. **Overview first, zoom and filter, details on demand (Shneiderman).** This maps to three layers: 90 s (one screen),
   2 min (scroll), deep (every entry plus its source). Quote 4: "Sometimes … two minutes. Sometimes … dig into everything."
3. **The detail is zero jumps away.** Every value carries a source chip, or its title is the link. One click opens a
   side `<dialog>` with the raw note, email or PDF page; there is no tab change. Fixes slide 12 ("the detail one jump
   away") and slide 11 ("walking tab by tab"). Quotes 5–6, D-006.
4. **Exceptions over inventory.** Show what's late, contradictory, changed or waiting, not counts of things. CasePeer's
   KPI tiles are mostly empty and its 2023 tasks are not flagged overdue. Quotes 3, 11.
5. **Code computes, AI narrates, both cite.** Dates, ages, overdue days, money sums and the specials check are code.
   AI writes the story, ranks key events and finds contradictions, and its output is cached. Quote 10, CLAUDE.md rule 3.
6. **Deny by default, and show the denial.** The provider page is an allowlisted slice. In preview, the attorney sees
   dashed "Hidden from provider" markers for everything withheld. Slide 10; quotes 15–16; D-003.
7. **5-second glanceability.** Status is always color + icon + words (✓ ! ⏳ 🔒), never color alone. The first screen
   answers who, what happened, the stage, what's late and what it's worth.

**Anti-patterns we will not repeat (slides 6, 11–13):** billing tiles showing $0.00 where PI money belongs (Clio) ·
key facts as truncated free text behind "Show more" (Clio custom fields) · a blank matter stage (Clio) · count-only
KPI tiles with no values (CasePeer) · a single bills total with no per-provider split (CasePeer) · overdue tasks not
flagged (CasePeer) · injuries on a separate tab (CasePeer) · timelines of system events like "Status changed to: pnc"
(Lawmatics) · a story the reader must assemble by hand (all three) · an AI chat box as the main interface (slide 8).

## b. Information hierarchy
### Firm view
| Layer | Block (top→bottom) | Shows | Source (table.field) | Code/AI | Quote |
|---|---|---|---|---|---|
| 90 s | Top bar | matter, view switch, last sync, "digest cached" | matters, ingest_runs | code | 10 |
| 90 s | Case header | initials/photo, name, age, employer, responsible atty, stage 5/8 stepper, incident date, SOL ✓, last talked to client, next deadline | matters, contacts.date_of_birth, custom_field_values, matter_stages, tasks, communications (Phone with client) | code | 7, 9, 5 |
| 90 s | "Since you last looked" strip | counts since last visit + top 3 changes | notes.date, communications.date, documents.received_at vs our `last_seen` | code counts, AI picks top 3 | 1, 2 |
| 90 s | What this case is about | 3 sentences, each with chips | notes, custom_field_values, documents (page) | AI (cached) | 1, 8 |
| 90 s | Needs attention | overdue / coming up, who it waits on (provider · client · firm), next calendar entry | tasks.due_at/status/name, calendar_entries | code (prefix "By medical provider:" → provider) | 11 |
| 90 s | Money 🔒 | value $375,000 vs coverage $100k/$300k (confirmed), ratio 3.75×, specials $118,400 ✓, Medicaid lien, no-fault, UM/UIM, wage loss, firm spend $1,410 | custom_field_values, activities (non_billable_total vs total), communications | code | 12, 13 |
| 90 s | Red flags 🔒 | 4 contradictions, each with ≥2 sources | notes, custom_field_values, record PDFs | AI (cached), verify | (F7) |
| 2 min | Key events | 10 of 187 entries | candidates from code (docs in Pleadings, procedures, stage-type notes, SOL, IMEs); AI ranks | code+AI | 3 |
| 2 min | Specials by provider | 9 bars, ledger chips | activities.note (provider; service range) | code | 12 |
| 2 min | Injuries & treatment | body part → finding → page cite → treatment | 04-medical-records PDFs (text layer) | AI extract, page-cited | 8 |
| 2 min | Treating providers | billed, service dates, records pages, last contact, open request | activities, documents.page_count, communications, tasks | code | 22 |
| deep | All entries | filter pills by type, search, newest first, each opens source | notes, communications, documents, tasks, calendar_entries, activities | code | 4, 6 |
| deep | Source dialog | raw text / PDF page, Clio type + id + page | raw, documents.local_path | code | 5, 6 |

### Provider view (as the provider sees it; the attorney sees the same page inside "Preview as provider")
| Layer | Block | Shows | Source | Code/AI | Quote |
|---|---|---|---|---|---|
| 90 s | Status card | "Case is active: in the lawsuit stage", last activity date, plain-language 8-step milestones, when bills get paid | matters.stage_name, max(notes.date, communications.date) | code | 19, 15 |
| 90 s | What we need from your office | open tasks for this provider + recent requests sent to them; "newest record we hold is dated …" | tasks ("By medical provider: <name>"), communications to provider, activities services end | code | 22 |
| 90 s | Your bills on file | billed $14,220, 130 lines, date range, payment status as recorded ("unknown") | activities.non_billable_total, bill PDF lines | code | 18 (partial) |
| 90 s | Latest update | "case moved" text, built from tasks/stage, needs approval | tasks, matters | AI draft → attorney approves | 20 |
| 2 min | Treatment | status line + next booked visit at their office | custom_field_values(Treatment Status), calendar_entries | code | 23 (partial) |
| 2 min | Records on file | their own records + records the firm chose to share | documents | code | 21 |
| deep | Open a shared document | only allowlisted PDFs | documents | code | 21 |
Never on this page: notes text, case value, liability, prior injuries, other providers' bills, liens, wage loss,
negotiation history, expert reports, claim numbers. The build fails if any of these appear (see `build.py` leak check).

## c. Wireframes (ASCII, 1440 wide; see HTML for the real thing)
```
FIRM ─────────────────────────────────────────────────────────────────────────────────────────────────────────
[Luma / 00001-Sapini · Justin Sapini]  [Firm view|Provider sharing]           Synced 11:10 · digest cached
┌ JS  Justin Sapini        │ Stage 5 of 8 ▬▬▬▬■□□□  │ Incident Apr 23 2023 [F] │ SOL Apr 22 2026 ✓ [T]       ┐
│[ID] 30 · Fin. advisor    │ Intake…Litigation…Closed│ Last talked Sep 27 (5d)[C]│ Next Oct 5 reconcile…[T]  │
└──────────────────────────┴─────────────────────────┴───────────────────────────┴───────────────────────────┘
[Since you last looked · MOCK Sep 1 · 8 notes 15 emails 3 docs · Coverage confirmed[E] · 3 reports[D] · …  All 26 →]
┌ WHAT THIS CASE IS ABOUT (AI, cited) ┐┌ MONEY 🔒 ─────────────────┐┌ RED FLAGS 🔒 (AI, verify) ───────┐
│ 1. Sideswiped … [F][N]               ││ $375,000 [F]│ $100,000 ✓[E]││ ! PT discharge vs never… [D p12]│
│ 2. L shoulder surgery; R undated…    ││ 3.75× limit (computed)      ││ ! Whose $100k policy? [N][N][E] │
│ 3. Litigation; IMEs done…            ││ Specials $118,400 ✓ 9 bills ││ ! Prior injury denied [N][N]    │
├ NEEDS ATTENTION 2 late·4 next·4 wait ┤│ Medicaid lien $22,180       ││ ! Three accounts of crash [N]   │
│ Aug 25 38d late Updated records… ⏳McCulloch ││ No-fault exhausted · UM/UIM ││                                 │
│ Sep 26 6d late  Employment recs… ⏳Client    ││ Wage loss · Firm spent $1,410││                                │
│ Oct 5… Oct 7… Oct 10… Oct 14…  · next cal Oct 9 │└─────────────────────────────┘└─────────────────────────────────┘
──── 2-minute layer: Key events (10 of 187) | Specials bars | Injuries (page-cited) | Treating providers ────
──── Deep layer: [All 187][Notes 42][Emails 69][Docs 31][Tasks 14][Calendar 17][Ledger 14] [search] → rows ──
PROVIDER SHARING (attorney) ────────────────────────────────────────────────────────────────────────────────
┌ 1 Choose ■2 Preview 3 Approve 4 Receipts ┐ ┌ PREVIEW AS PROVIDER · Advanced Rockland Chiro   [Not yet shared]┐
│ providers list (9) · draft / not shared   │ │ Justin Sapini · DOB · injured Apr 23 2023 · HIPAA on file [F]   │
├ SHARED WITH … (toggles)                   │ │ ✓ Case is active: lawsuit stage · last activity Sep 27           │
│ ● status ● own bills ● own records        │ │   Case opened→Treating→Demand→Negotiating→■Lawsuit→Trial→Bills paid│
│ ● what we need ● treating? ● updates      │ │ ┌ What we need (2) ───────────┐┌ Your bills $14,220 · 130 lines┐ │
│ ○ coverage [Off|"Confirmed"|Amounts]      │ │ └ newest record from you Aug 15, 2024 ┘└ payment status: unknown┘ │
│ other providers' records: ● HVR MRI ○ op  │ │ Latest update (AI draft, needs approval)                          │
├ APPROVE [Approve and share] receipts      │ │ Treatment: active · next visit Oct 9 │ Records on file + shared   │
├ NEVER SHARED 🔒 value · liability · notes │ │ ░ Hidden from provider: coverage (Off) ░                           │
└ · other bills · liens · experts           │ │ ░ Hidden from provider: value, liability, 42 notes… (firewall) ░  │
```

## d. Sharing-controls flow (attorney side)
1. **Choose** provider (list = providers with charges in `activities`, with draft / shared / not-shared state from our DB).
2. **Toggle** the allowlist per provider. Defaults: status, own bills, own records, requests, treatment status ON;
   coverage OFF (graded Off / "coverage confirmed" / amounts, pending Q-1); other providers' records OFF, one at a time;
   firewall items are locked and render as 🔒 switches that cannot move.
3. **Preview as provider:** the same template the provider gets, rendered with `preview=True`. In preview, every
   withheld block renders a dashed `hidden_marker` in place, so the attorney sees what's missing and why. The real
   provider render omits it entirely, so nothing is even hinted.
4. **Approve and share:** writes a snapshot (facts + allowlist + approver + time) to our SQLite and returns a signed,
   expiring read-only link. Nothing is written to Clio (D-001) and nothing is sent without this click (rule 6). The
   "case moved" update (P4) is an AI draft shown in the preview and goes out only inside an approved snapshot.
5. **Receipts:** link opens are logged per snapshot (time, count) and shown under Approve. For the demo this can be
   MOCK-labelled or a real local hit counter.

## e. Component kit: Jinja macros in `app/web/templates/components/`
Fact shape passed everywhere: `{label, value, kind(note|email|call|doc|field|task|ledger|matter|cal), clio_id, date, page}`.
| Macro | Params | Purpose |
|---|---|---|
| `source_chip(fact, label=None)` | fact | pill `<button>` with type dot; `hx-get="/source/{kind}/{id}?page="` into `#source-body`, then `showModal()` |
| `source_link(fact, text)` | fact, text | the item's own title opens its source (dotted underline) |
| `source_dialog()` | — | the single right-side native `<dialog id=source>` per page |
| `status_tag(kind, text)` · `severity_icon(level)` | ai/firm/crit/serious/warn/ok/mock/gray | colored pill / ✓ ! icon, always with words |
| `card(title, right=None)` | `{% call %}` body | white rounded panel with an uppercase label header |
| `top_bar(matter, view, sync)` | | brand bar, view switch, sync + cache line |
| `case_header(client, matter, stages, key_dates)` · `stage_stepper(stages, current, tone)` | | header grid; 8-step bar (brand tone for firm, ok tone for provider) |
| `change_strip(changes, since)` | | one-line "since you last looked" with top-3 chips |
| `story_block(sentences)` | `[{text, facts}]` | 3 cited sentences |
| `attention_list(overdue, upcoming, calendar_next)` | | single-line rows: date, late tag, title-link, ⏳ who |
| `kpi_tile(label, value, sub, facts, firm_only)` · `money_row(label, value, facts)` | | hero numbers and ledger rows |
| `flag_card(flag)` | `{level, title, text, facts}` | contradiction with ≥2 sources |
| `timeline(events, total)` · `specials_bars(rows)` | | key events "10 of N"; one-hue horizontal bars, value labels |
| `injury_table(rows)` · `provider_table(rows)` · `entry_table(entries, filters)` | | 2-min and deep tables; filter pills via `hx-get` |
| `provider_picker(providers, selected)` · `share_toggle(item, state)` | state on/off/locked | Alpine `x-model` switch; locked shows 🔒 |
| `firewall_list(items)` · `hidden_marker(label, reason)` · `approval_bar(provider, receipts)` | | deny list; dashed preview-only marker; approve + receipts |
| `provider_status(stage, last_activity, milestones)` · `update_draft(text, facts, approve_url)` | | provider hero; P4 draft |

**Tokens** (paste into the inline `tailwind.config`; vendor `tailwind`, `htmx`, `alpine` JS into `app/web/static/`
so the demo works with wifi off):
```js
tailwind.config = { theme: { extend: {
  colors: { canvas:'#f5f4f0', ink:{DEFAULT:'#1c2128',2:'#454c56'}, muted:'#6b7280', line:{DEFAULT:'#e4e2dc',2:'#efeee9'},
    brand:{DEFAULT:'#1f3a5f',soft:'#dfe8f3'}, accent:{DEFAULT:'#2a78d6',soft:'#eaf2fc',ink:'#1d5fae'},
    ok:{DEFAULT:'#0ca30c',soft:'#e9f6e9',ink:'#0a6e0a'}, warn:{DEFAULT:'#fab219',soft:'#fff6e0',ink:'#7a5200'},
    serious:{DEFAULT:'#ec835a',soft:'#fdefe8',ink:'#9a3f17'}, crit:{DEFAULT:'#d03b3b',soft:'#fbeaea',ink:'#a32020'},
    firm:{DEFAULT:'#6d28d9',soft:'#f1ebfd'}, mock:{DEFAULT:'#6b5600',soft:'#fff1c2'} },
  fontFamily: { sans:['-apple-system','BlinkMacSystemFont','"Segoe UI"','Inter','Roboto','sans-serif'] },
  fontSize: { label:['11px',{lineHeight:'16px',letterSpacing:'0.06em'}], body:['14px','20px'], title:['22px','28px'], kpi:['24px','30px'] } } } }
```
Spacing: Tailwind default 4 px scale. Cards use `p-4 rounded-xl border-line`; grid gaps are `gap-3.5` (14 px); a
layer break is `mt-7`. Status meaning: crit = overdue or contradiction; serious = waiting on a provider or a flag;
warn = waiting on the client or due soon; ok = done or confirmed; firm (violet) = 🔒 firm-only; mock = dashed yellow.
Text uses the `*-ink` shades only, never the raw status color.

## f. Quote traceability (slide 9)
| # | Quote (short) | Answered by |
|---|---|---|
| 1 | up to speed, what happened recently | story_block + change_strip + key events |
| 2 | what changed since I last opened | change_strip (needs a per-user `last_seen` in our DB; MOCK in wireframe) |
| 3 | 300 entries → the 10 that matter | timeline "10 of 187" |
| 4 | two minutes vs dig into everything | 90 s / 2 min / deep layers |
| 5 | a date on screen → where it came from | every header date carries a chip |
| 6 | click anything → note/doc/email | source_chip / source_link → dialog with raw text + page |
| 7 | client's picture on open | header avatar slot. Partial: wireframe shows initials; app renders page 1 of `photo-id.pdf` (scanned, no text) |
| 8 | injuries inside a 200-page scan | injury_table, page-cited (records have text layers; chiro chart is 131 pp) |
| 9 | when did anyone last talk to the client | header "Last talked to client" (latest Phone with client; emails shown separately) |
| 10 | don't re-digest every open | AI outputs cached per ingest run; re-run only on new entries; shown in top bar |
| 11 | overdue / coming / waiting on someone | attention_list with ⏳ provider/client tags |
| 12 | worth and coverage | Money heroes + ratio |
| 13 | how much has the firm spent | money_row "Firm has spent $1,410 · 5 costs" |
| 14 | what we shared, has anyone opened it | approval_bar receipts (snapshot log) |
| 15 | doctors see where the case is | provider_status |
| 16 | adjust what the provider sees before sending | share_toggle + preview + hidden_marker |
| 17 | a secure way of sharing part of my case | signed expiring read-only link to an approved snapshot. Partial: no provider login (Q-6) |
| 18 | is there coverage behind the case | graded coverage toggle, default Off. Partial: depends on Q-1 |
| 19 | is this case still alive | "Case is active" + last activity date |
| 20 | tell me when the case moves | update_draft → approval → link email. Partial: sending stays manual (rule 6) |
| 21 | I only see the records I sent | "Other providers' records" toggles (HVR MRI shared in preview) |
| 22 | what does the firm need from my office | provider "What we need" (tasks + request emails + newest-record date) |
| 23 | is my patient still showing up | Partial: treatment status + next booked visit; Clio has no attendance log, so we don't claim attendance |

## g. Validation kit (show the laptop, ≤30 s each)
| # | Ask | Listen for | What it changes |
|---|---|---|---|
| 1 | (firm.html, 10 s, then cover it) "What's this case about, and what's the next thing you'd do?" | did they say surgery undated / IMEs / McCulloch overdue? | if they miss it, reorder: attention above story, or shorten the story to 2 lines |
| 2 | "What would you click first?" | a source chip, a flag, Money | high chip use = invest in the source dialog (deep link, highlight); if ignored, shrink chips to icons |
| 3 | "Which of these would you never let a treating provider see? Is 'coverage confirmed' without amounts OK?" | coverage level, the request texts, treatment status | sets the allowlist defaults and the coverage grade (closes Q-1) |
| 4 | (provider.html) "As the chiropractor: is this case alive, and what do they need from you?" | answers in <10 s | if slow, make "What we need" the hero above the status card |
| 5 | "What's missing that would make you pay for this?" (Swans engineers: "what would break on a real firm?") | negotiation status, lien amounts, multi-matter | add one block or cut one; log the answers in LOG.md |
