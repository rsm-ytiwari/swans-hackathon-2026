# UI critique: do we repeat the organizers' criticisms? · 2026-10-02 11:35 · reviewer, read-only

Evidence: 1440x900 viewport screenshots in `.playwright-mcp/critique-{firm-proto,provider-proto,live-firm,live-share,live-provider-preview}.png`
(+ `-full` for firm). Counts come from a DOM pass over the text and buttons that are visible in the first viewport.

## 1. Verdict
- **Firm prototype: yes, it is overloaded.** The first screen has 638 words, 42 source pills, 11 dollar figures and 9 bands. It
  answers the right questions but scatters them over 4 cards and makes the reader join them: "the story assembled by hand", at higher density.
- **Live firm app: less text (260 words), but it has Clio's shape.** Three equal cards (Key facts / Money / Overdue) form a
  re-skinned KPI grid, with a count tile ("Treating providers 10"), lists, and Clio schema names on the chips. It has no bottom line and no flags.
- **Provider side: the live preview is the most digestible screen we have.** The live share page (10 cards × 6 checkboxes)
  is a pure inventory list. The prototype sets the attorney controls beside the preview, so the two compete for the first screen.

## 2. Organizer criticism → our UI
| Criticism (source) | Firm proto | Provider proto | Live app | Repeats? | Evidence |
|---|---|---|---|---|---|
| "what's been happening" = reading everything (S6) | 638 words before scroll | 538 words incl. controls | 260 words | partly | Proto: the recent state sits in story sentence 3, a strip and Money, so you must read all three |
| "visual digestion… without knowing what to ask" (S8) | stepper only; rest is text + pills | stepper + text | stepper + text cards | partly | The only visual encoding above the fold is the 8-step bar. The key-events timeline and bars sit in the 2-min layer |
| "walking tab by tab" (S11) | one page, 3 layers | same page | firm and sharing are separate pages | no | Source dialog opens in place (hx-get to #source-body), both proto and live |
| "counts and lists on the dashboard" (S12) | strip "8 notes · 15 emails/calls · 3 docs"; "2 overdue · 4 coming up · 4 waiting"; "9 providers"; "5 costs"; "All 26" | "9 providers… MOCK" | tile "Treating providers **10**"; Providers & bills list (10); Coming up list; share = 60 checkboxes | proto partly / live **yes** | The live count tile is CasePeer's "HEALTH PROVIDERS 2" all over again |
| "the detail one jump away" (S12) | chips open dialog | same | chips open dialog | no | Good. Cost: 42 pills of ink on the first screen |
| "the story assembled by hand" (S12) | story, money, flags and attention are 4 separate cards; no bottom line | n/a | 1 header sentence, then facts/money/tasks to join yourself | proto partly / live **yes** | Nowhere does the screen say "$375k claim vs $100k cover; blocked on undated R-shoulder surgery; chase McCulloch" |
| "I'm not sure what exactly happened" (raw L48) | story s1 answers it | "injured Apr 23 2023" | header sentence answers it | no | — |
| "not something I'd look at and see what is happening" (raw L49) | "In litigation; IMEs done" is sentence 3 of card 2 | "Case is active: lawsuit stage" | stepper only | partly | "What is happening now" never leads the page |
| Clio: KPIs + custom fields + contact details, still not enough (raw L46, S11) | Money = 7-row custom-field list | — | 3 equal cards, ~400px empty in Key facts/Money | live **yes** | It reads as Details/Financial/Custom fields restyled |
| Lawmatics: system events, not meaning (S13) | deep rows show filenames | — | chip labels "CustomFieldValue", "CalendarEntry"; task text "By medical provider: X - …"; provider page shows "05-medical-bills__created__advanced-…pdf" | live partly | These are raw Clio/system strings on screen |
| Q3 "of 300 entries, the 10 that matter" (S9) | ~33 facts above the fold (my count) | ~20 | ~25 | partly | The curated "10 of 187" sits below the fold. The first screen shows 3× that many items, uncurated |
| Q4 "two minutes… or everything" | 3 layers | — | one flat layer | live partly | — |
| Q11 overdue / coming / waiting | one list, good | — | split across "Overdue & next 21 days" and "Coming up"; provider name printed twice per row | live partly | — |
| Q19/Q20 provider: alive? when does it move? | "active · last activity Sep 27" + update | ✓ | "lawsuit filed" with no date and no update | live partly | — |

## 3. Screen budget
**Firm first screen: at most 5 blocks, ~180 words, ≤ 7 numbers in total (Miller), ≤ 10 click targets visible (Hick).**
| # | Block | The one question it answers | Max |
|---|---|---|---|
| 1 | Header: photo/initials, name, age/job, stage stepper, one meta line "Injured Apr 23 2023 · SOL met ✓ · last client call Sep 27 (5d)" | Who is this and where does the case stand? | 3 lines |
| 2 | **Bottom line** (BLUF, AI, cached): ① status now ② the blocker ③ what changed since last visit | What's going on, in one breath? | 3 sentences |
| 3 | **Do next**: overdue first, then the next 3; date · late tag · short title · ⏳ who | What do I do or chase now? | 5 rows, 1 line each |
| 4 | **Worth vs coverage**: $375k vs $100k/person, the 3.75× gap, specials $118,400 ✓ | Is the money there? (Q12) | 4 numbers |
| 5 | **Red flags**: 4 one-line titles, expand to evidence | Is anything wrong? | 4 lines |
Everything else goes to the 2-min layer: key events, specials by provider, injuries, treating providers, the **money detail**
(Medicaid lien, no-fault, UM/UIM, wage loss, firm spend) and the flag evidence text. The deep layer keeps "All entries".
The sync status moves into a footer/tooltip. Remove the wireframe banner in the app.

**Provider page (what the provider sees): at most 4 blocks, ~120 words.**
| # | Block | Question | Max |
|---|---|---|---|
| 1 | Status: "Case is active · lawsuit stage · last activity Sep 27" + stepper + "bills paid at settlement" | Is it alive, and when do I get paid? (Q19) | 3 lines |
| 2 | What we need from your office + "newest record we hold: Aug 15 2024" | What do they want from me? (Q22) | 3 items |
| 3 | Your bills on file: $14,220 · 130 lines · status | How much, and what for? | 2 lines |
| 4 | Latest update (approved) | What moved? (Q20) | 2 lines |
Second layer: Treatment, Records on file, shared documents. **Attorney controls never share the viewport with the preview:**
collapse them to one bar ("Sharing with Advanced Rockland: 6 of 7 on · Edit ▸ · Approve & share") that opens a drawer.

## 4. Cut / merge / move
**Cut**
- The since-strip counts ("8 notes · 15 emails/calls · 3 docs") and the attention-header counts ("2 overdue · 4 coming up · 4 waiting").
- The live tile "Treating providers 10". It is a count with no answer. (It also disagrees with the proto's "9 providers".)
- The header "Next deadline Oct 5". It is wrong as a priority while 2 items are overdue (38d, 6d), and it duplicates Do next.
- The visible type pills on every value: 42 on the proto first screen. Keep click-to-source as a dotted-underlined value
  (the `source_link` macro already exists) and show the type/date in the dialog. This still meets Q5/Q6.
- Provider proto: the 1·Choose 2·Preview 3·Approve 4·Receipts stepper. The Approve button carries the flow.
- Live: the Clio class names ("CustomFieldValue", "CalendarEntry", "Communication") as chip text. Use "Field", "Calendar", "Call".
- Live: the "By medical provider: <name> - " task prefix and the repeated "Waiting on <name>" line. Show the ⏳ tag once.
- Live provider page: raw filenames. Show "Chiropractic chart · 131 pp · Apr 2023" instead.

**Merge**
- Story card + since-strip + header date cluster → **Bottom line** (block 2). This removes the triplicates: "coverage confirmed"
  appears 3× on the proto first screen, "no surgery date" 2×, and the Oct 5 task 2×.
- The 3.75× red banner + the two Money heroes → one "worth vs coverage" line with the gap.
- Live: "Overdue & next 21 days" + "Coming up" → one **Do next** list.
- Live share page: 10 provider cards → one picker sorted by "has an open ask / overdue", plus one preview with inline toggles (spec §d already says this).

**Move**
- Money rows Medicaid lien, no-fault, UM/UIM, wage loss, firm spend → 2-min "Money detail", placed beside specials-by-provider.
- Flag evidence paragraphs → expand-on-click under each one-line flag title.
- Live: Providers & bills list → 2-min layer (sorted by $, $0 Capiola last or dropped).
- Live firm: the 3-column equal-card grid → one priority column (blocks 1–5) + a narrow right rail at most. The grid is what makes it read as Clio.

## 5. Three biggest wins for "digestible", ranked
1. **Add the Bottom line block and delete what it replaces** (story card, since-strip, header date cluster). This is the only
   change that removes "assembled by hand": 3 sentences give status, blocker and change. It also kills the triplicates.
2. **Enforce the 5-block / ~180-word budget**: Money drops to 4 numbers, flags become one-liners, pills become underlined
   values, and Do next shows 5 rows. Proto goes from 638 words, 42 pills and 11 dollar figures to roughly ≤ 200 words, 0 pills and ≤ 4 dollar figures.
3. **De-Clio the live app**: one priority column instead of 3 equal KPI cards; no count tile; one Do next list with human
   labels; and on sharing, a picker + preview instead of 60 checkboxes. The live provider preview needs only label cleanup and a last-activity date.
