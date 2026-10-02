# 90-second video: the whole pitch (no live presenting)

**Thesis (the one idea the video sells):** Slide 9 offered 23 asks. We didn't build 23. We built the ones that
**cost a firm money when they go wrong**, and built them properly:
1. **A stalled case nobody notices** → know the case in 90 seconds, starting with what's blocking it
2. **A fact nobody can check** → every line opens its source; red flags only when both quotes match the record word for word
3. **A provider left in the dark, or handed the whole file** → an attorney-approved page per provider; strategy is blocked on the server

**One story thread:** the McCulloch surgeon who is blocking the case on the firm page is the same provider we share
with. The firm half and the provider half read as one product, not two features.

## Script (~210 words · speak at ~2.5 words/s · CAPTION = on-screen text, the slide-9 quote in quotation marks)

| # | Time | On screen | Voice-over |
|---|---|---|---|
| 1 | 0–13 | **Asset: `plan/video/slide9-thesis.mp4`** (13 s). Slide 9 verbatim → shrinks, other quotes dim → card 1 + its 6 quotes (3.8 s) → card 2 + 2 quotes (6.3 s) → card 3 + 6 quotes (8.5 s) → "14 of 23 asks" + their "Build the ones you believe in" box (11 s) | (0–4) "Swans gave us twenty-three asks. We built for the three problems that cost a firm money: (4–6) a case that stalls, and nobody notices; (6–8.5) a fact nobody can check; (8.5–11) and a provider left in the dark, or handed the whole file." (11–13: let the "14 of 23" card land; no words) |
| 3 | 13–31 | Matters home (worst first) → click Sapini. Hold on header, 3 lines, BLOCKED banner. Click "11 updates since". CAPTION 1 (first 2 s): "Sapini · 3½ years · 162 Clio entries · 15 PDFs". CAPTION 2: "Get me up to speed… without me having to ask anyone." | "Open the case, and one screen tells you what happened, where it stands, and the biggest risk. Then what's actually stalling it: the surgeon owes a surgery date, thirty-eight days late. Back from two weeks off? Just the eleven updates since you last looked." |
| 4 | 31–49 | Click a source link (opens note/PDF). Then red flag "Conflicting accounts of collision mechanism" → Compare → both quotes → open source. CAPTION: "If a date is on screen, I need to see where it came from." | "Every line opens the note, email or PDF it came from. Our AI reads the whole file for contradictions, and only shows a red flag when both quotes match the records word for word. Here, two records describe the crash differently." |
| 5 | 49–74 | Providers table: McCulloch "Not shared" → Share → preview with "What the firm needs from your office" → hover a locked "never shared" row → Approve → open link → back: row reads "Shared · opened". CAPTION 1: "Is this case even still alive?" (from providers). CAPTION 2: "Let me adjust what the provider sees before I send it." | "Now the other side. That surgeon gets their own page: the case is alive, it's in litigation, and here's exactly what we need from your office. The attorney picks what each provider sees. Notes, strategy and case value can't be shared; the server blocks them. Approve, send a secure link, and see when they open it." |
| 6 | 74–90 | Okafor case: new brief, "Denial of prior neck problems" flag → Compare. End card: product name + "Read-only from Clio · any matter · AI cost per case: $X". CAPTION: "Don't digest the whole case with AI again every time someone opens it." | "Nothing is hardcoded. On a second case we wrote ourselves, it built a fresh brief and caught the contradiction we planted. Read-only from Clio. The AI runs once per update, not every time someone opens the case." |

**If over time:** drop "Back from two weeks off…" from beat 3, then "Here, two records describe the crash differently" from beat 4.
**Beat 1 asset:** `plan/video/slide9-thesis.mp4` (1080p, 13 s) + stills `still-*.png` for editors that prefer images. Built from the real PDF page
(`slide9.png`), so the quotes are verbatim; edit `slide9-thesis.html` (quote groups listed in its script) and re-run `render.py` to change it.
**Every number above is checked on the live app (14:55):** 38 days overdue (McCulloch), 11 updates since Sep 18, 7 red flags,
Okafor flag present. Sapini = 162 Clio entries (42 notes, 69 communications, 14 tasks, 17 calendar, 5 expenses, 15 docs; sapini-map §1).
**Kept out of the voice-over on purpose:** "bills exceed the policy": coverage $100k is `ASSUMED` in the app, not from Clio.
"300 entries" is the slide's number, not Sapini's. **$X**: fill from `uv run python -c "from app.core.llm import cost_report; print(cost_report())"`
after one clean run of one case (whole dev log so far = $1.00 for 130 calls across 3 matters, so one case is well under $1, API-equivalent Haiku 4.5 pricing).

## Why these, and not the rest (slide 9 → what we built). For the submission form (item 05) and any Q&A.

| Slide-9 ask | Status | Where / why |
|---|---|---|
| 1 Up to speed without asking · 3 "ten that matter" · 4 two minutes vs dig in | Built | First screen (3 lines, blocker, do-next, red flags) + "More detail" layer |
| 2 What changed since I last opened | Built | "Since you last looked", pick any date |
| 5 Where a date came from · 6 Click to open the source | Built | Every fact carries its Clio source (D-006) |
| 9 When did anyone last talk to the client | Built | Header "Last talked to client" |
| 10 Don't re-digest with AI every open | Built | AI runs per ingest, cached (`app/cache/`) |
| 11 Overdue / coming / waiting on someone | Built | Blocker banner + Do next ("Waiting on …") |
| 12 Worth and coverage | Built | Worth-vs-coverage bar (Sapini coverage `ASSUMED`) |
| 14 What we shared, was it opened · 15, 16, 17 share part of the case securely | Built | Share console, preview, approve, token link, view receipt, server-side firewall |
| 19 Is the case alive · 22 What does the firm need from my office | Built | Provider page: stage + requests |
| 18 Coverage · 21 Other providers' records · 23 Still showing up to treatment | Attorney opt-in, off by default | Money and others' records are the attorney's call (slide 10) |
| 8 Injuries buried in a 200-page scan | Partial | AI injury chips in the brief; no page-cited extraction from records (cut from V1) |
| 13 What has the firm already spent | Not shown | Firm costs are computed in `facts.py` but not on screen |
| 20 Tell me when the case moves | Not built | Needs outbound messages; every send needs approval (rule 6). Next step |
| 7 Client's picture | Not built | Low stakes; the brief opens with name, injuries, and stage instead |

**Prioritization rule, in one line for Q&A:** if getting it wrong loses money or trust (missed blocker, uncheckable fact,
leaked strategy), we built it end to end; if it's a convenience, it waited.

## Production: record so UI changes don't break the video
1. **Record the voice-over first**, now (the script doesn't depend on pixel layout). Phone voice memo in a quiet room, 2–3 takes, keep the best.
2. **Capture screen clips per beat after the UI freeze** (QuickTime: File › New Screen Recording, or Loom), silent, ~1.5× longer than needed.
3. Cut clips under the audio, add CAPTION text (iMovie / CapCut / Descript). Captions in the slide-9 quote style = the judges' own words answered.
4. Before capturing: McCulloch share reset to "Not shared" (so beat 5 shows it change live); AI results already generated for Sapini and
   Okafor; `APP_TODAY=2026-10-02`; browser zoom 110%, bookmarks bar hidden, Do Not Disturb on, no password prompt on screen.
5. Export 1080p, upload to Google Drive, "Anyone with the link can view", test in an incognito window.

Note: slide 18 says the Top 7 get 4 minutes in front of judges at 5:00. If we make it, the table above is the talk track.
