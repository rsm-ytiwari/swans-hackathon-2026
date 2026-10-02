# Sapini case map: Clio seed + case PDFs

Inventory only (no proposals). Built 2026-10-02 from `Sapini Case Materials/` (local, gitignored; the app must read
the matter from Clio, not from these files). **INFERRED** = our reading, not printed in the source. Part 1 covers the
Clio seed JSON + manual setup guide; Part 2 covers the 15 PDFs. Slides/transcript are in `slides-inventory.md`.

## Part 1: Clio seed JSON (`sapini-clio-data.json`) and setup guide

Inventory only: no proposals. Sources are `Sapini Case Materials/sapini-clio-data.json` (133,182 bytes) and `Sapini Case Materials/Sapini - manual setup guide.pdf` (30 pp, A4 landscape, created 2026-10-01). Anything I inferred is labelled **INFERRED**. Every number below comes from those two files or from a script whose command is shown.

**ID convention used here.** `N#`, `M#`, `C#`, `T#`, `X#`, `D#` are the **0-based index into the JSON `items` list** for notes, communications, calendar entries, tasks, expenses and documents. The setup guide numbers rows differently: 1-based and sorted by date. Section 13 gives the mapping.

**Date mechanism (from `about.dates`, verbatim):** "All dates are already resolved for Friday 2026-10-02. Date-only fields are YYYY-MM-DD; calendar entries and document received_at are UTC." So the JSON holds **absolute dates, not offsets**. Some prose still carries relative offsets such as "DOI + 94", "DOI + 1" and "DOI + 107", and those are never resolved into dates. **INFERRED:** the absolute dates look generated as round day offsets from the date of incident 2023-04-23, for example open date = DOI+14, SOL = DOI+1095, and many events at DOI+N×10 (see the DOI+days column in section 8). Where a note gives an offset, it agrees with the calendar: N6 "DOI + 94" is 2023-07-26, the same day as C2 (the surgery), and M15 "DOI + 80" is 2023-07-12, the same day as C1.

---

### 1. JSON structure (every section, sub-key, item count)

| Section | Sub-keys | Items |
|---|---|---|
| `about` | `what`, `api_base` (`https://app.clio.com/api/v4`), `request_shape` (bodies wrapped in `{"data": body}`), `placeholders` (dict, 9 keys: `rule`, `{{user_id}}`, `{{practice_area_id}}`, `{{stage:<name>}}`, `{{field:<name>}}`, `{{contact:<ref>}}`, `{{matter_id}}`, `{{folder:<name>}}`, `{{calendar_id}}`), `dates`, `rate_limit` ("600 requests per minute per token. The whole matter is about 230 requests plus 85 MB of uploads."), `oauth_scopes_needed` | 7 keys |
| `matter_stages` | `manual_step` (true), `why` (API cannot create stages), `where`, `stages_in_order` (list), `sapini_stage` | 8 stages |
| `custom_fields` | `endpoint` (POST /custom_fields.json), `items[].body{name,parent_type,field_type,displayed}` | 16 |
| `contacts` | `endpoint`, `note`, `items[]{ref, body}` | 10 |
| `matter` | `endpoint` (POST /matters.json), `note`, `body{client, description, status, open_date, statute_of_limitations, practice_area, matter_stage, custom_field_values[16]}` | 1 matter, 16 CF values |
| `relationships` | `endpoint`, `items[].body{matter, contact, description}` | 9 |
| `folders` | `endpoint`, `note`, `items[].body{name, parent{id,type}}` | 9 |
| `documents` | `how` (3 steps: POST, PUT bytes to put_url, PATCH fully_uploaded), `files_location`, `items[]{local_path, bytes, sha256, body{name, parent, received_at}}` | 15 |
| `notes` | `endpoint`, `items[].body{type ("Matter"), date, subject, detail, matter}` | 42 |
| `communications` | `endpoint`, `items[].body{type (EmailCommunication/PhoneCommunication), date, subject, body, senders[], receivers[], matter}` | 69 (56 EmailCommunication, 13 PhoneCommunication) |
| `tasks` | `endpoint`, `items[].body{name, description, due_at, status, matter, assignee, [statute_of_limitations]}` | 14 |
| `calendar_entries` | `endpoint`, `items[].body{summary, description, start_at, end_at, matter, calendar_owner}` | 17 |
| `expenses` | `endpoint` (POST /activities.json), `items[].body{type "ExpenseEntry", date, quantity, price, matter, user, note, tax_setting}` | 5 |

Totals agree with the guide cover page: 16 custom fields, 10 contacts, 42 notes, 69 communications, 14 tasks, 17 calendar entries, 5 expenses, 15 documents.

### 2. Custom fields (16): definition and value on the matter

All 16 fields have `parent_type: Matter` and `displayed: true`. None has picklist options; there are no picklist fields.

| # | Name | field_type | Value on matter |
|---|---|---|---|
| F1 | Date of Incident | date | `2023-04-23` |
| F2 | Accident Location | text_line | Cedar Street at its intersection with Garden Street, New Rochelle, Westchester County, NY |
| F3 | Case Summary | text_area | Sideswiped by a Metro-North utility vehicle on Cedar Street, New Rochelle. Both shoulders, both knees, and a head injury. |
| F4 | Insurance Carrier | text_line | Metro-North Commuter Railroad, SELF-INSURED. Claims administered by Claims Service Bureau. Client's own no-fault: Progressive Insurance Company, P.O. Box 2930, Clinton, IA 52733. |
| F5 | Claim Number | text_line | SIR068120 (Metro-North / Claims Service Bureau) |
| F6 | Policy Limits | text_area | "Defendant liability: $100,000 / $300,000\nClient UM/UIM: $25,000 / $50,000\nNo-fault: $50,000" |
| F7 | Policy Limits Confirmed | checkbox | `true` |
| F8 | Estimated Case Value | currency | `375000.0` **(STRATEGY)** |
| F9 | Case Value Rationale | text_area | "Economics alone come to $332,400: $118,400 in specials and $214,000 claimed in wage loss… The case is worth more than the coverage. We are capped at the $100,000 defendant limit and the Medicaid lien of $22,180.00 comes off whatever we recover." **(STRATEGY)** |
| F10 | Medical Specials To Date | currency | `118400.0` |
| F11 | Wage Loss Claimed | text_area | "$214,000.00 claimed to date. Financial advisor, Northwestern Mutual, 875 Third Avenue, New York NY 10022. Commission-only… Figure is from the client's own 2022 1099; no economic expert retained." (last clause is **STRATEGY**-adjacent) |
| F12 | Liability Assessment | text_area | "Contested on two independent levels, neither investigated." **(STRATEGY)** |
| F13 | Treatment Status | text_area | "Active and ongoing, over three years post-loss. Never discharged, no MMI declared." |
| F14 | Health Insurance or Lien Holder | text_area | "New York State Medicaid lien, $22,180.00 asserted. Progressive no-fault: $50,000 basic economic loss exhausted, which under Insurance Law 5104(a) is not recoverable from the tortfeasor. Social Security Disability claim filed and pending. Defendants pleaded CPLR 4545 collateral source." |
| F15 | Prior Related Injuries | text_area | "Denied by the client, contradicted by his own paperwork." **(STRATEGY)** |
| F16 | HIPAA Authorization Received | checkbox | `true` |

Arithmetic check: 118,400 + 214,000 = 332,400, which matches F9.

### 3. Matter record (every field)

| Field | Value |
|---|---|
| client | `{{contact:client}}` (Justin Sapini) |
| description | "Sapini, Justin — MVA (Cedar St & Garden St, New Rochelle)" |
| status | Open |
| open_date | 2023-05-07 |
| statute_of_limitations | 2026-04-22 |
| practice_area | `{{practice_area_id}}` (Personal Injury) |
| matter_stage | `{{stage:Litigation}}` |
| custom_field_values | 16 entries (section 2) |
| endpoint note | "matter_stage must be sent together with practice_area, or Clio answers 422." |

The guide adds one item not in the JSON: "Responsible / originating attorney: Leave as you, or whoever is on the account" (p6).

### 4. Contacts (10) and relationships (9)

| ref | Type | Name | Role (from relationships) | Key contact fields |
|---|---|---|---|---|
| client | Person | Mr. Justin Sapini | Matter client (not a related contact) | company Northwestern Mutual; DOB 1995-12-21; email jsapini.tx@mailbox.test; phone (845) 358-2214; address Cypress, TX 77433 |
| ferrara | Person | Anthony Ferrara | "Adverse driver" | address only (Brookfield, CT); no email or phone |
| metronorth | Company | Metro-North Commuter Railroad | "Adverse party, self-insured public authority" | claims@mnr-railroad.test; New York, NY |
| csb | Company | Claims Service Bureau | "Third-party claims administrator for Metro-North" | adjusters@claimsservicebureau.test; c/o D&D Associates, Garden City, NY |
| progressive | Company | Progressive Insurance Company | "No-fault carrier, client's own policy" | nofault.ny@progressive-claims.test; Clinton, IA |
| montefiore | Company | Montefiore Nyack Hospital | "Hospital, emergency care DOI + 1" | him@montefiorenyack.test; Nyack, NY |
| mcculloch | Company | McCulloch Orthopaedic Surgical Services, PLLC | "Treating provider, orthopaedic surgery" | records@mccullochortho.test; Bronx, NY |
| capiola | Person | Dr. David Capiola (company McCulloch) | "Treating orthopaedic surgeon, left shoulder arthroscopy" | dcapiola@mccullochortho.test; New Rochelle, NY |
| rocklandchiro | Company | Advanced Rockland Chiropractic Offices, P.C. | "Treating provider, chiropractic (Kevin M. Haggerty, D.C.)" | records@advancedrocklandchiro.test; Spring Valley, NY |
| sportscare | Company | SportsCare Physical Therapy of New York | "Treating provider, physical therapy" | records@sportscareny.test; Nanuet, NY |

By role:
- **Client:** 1.
- **Medical providers:** 5 (Montefiore, McCulloch, Capiola, Rockland Chiro, SportsCare).
- **Insurers and adjusters:** 2. Progressive is the no-fault carrier. CSB is a TPA, not a carrier, and **no named adjuster** appears anywhere.
- **Adverse parties:** 2 (Ferrara, Metro-North).
- **Defense counsel:** **none.** N32 mentions "Defence counsel" but there is no contact, and M54 says CSB "referred the question to counsel".
- **Court or judge:** **none.** D11 "letter-to-judge" exists, but no judge or court contact is defined.
- **Experts:** **none** as contacts. Dr. Emmanuel Hostin (ortho IME), Dr. Jack W. Tsao (neuro IME) and Dr. Katzman (radiology) appear only in text and file names.

People and entities named only in prose, with no contact record: Kevin M. Haggerty, D.C. (in the relationship text only); Kyle Pullano (Metro-North witness, D8 subpoena); New Horizon Surgical Center (Paterson NJ); Hudson Valley Radiology / Mid Rockland (imaging); Abramov and Kwan (physiatry and neurology); Ludena (PT); Nicole Kosuda, P.A.; Kenneth Blumberg M.D. (2011 X-ray); S. Alvarez (paralegal, N0); New York State Medicaid lien unit; SSA. The no-fault claim number `22-4471102` appears only in M20 and M22. The Montefiore account `4471-SAPINI` appears only in M11 and M28.

**INFERRED oddity:** the client's address is Cypress, TX and his email handle is ".tx", but his phone is a (845) area code and he attends weekly treatment in Rockland County, NY (C14–C16, M52).

**Communications counterparties:** every one of the 69 communications has `{{user_id}}` on one side. The other sides are the client, CSB, McCulloch, Rockland Chiro, SportsCare, Montefiore and Progressive. No communication goes to or from Metro-North, Ferrara, Capiola or any defense counsel. CSB acts as the defense discovery counterparty in M41, M59, M61 and M66 (M41 calls it "Your client"). **INFERRED:** CSB stands in for defense counsel in this dataset.

### 5. Matter stages (ordered) and current stage

1 Intake → 2 Treatment → 3 Demand → 4 Negotiation → 5 **Litigation (current, `sapini_stage`)** → 6 Trial → 7 Disbursement → 8 Closed.

These are a manual step: the "Clio API cannot create matter stages; every write to /matter_stages.json is refused". They must be created under the Personal Injury practice area, or the matter create fails with 422.

### 6. Folders (9)

01 Intake and Retainer (2 docs) · 02 Pleadings (4) · 03 Discovery (3) · 04 Medical Records (1) · 05 Medical Bills and Liens (1) · 06 Correspondence (1) · **07 Insurance (0)** · 08 Experts (3) · **09 Settlement (0)**.

The JSON note says: "07 Insurance and 09 Settlement stay empty on Sapini; create them anyway." N1 explains why 07 is empty: self-insured, "no declarations page to request".

### 7. Documents (15) with sha256 verification

Command (run from `Sapini Case Materials/`): a Python loop calling `shasum -a 256 <local_path>` and `os.path.getsize` for each `documents.items[]`, then walking `Sapini documents/` for unreferenced files.

| D# | Folder | name (= file name) | received_at (UTC) | bytes | sha256 (first 12) | Result |
|---|---|---|---|---|---|---|
| D0 | 01 Intake and Retainer | 01-intake__created__hipaa-authorization.pdf | 2023-05-14T10:00Z | 3,607 | bec45b4220c9 | MATCH, bytes match |
| D1 | 01 Intake and Retainer | 01-intake__created__photo-id.pdf | 2023-05-07T10:00Z | 46,937 | 38e54578b6ee | MATCH, bytes match |
| D2 | 02 Pleadings | 02-pleadings__doc-01__summons-complaint.pdf | 2024-03-08T10:00Z | 1,043,948 | 60c007036b61 | MATCH, bytes match |
| D3 | 02 Pleadings | 02-pleadings__doc-05__verified-answer-demands.pdf | 2024-04-17T10:00Z | 757,118 | 312e76a49a9a | MATCH, bytes match |
| D4 | 02 Pleadings | 02-pleadings__doc-07__bill-of-particulars.pdf | 2024-05-27T10:00Z | 562,026 | 1011afe0cc8d | MATCH, bytes match |
| D5 | 02 Pleadings | 02-pleadings__doc-41__bop-affirmative-defenses.pdf | 2024-06-26T10:00Z | 112,381 | 8ec38780c6a3 | MATCH, bytes match |
| D6 | 03 Discovery | 03-discovery__doc-08__response-discovery-demands.pdf | 2024-05-07T10:00Z | 445,350 | 6260e870e40a | MATCH, bytes match |
| D7 | 03 Discovery | 03-discovery__doc-40__defendants-response-demand.pdf | 2024-11-03T10:00Z | 1,144,399 | 74616933f985 | MATCH, bytes match |
| D8 | 03 Discovery | 03-discovery__doc-43__subpoena-kyle-pullano.pdf | 2025-01-02T10:00Z | 229,494 | 01aac1e8018c | MATCH, bytes match |
| D9 | 04 Medical Records | 04-medical-records__doc-19__records-bundle-part1-haggerty-imaging.pdf | 2025-03-23T10:00Z | 42,107,788 | 8b7b02e3c198 | MATCH, bytes match |
| D10 | 05 Medical Bills and Liens | 05-medical-bills__doc-20__records-and-bills-part2-pt-ortho-er-operative.pdf | 2025-03-23T10:00Z | 34,179,576 | 84c55c91f370 | MATCH, bytes match |
| D11 | 06 Correspondence | 06-correspondence__doc-12__letter-to-judge.pdf | 2024-09-24T10:00Z | 136,412 | e2e35fc80058 | MATCH, bytes match |
| D12 | 08 Experts | 08-experts__doc-47__radiology-review-katzman.pdf | 2026-09-22T10:00Z | 733,553 | c68a6bb9a213 | MATCH, bytes match |
| D13 | 08 Experts | 08-experts__doc-55__expert-exchange-neuro-tsao.pdf | 2026-09-20T10:00Z | 2,801,219 | 8d1e7311174d | MATCH, bytes match |
| D14 | 08 Experts | 08-experts__doc-56__ime-orthopedic-hostin.pdf | 2026-09-14T10:00Z | 776,965 | 027581b60b97 | MATCH, bytes match |

**Result: 15/15 MATCH. 0 mismatch, 0 with no local file, 0 with no hash.** The only unreferenced local file is `Sapini documents/.DS_Store` (macOS metadata). There is also a sibling `Sapini Case Materials/_ocr/` directory, which is not referenced by the JSON (made by another agent; out of scope here).

Every document body also has `parent {id: {{folder:<name>}}, type: Folder}`; there are no other body fields. The guide (p6) explains the file names: "doc-19 = court docket document 19 … 'created' in place of a docket number means the firm made it (HIPAA form, photo ID)". Docket numbers present: 01, 05, 07, 08, 12, 19, 20, 40, 41, 43, 47, 55, 56.

### 8. Chronological skeleton

- **Accident (DOI):** 2023-04-23 (Sun), from `matter.custom_field_values[Date of Incident]`. N0: about 8:30 a.m., southbound Cedar St, New Rochelle.
- **SOL:** `matter.statute_of_limitations` = **2026-04-22** (cited field). It is also T0 (`statute_of_limitations: true`, status complete) and C8 ("LIMITATIONS DATE… Three-year statute of limitations expires").
  - **INFERRED check:** DOI + 3 calendar years = 2026-04-23, but the field is 2026-04-22. 2026-04-22 − 2023-04-23 = **1095 days** (= 3 × 365; the period spans 2024-02-29), so the field looks computed as DOI + 1095 days rather than as three calendar years.
  - The JSON also states a *different* governing rule without a number. N22: "a notice of claim and the shortened period against a public benefit corporation, not the ordinary three years". T0: "Three-year statute of limitations, and the shortened period applicable to a claim against a public benefit corporation. Satisfied: the notice of claim was served and suit commenced within time." The length of the shortened period, the Presentation of Claim service date and the notice of claim date are **not present** in the JSON.
- **Today, 2026-10-02:** the SOL date is 163 days in the past and marked satisfied. No pending item is due today.

Timeline: every dated item (notes, communications, calendar, tasks, documents, expenses, plus matter dates), sorted. Generated by `python3 <session-scratchpad>/gen.py` (sums/sorts the JSON; not committed). The DOI+days column = date − 2023-04-23.

165 events
| date | wkday | DOI+days | source | event |
|---|---|---|---|---|
| 2023-04-23 | Sun | 0 | matter.custom_field_values[Date of Incident] | Date of incident (accident), Cedar St at Garden St, New Rochelle |
| 2023-05-07 | Sun | 14 | calendar_entries[0] (C0) | Initial client consultation, Justin Sapini (10:00-10:45Z) |
| 2023-05-07 | Sun | 14 | communications[0] (M0) | Email: Photographs of my paperwork |
| 2023-05-07 | Sun | 14 | documents[1] (D1) received_at | 01-intake__created__photo-id.pdf |
| 2023-05-07 | Sun | 14 | matter.open_date | Matter open date |
| 2023-05-07 | Sun | 14 | notes[0] (N0) | Intake summary |
| 2023-05-08 | Mon | 15 | communications[1] (M1) | Email: Retainer agreement and HIPAA authorization |
| 2023-05-09 | Tue | 16 | notes[22] (N22) | File opened and claim set up |
| 2023-05-11 | Thu | 18 | communications[2] (M2) | Phone: Intake follow-up: employment and treatment |
| 2023-05-14 | Sun | 21 | communications[3] (M3) | Email: Signed retainer and HIPAA returned |
| 2023-05-14 | Sun | 21 | documents[0] (D0) received_at | 01-intake__created__hipaa-authorization.pdf |
| 2023-05-14 | Sun | 21 | notes[1] (N1) | Coverage note: Metro-North is self-insured |
| 2023-05-14 | Sun | 21 | tasks[9] (T9) due | Serve letter of representation on Claims Service Bureau [complete] |
| 2023-05-15 | Mon | 22 | communications[4] (M4) | Email: Letter of representation, claim SIR068120 |
| 2023-05-18 | Thu | 25 | notes[23] (N23) | Treatment commenced |
| 2023-05-22 | Mon | 29 | communications[5] (M5) | Email: RE: Letter of representation, claim SIR068120 |
| 2023-05-23 | Tue | 30 | notes[2] (N2) | Mechanism: the client has given three different accounts |
| 2023-05-31 | Wed | 38 | notes[3] (N3) | Prior injury discrepancy: left ankle |
| 2023-06-02 | Fri | 40 | communications[6] (M6) | Email: HIPAA authorization, claim SIR068120 |
| 2023-06-02 | Fri | 40 | tasks[10] (T10) due | Catalogue client's own document stack [complete] |
| 2023-06-07 | Wed | 45 | notes[4] (N4) | Scope of employment is the whole case |
| 2023-06-22 | Thu | 60 | communications[7] (M7) | Email: Records request: Justin Sapini, Dr. Capiola file |
| 2023-06-28 | Wed | 66 | communications[8] (M8) | Email: Records request: Justin Sapini, chiropractic file |
| 2023-07-04 | Tue | 72 | communications[9] (M9) | Email: Records request: Justin Sapini, physical therapy file |
| 2023-07-12 | Wed | 80 | calendar_entries[1] (C1) | Pre-operative consultation, Dr. Capiola (09:30-10:30Z) |
| 2023-07-12 | Wed | 80 | communications[15] (M15) | Phone: Pre-operative scheduling, left shoulder |
| 2023-07-12 | Wed | 80 | notes[5] (N5) | Left shoulder surgery authorised |
| 2023-07-20 | Thu | 88 | communications[16] (M16) | Email: Surgical date confirmed, left shoulder |
| 2023-07-26 | Wed | 94 | calendar_entries[2] (C2) | Left shoulder arthroscopy, New Horizon Surgical Center (07:30-11:30Z) |
| 2023-07-27 | Thu | 95 | communications[10] (M10) | Email: Records request: emergency department chart |
| 2023-07-28 | Fri | 96 | communications[17] (M17) | Phone: Post-surgery check-in with client |
| 2023-08-01 | Tue | 100 | communications[18] (M18) | Email: Request: operative report, left shoulder |
| 2023-08-01 | Tue | 100 | notes[6] (N6) | Post-operative: left shoulder arthroscopy performed |
| 2023-08-01 | Tue | 100 | tasks[8] (T8) due | Request operative report, left shoulder [complete] |
| 2023-08-11 | Fri | 110 | communications[19] (M19) | Email: Operative report enclosed |
| 2023-08-21 | Mon | 120 | communications[11] (M11) | Email: Invoice for medical records, account 4471-SAPINI |
| 2023-08-31 | Thu | 130 | calendar_entries[3] (C3) | Post-operative follow-up, Dr. Capiola (11:00-11:45Z) |
| 2023-08-31 | Thu | 130 | communications[12] (M12) | Email: Records enclosed: Sapini, orthopaedic file and operative report |
| 2023-08-31 | Thu | 130 | expenses[1] (X1) | $65.00 Records reproduction: McCulloch Orthopaedic records copy, including the left shoulder operative report. |
| 2023-08-31 | Thu | 130 | notes[7] (N7) | Records received: McCulloch Orthopaedic (Dr. Capiola) |
| 2023-09-20 | Wed | 150 | notes[8] (N8) | Imaging summary: ten studies |
| 2023-10-20 | Fri | 180 | communications[13] (M13) | Email: Records enclosed: Sapini, chiropractic file |
| 2023-10-20 | Fri | 180 | notes[9] (N9) | Records received: Advanced Rockland Chiropractic (Haggerty) |
| 2023-11-09 | Thu | 200 | expenses[0] (X0) | $85.00 Records reproduction: Montefiore Nyack emergency department chart reproduction. |
| 2023-11-09 | Thu | 200 | tasks[7] (T7) due | Pay Montefiore Nyack records invoice and re-request [complete] |
| 2023-11-19 | Sun | 210 | communications[14] (M14) | Email: Records enclosed: Sapini, physical therapy file |
| 2023-11-19 | Sun | 210 | notes[10] (N10) | Records received: SportsCare Physical Therapy (Ludena) |
| 2023-11-29 | Wed | 220 | expenses[3] (X3) | $450.00 Records reproduction: Reproduction and imaging copy charges for the remaining treating providers and the ten imaging studies. |
| 2023-11-29 | Wed | 220 | notes[24] (N24) | Records collection: what we hold and what is missing |
| 2023-12-19 | Tue | 240 | communications[20] (M20) | Email: No-fault benefits exhausted, claim 22-4471102 |
| 2023-12-29 | Fri | 250 | communications[21] (M21) | Email: Request for no-fault payment ledger |
| 2024-01-08 | Mon | 260 | notes[11] (N11) | No-fault exhausted |
| 2024-01-13 | Sat | 265 | communications[22] (M22) | Email: No-fault payment ledger enclosed |
| 2024-02-17 | Sat | 300 | communications[23] (M23) | Email: Medicaid coverage and what a lien means |
| 2024-02-17 | Sat | 300 | notes[12] (N12) | Specials tally to date: $118,400.00 |
| 2024-03-08 | Fri | 320 | documents[2] (D2) received_at | 02-pleadings__doc-01__summons-complaint.pdf |
| 2024-03-28 | Thu | 340 | communications[24] (M24) | Email: Social Security Disability filing acknowledged |
| 2024-03-28 | Thu | 340 | notes[13] (N13) | Lien and collateral source position |
| 2024-03-28 | Thu | 340 | tasks[13] (T13) due | File Medicaid lien acknowledgment [complete] |
| 2024-04-07 | Sun | 350 | communications[25] (M25) | Email: Updated records and itemised bill to date |
| 2024-04-12 | Fri | 355 | communications[40] (M40) | Email: Demand package, claim SIR068120 |
| 2024-04-12 | Fri | 355 | notes[14] (N14) | Demand package served on Claims Service Bureau |
| 2024-04-17 | Wed | 360 | documents[3] (D3) received_at | 02-pleadings__doc-05__verified-answer-demands.pdf |
| 2024-04-29 | Mon | 372 | notes[15] (N15) | Adjuster response: negotiations opened |
| 2024-05-07 | Tue | 380 | documents[6] (D6) received_at | 03-discovery__doc-08__response-discovery-demands.pdf |
| 2024-05-27 | Mon | 400 | calendar_entries[4] (C4) | Consultation re second surgery, right shoulder (14:00-14:45Z) |
| 2024-05-27 | Mon | 400 | communications[26] (M26) | Email: Request for updated treatment notes |
| 2024-05-27 | Mon | 400 | documents[4] (D4) received_at | 02-pleadings__doc-07__bill-of-particulars.pdf |
| 2024-05-27 | Mon | 400 | notes[16] (N16) | Second surgery recommended: right shoulder |
| 2024-06-26 | Wed | 430 | documents[5] (D5) received_at | 02-pleadings__doc-41__bop-affirmative-defenses.pdf |
| 2024-07-21 | Sun | 455 | expenses[4] (X4) | $210.00 Court filing: Summons and complaint filing, New York County index 160000/2024. |
| 2024-08-15 | Thu | 480 | communications[27] (M27) | Email: Updated chiropractic notes enclosed |
| 2024-09-24 | Tue | 520 | documents[11] (D11) received_at | 06-correspondence__doc-12__letter-to-judge.pdf |
| 2024-10-07 | Mon | 533 | communications[65] (M65) | Phone: Post-operative check-in with the client |
| 2024-10-19 | Sat | 545 | notes[38] (N38) | Discovery served both ways |
| 2024-11-03 | Sun | 560 | documents[7] (D7) received_at | 03-discovery__doc-40__defendants-response-demand.pdf |
| 2024-11-18 | Mon | 575 | communications[66] (M66) | Email: Notice to produce and combined demands |
| 2025-01-02 | Thu | 620 | documents[8] (D8) received_at | 03-discovery__doc-43__subpoena-kyle-pullano.pdf |
| 2025-01-10 | Fri | 628 | communications[67] (M67) | Email: No-fault benefits exhausted |
| 2025-02-16 | Sun | 665 | notes[39] (N39) | Records production to defence |
| 2025-03-01 | Sat | 678 | communications[68] (M68) | Email: Medicaid lien notice |
| 2025-03-18 | Tue | 695 | notes[40] (N40) | Client is still out of work |
| 2025-03-23 | Sun | 700 | documents[10] (D10) received_at | 05-medical-bills__doc-20__records-and-bills-part2-pt-ortho-er-operative.pdf |
| 2025-03-23 | Sun | 700 | documents[9] (D9) received_at | 04-medical-records__doc-19__records-bundle-part1-haggerty-imaging.pdf |
| 2025-04-08 | Tue | 716 | communications[52] (M52) | Email: Checking in: still going to therapy |
| 2025-04-15 | Tue | 723 | calendar_entries[12] (C12) | Compliance conference (10:00-10:45Z) |
| 2025-04-22 | Tue | 730 | notes[29] (N29) | Two years on, still treating |
| 2025-05-07 | Wed | 745 | communications[53] (M53) | Email: Records request: updated physical therapy ledger |
| 2025-05-24 | Sat | 762 | communications[54] (M54) | Phone: Call to Claims Service Bureau re scope of employment |
| 2025-06-12 | Thu | 781 | notes[30] (N30) | Discovery status |
| 2025-07-09 | Wed | 808 | communications[55] (M55) | Phone: Call from the client re the second surgery |
| 2025-07-23 | Wed | 822 | notes[31] (N31) | Medicaid lien |
| 2025-08-10 | Sun | 840 | communications[56] (M56) | Email: Records request: updated chiropractic ledger |
| 2025-08-27 | Wed | 857 | notes[32] (N32) | Deposition scheduling |
| 2025-09-14 | Sun | 875 | communications[57] (M57) | Email: Social Security Disability claim status |
| 2025-10-09 | Thu | 900 | calendar_entries[13] (C13) | Client appointment: treatment and surgery decision (14:00-14:30Z) |
| 2025-10-09 | Thu | 900 | communications[58] (M58) | Phone: Client check-in |
| 2025-10-24 | Fri | 915 | notes[33] (N33) | Capiola follow-up: surgery still recommended |
| 2025-11-13 | Thu | 935 | communications[59] (M59) | Email: Defendants supplemental demand for authorizations |
| 2025-12-06 | Sat | 958 | communications[28] (M28) | Email: Second request: itemised bill, account 4471-SAPINI |
| 2025-12-08 | Mon | 960 | notes[34] (N34) | Specials tally, interim |
| 2025-12-23 | Tue | 975 | communications[60] (M60) | Email: Year-end check-in |
| 2026-01-12 | Mon | 995 | notes[35] (N35) | Case posture at the turn of the year |
| 2026-01-29 | Thu | 1012 | communications[61] (M61) | Email: Compliance conference date |
| 2026-02-16 | Mon | 1030 | communications[62] (M62) | Phone: Call to the client ahead of the conference |
| 2026-03-06 | Fri | 1048 | notes[36] (N36) | Compliance conference |
| 2026-03-23 | Mon | 1065 | communications[63] (M63) | Email: Records chaser: physical therapy |
| 2026-04-22 | Wed | 1095 | calendar_entries[8] (C8) | LIMITATIONS DATE: Sapini (09:00-09:30Z) |
| 2026-04-22 | Wed | 1095 | matter.statute_of_limitations | SOL date field |
| 2026-04-22 | Wed | 1095 | tasks[0] (T0) due | Limitations Date [complete] |
| 2026-05-05 | Tue | 1108 | communications[29] (M29) | Email: Third request: updated treatment notes |
| 2026-05-05 | Tue | 1108 | communications[30] (M30) | Email: Right shoulder arthroscopy: requesting a date |
| 2026-06-04 | Thu | 1138 | notes[17] (N17) | Case evaluation |
| 2026-06-14 | Sun | 1148 | communications[31] (M31) | Phone: Call to scheduling re right shoulder date |
| 2026-07-04 | Sat | 1168 | communications[32] (M32) | Email: Second request: right shoulder surgical date |
| 2026-07-04 | Sat | 1168 | notes[18] (N18) | Right shoulder surgery still has no date |
| 2026-08-03 | Mon | 1198 | communications[33] (M33) | Email: Third request: right shoulder surgical date |
| 2026-08-03 | Mon | 1198 | communications[35] (M35) | Email: IME notice: orthopaedic examination |
| 2026-08-03 | Mon | 1198 | notes[19] (N19) | Demand history and current damages update |
| 2026-08-18 | Tue | 1213 | communications[36] (M36) | Email: IME notice: neurological examination |
| 2026-08-23 | Sun | 1218 | communications[34] (M34) | Email: Claim SIR068120: file review |
| 2026-08-25 | Tue | 1220 | tasks[1] (T1) due | By medical provider: McCulloch Orthopaedic Surgical Services, PLLC - Updated records and right shoulder surgical date [pending] |
| 2026-09-02 | Wed | 1228 | calendar_entries[5] (C5) | Orthopedic IME, Dr. Emmanuel Hostin (13:00-14:30Z) |
| 2026-09-02 | Wed | 1228 | notes[20] (N20) | Defence independent medical examinations attended |
| 2026-09-02 | Wed | 1228 | tasks[11] (T11) due | Attend orthopedic IME with client [complete] |
| 2026-09-03 | Thu | 1229 | expenses[2] (X2) | $600.00 IME observer: Observer attendance at the two completed defence medical examinations; this is the plaintiff firm observer cost, not payment for the defence reports. |
| 2026-09-05 | Sat | 1231 | communications[41] (M41) | Email: Discovery status and outstanding demands |
| 2026-09-06 | Sun | 1232 | notes[25] (N25) | Discovery is stuck on the maintenance records |
| 2026-09-07 | Mon | 1233 | calendar_entries[6] (C6) | Neurological IME, Dr. Jack W. Tsao (10:00-11:30Z) |
| 2026-09-07 | Mon | 1233 | communications[37] (M37) | Phone: IME watchdog booking confirmed |
| 2026-09-07 | Mon | 1233 | tasks[12] (T12) due | Attend neurological IME with client [complete] |
| 2026-09-08 | Tue | 1234 | communications[42] (M42) | Email: RE: Discovery status and outstanding demands |
| 2026-09-08 | Tue | 1234 | communications[64] (M64) | Email: RE: Coverage confirmation, claim SIR068120 |
| 2026-09-09 | Wed | 1235 | notes[37] (N37) | Coverage confirmed in writing |
| 2026-09-10 | Thu | 1236 | communications[43] (M43) | Email: Compliance conference: proposed dates |
| 2026-09-12 | Sat | 1238 | communications[44] (M44) | Phone: Client call: the IME examinations |
| 2026-09-13 | Sun | 1239 | notes[26] (N26) | Both defence examinations attended, reports now served |
| 2026-09-14 | Mon | 1240 | communications[45] (M45) | Email: IME report served: orthopaedic examination |
| 2026-09-14 | Mon | 1240 | documents[14] (D14) received_at | 08-experts__doc-56__ime-orthopedic-hostin.pdf |
| 2026-09-15 | Tue | 1241 | notes[41] (N41) | Case posture, and what is still not done |
| 2026-09-17 | Thu | 1243 | communications[46] (M46) | Email: Chaser: right shoulder surgical date |
| 2026-09-18 | Fri | 1244 | notes[27] (N27) | The second surgery is now the biggest open question on this file |
| 2026-09-20 | Sun | 1246 | communications[47] (M47) | Email: Expert exchange served: neurology |
| 2026-09-20 | Sun | 1246 | documents[13] (D13) received_at | 08-experts__doc-55__expert-exchange-neuro-tsao.pdf |
| 2026-09-21 | Mon | 1247 | communications[38] (M38) | Email: Updated employment and commission records |
| 2026-09-22 | Tue | 1248 | communications[48] (M48) | Email: Radiology review served |
| 2026-09-22 | Tue | 1248 | documents[12] (D12) received_at | 08-experts__doc-47__radiology-review-katzman.pdf |
| 2026-09-24 | Thu | 1250 | communications[49] (M49) | Email: RE: Chaser: right shoulder surgical date |
| 2026-09-25 | Fri | 1251 | communications[51] (M51) | Phone: Call to the client re the second surgery |
| 2026-09-25 | Fri | 1251 | notes[28] (N28) | Specials cannot be closed while two ledgers are unreconciled |
| 2026-09-26 | Sat | 1252 | communications[50] (M50) | Email: Updated ledger request: chiropractic |
| 2026-09-26 | Sat | 1252 | tasks[5] (T5) due | Obtain updated employment and commission records from client [pending] |
| 2026-09-27 | Sun | 1253 | communications[39] (M39) | Phone: Client call: should he keep going to PT |
| 2026-09-27 | Sun | 1253 | notes[21] (N21) | Client call: treatment status |
| 2026-10-05 **(FUTURE)** | Mon | 1261 | tasks[4] (T4) due | Reconcile chiropractic and PT ledgers against CPT lines [pending] |
| 2026-10-07 **(FUTURE)** | Wed | 1263 | tasks[2] (T2) due | By medical provider: Advanced Rockland Chiropractic Offices, P.C. - Current daily notes and itemised bill to date [pending] |
| 2026-10-09 **(FUTURE)** | Fri | 1265 | calendar_entries[15] (C15) | Client treatment: chiropractic, Advanced Rockland Chiropractic Offices, P.C. (17:30-18:00Z) |
| 2026-10-10 **(FUTURE)** | Sat | 1266 | calendar_entries[14] (C14) | Client treatment: physical therapy, SportsCare Physical Therapy of New York (09:00-09:45Z) |
| 2026-10-10 **(FUTURE)** | Sat | 1266 | calendar_entries[9] (C9) | Call to McCulloch Orthopaedic re right shoulder surgical date (10:30-10:45Z) |
| 2026-10-10 **(FUTURE)** | Sat | 1266 | tasks[6] (T6) due | Confirm date of right shoulder arthroscopy with Dr. Capiola's office [pending] |
| 2026-10-14 **(FUTURE)** | Wed | 1270 | calendar_entries[7] (C7) | Follow-up call with client re treatment status (15:00-15:30Z) |
| 2026-10-14 **(FUTURE)** | Wed | 1270 | tasks[3] (T3) due | By medical provider: SportsCare Physical Therapy of New York - Ongoing treatment notes [pending] |
| 2026-10-17 **(FUTURE)** | Sat | 1273 | calendar_entries[16] (C16) | Client treatment: physical therapy (following week), SportsCare Physical Therapy of New York (09:00-09:45Z) |
| 2026-10-21 **(FUTURE)** | Wed | 1277 | calendar_entries[10] (C10) | File review: compliance conference and the second surgery (15:00-16:00Z) |
| 2026-10-29 **(FUTURE)** | Thu | 1285 | calendar_entries[11] (C11) | Client appointment: updated employment and commission records (11:00-11:45Z) |

### 9. Tasks (14), classified as of 2026-10-02

Overdue = due < 2026-10-02 and status ≠ complete. Every task is assigned to `{"id": "{{user_id}}", "type": "User"}`: the single firm user, with no named person.

| # | name | due_at (weekday) | status | assignee | class as of 2026-10-02 |
|---|---|---|---|---|---|
| T0 | Limitations Date | 2026-04-22 (Wed) | complete | User {{user_id}} | complete |
| T1 | By medical provider: McCulloch Orthopaedic Surgical Services, PLLC - Updated records and right shoulder surgical date | 2026-08-25 (Tue) | pending | User {{user_id}} | **OVERDUE** (38 days) |
| T2 | By medical provider: Advanced Rockland Chiropractic Offices, P.C. - Current daily notes and itemised bill to date | 2026-10-07 (Wed) | pending | User {{user_id}} | upcoming (in 5 days) |
| T3 | By medical provider: SportsCare Physical Therapy of New York - Ongoing treatment notes | 2026-10-14 (Wed) | pending | User {{user_id}} | upcoming (in 12 days) |
| T4 | Reconcile chiropractic and PT ledgers against CPT lines | 2026-10-05 (Mon) | pending | User {{user_id}} | upcoming (in 3 days) |
| T5 | Obtain updated employment and commission records from client | 2026-09-26 (Sat) | pending | User {{user_id}} | **OVERDUE** (6 days) |
| T6 | Confirm date of right shoulder arthroscopy with Dr. Capiola's office | 2026-10-10 (Sat) | pending | User {{user_id}} | upcoming (in 8 days) |
| T7 | Pay Montefiore Nyack records invoice and re-request | 2023-11-09 (Thu) | complete | User {{user_id}} | complete |
| T8 | Request operative report, left shoulder | 2023-08-01 (Tue) | complete | User {{user_id}} | complete |
| T9 | Serve letter of representation on Claims Service Bureau | 2023-05-14 (Sun) | complete | User {{user_id}} | complete |
| T10 | Catalogue client's own document stack | 2023-06-02 (Fri) | complete | User {{user_id}} | complete |
| T11 | Attend orthopedic IME with client | 2026-09-02 (Wed) | complete | User {{user_id}} | complete |
| T12 | Attend neurological IME with client | 2026-09-07 (Mon) | complete | User {{user_id}} | complete |
| T13 | File Medicaid lien acknowledgment | 2024-03-28 (Thu) | complete | User {{user_id}} | complete |

**Summary:** 2 overdue (T1 McCulloch records and surgical date, 38 days; T5 client commission records, 6 days). 0 due today. 4 upcoming (T4 10-05, T2 10-07, T6 10-10, T3 10-14). 8 complete. T5 and T6 fall on Saturdays.

### 10. Expenses (5) and total

Command: `python3 <session-scratchpad>/gen.py` (sums/sorts the JSON; not committed) (sums `price * quantity` over `expenses.items`). All entries have quantity 1, `tax_setting: no_tax`, user `{{user_id}}`, and the note line "Paid by the firm in USD; not yet reimbursed. Case expense, not patient treatment charges."

| # | date | amount (price x qty) | note (first line) |
|---|---|---|---|
| X0 | 2023-11-09 | $85.00 | Records reproduction: Montefiore Nyack emergency department chart reproduction. |
| X1 | 2023-08-31 | $65.00 | Records reproduction: McCulloch Orthopaedic records copy, including the left shoulder operative report. |
| X2 | 2026-09-03 | $600.00 | IME observer: Observer attendance at the two completed defence medical examinations; this is the plaintiff firm observer cost, not payment for the defence reports. |
| X3 | 2023-11-29 | $450.00 | Records reproduction: Reproduction and imaging copy charges for the remaining treating providers and the ten imaging studies. |
| X4 | 2024-07-21 | $210.00 | Court filing: Summons and complaint filing, New York County index 160000/2024. |


TOTAL = $1,410.00

The total is **$1,410.00**, all unreimbursed. The JSON order is not chronological; the guide re-sorts by date (X1–X5).

### 11. Insurance, coverage and policy limits: where they live

| Path | Value |
|---|---|
| `matter.body.custom_field_values[{{field:Policy Limits}}].value` | "Defendant liability: $100,000 / $300,000\nClient UM/UIM: $25,000 / $50,000\nNo-fault: $50,000" |
| `matter.body.custom_field_values[{{field:Policy Limits Confirmed}}].value` | `true` |
| `matter.body.custom_field_values[{{field:Insurance Carrier}}].value` | "Metro-North Commuter Railroad, SELF-INSURED. Claims administered by Claims Service Bureau. Client's own no-fault: Progressive…" |
| `matter.body.custom_field_values[{{field:Claim Number}}].value` | "SIR068120 (Metro-North / Claims Service Bureau)" |
| `matter.body.custom_field_values[{{field:Health Insurance or Lien Holder}}].value` | Medicaid lien $22,180.00; no-fault $50,000 exhausted; SSD pending; CPLR 4545 pleaded |
| `communications.items[42]` (M42, 2026-09-08, CSB→firm, subj "RE: Discovery status and outstanding demands") | "The bodily injury liability limits are $100,000 per person and $300,000 per occurrence. No excess or umbrella coverage is disclosed." |
| `communications.items[64]` (M64, 2026-09-08, CSB→firm, subj "RE: Coverage confirmation, claim SIR068120") | **identical body** to M42 |
| `communications.items[20]` (M20, 2023-12-19) and `[67]` (M67, 2025-01-10), Progressive→firm | $50,000 basic economic loss exhausted (claim 22-4471102); sent twice, 13 months apart |
| `notes.items[1]` (N1, 2023-05-14) | Metro-North self-insured; "Ferrara personally carries auto coverage identified at $100,000 / $300,000" |
| `notes.items[22]` (N22, 2023-05-09) | "Self-insured with no stated ceiling… no limit to confirm. Valuation cannot lean on a policy limit." |
| `notes.items[37]` (N37, 2026-09-09) | "Coverage confirmed in writing by the adjuster… Defendant liability $100,000 per person / $300,000 per occurrence… UM/UIM is $25,000 / $50,000… No-fault was $50,000 and is exhausted." |
| `notes.items[17]` (N17, 2026-06-04) | "The defendant carries $100,000 per person, the client's own UM/UIM sits under it" |
| Folder `07 Insurance` | empty by design; no declarations page or policy document exists |

**Not present:** any policy document or declarations page; any written source for the client's UM/UIM $25,000/$50,000 (it appears only in F6, N17 and N37, with no Progressive communication about it); any adjuster's name; the policy number of Ferrara's personal policy or the identity of its carrier.

**Contradiction:** the $100k/$300k limit is attributed to **Ferrara's personal auto policy** (N1). Elsewhere it is the **defendant/BI liability limit confirmed by CSB**, which is Metro-North's administrator, while Metro-North is "self-insured with no stated ceiling" (N22, F4) (M42/M64, N37, F6). N17 (June 2026) already relies on $100k before the written confirmation of 2026-09-08/09.

### 12. STRATEGY FLAGS: content that must never reach providers

Attorney mental impressions, valuation, settlement posture and weaknesses:

| Where | Excerpt |
|---|---|
| CF F8 Estimated Case Value | `375000.0` |
| CF F9 Case Value Rationale | "The case is worth more than the coverage. We are capped at the $100,000 defendant limit…" |
| CF F12 Liability Assessment | "Contested on two independent levels, neither investigated." |
| CF F15 Prior Related Injuries | "Denied by the client, contradicted by his own paperwork." |
| CF F11 Wage Loss Claimed | "Figure is from the client's own 2022 1099; no economic expert retained." |
| N1 | "If Metro-North comes out of the case on scope of employment, that policy is the entire recovery." |
| N2 | "three versions of this collision on file and two of them are his… the account we adopt is the case… Nobody has asked him for them." |
| N3 | "Three inconsistent positions on one ankle and all three are ours." (prior 2011 avulsion fracture) |
| N4 | "Everything about the value of this file sits on that fact… Kyle Pullano… has not been contacted." |
| N5 | "hypoplasia of the posterior inferior glenoid, which is developmental… Expect the defence to lean on it." |
| N8 | "the head injury claim rests entirely on imaging taken 107 days later." |
| N10 | "If the defence reads it as a discharge, the gap argument writes itself." |
| N11 | "our specials figure is a treatment-value number rather than the net third-party claim." |
| N13 | "the net to the client will look very different from the gross" |
| N15 | "Nothing here should be settled while treatment is open and the ledgers are unreconciled." |
| N17 (Case evaluation) | "Valuation: $375,000… Exposures, frankly stated: … credibility problem… a witness who has to be prepared carefully" |
| N19 | "update the settlement assessment as treatment and billing evidence develops" |
| N20 | "Client refused to provide past medical history… which we did not instruct and which will be reported." |
| N22 | "Valuation cannot lean on a policy limit." |
| N23 | "the wage claim… will be argued." |
| N25 | "Those records are the case… either it does not exist or nobody wants to find it." |
| N27 | "This is not an administrative problem, it is a valuation problem… the defence will say it was never needed" |
| N28 | "any number we give the authority is a number we may have to correct, which is the worst position to negotiate from." |
| N30 | "Responding rather than motioning: the paper is cheaper than the fight." |
| N32 | "That is convenient for them… it hands the calendar to a surgery that has no date." |
| N34 | "interim number and should not be quoted anywhere as final." |
| N35 | "liability is contested on two independent levels and neither has been investigated." |
| N37 | "Practical read: recovery is capped at $100,000 unless the case reaches a second defendant" |
| N40 | "This is the weakest documented part of the damages case." |
| N41 (Case posture) | "Liability is contested on two independent levels… Anticipate comparative negligence, assumption of risk and a seatbelt defence… causation exposure: … hypoplasia" |
| C10 (2026-10-21) | "whether to move to compel… and whether to value this case with the right shoulder surgery as recommended-but-undated" |
| T10 description | "including prior X-ray reports the client did not disclose." |
| M38 (to client) | "This is the single biggest number in your claim and right now it rests on one document." |
| M55 (client call) | "client… cannot afford to be out of work again… a gap will be used against him." |

Borderline items, sent to or from providers today and sensitive only if combined with the above: M33 ("We cannot finalise our client's claim while it is outstanding"), M46 ("the damages cannot be closed while the second surgery is an open question"), M50 ("specials schedule cannot be closed without it"). These are existing outbound provider emails and contain no valuation figures.

### 13. Setup guide (30 pp): section by section

| Pages | Section | Content | Facts not in JSON / discrepancies |
|---|---|---|---|
| 1 | Cover | "Everything **Cedar** would have put into Clio… enter it by hand if the app is down." Counts (16/10/42/69/14/17/5/15). Order of work: Steps 1–6. Tips: split the work, one person per section; start uploads early ("Two files are 34 MB and 42 MB"); copy-paste long text; "You (firm user)" = your own Clio login; documents pre-sorted by folder. | "Cedar" names the setup app (**INFERRED**). The tip's "34 MB and 42 MB" are decimal MB (34,179,576 and 42,107,788 bytes); the p7 table shows the same files as 32.6 MB and 40.2 MB (binary). Same bytes, different units. |
| 2 | Step 1: Matter stages | Settings → Matters → Matter stages, under Personal Injury; 8 stages in order; Sapini at Litigation. "Most common mistake: creating the stages under a different practice area." | Matches JSON. |
| 3–4 | Step 2: Custom fields F1–F16 | Settings → Custom fields → Matters, "no field set needed"; name, type and Sapini value per field. | Matches JSON exactly (automated text check). The only difference is date format (04/23/2023). |
| 5–6 (top) | Step 3: Contacts P1–P10 | Create, then link under Related contacts; the client is the matter's client, not a related contact. | Matches JSON contacts and relationship text (automated check). |
| 6 | Step 4: The matter | Same values as `matter.body`; dates shown in MM/DD/YYYY. | Adds "Responsible / originating attorney: leave as you". |
| 6–7 | Step 5: Folders and documents D1–D15 | 9 folders including the 2 empty ones; upload with exact file names; use the received date if the dialog has one. Explains the file-name convention (docket number, "created" = firm-made). | Names, folders and dates match JSON. Sizes are shown rounded. |
| 8–18 | Step 6a: Notes N1–N42 | "Set the date, subject and detail exactly as shown." Rows sorted by date. | All 42 JSON notes found verbatim with matching subject and date on the same page (automated). Guide numbers ≠ JSON index; mapping below. |
| 19–26 | Step 6b: Communications M1–M69 | Log email or phone with date, from → to, subject, body. | All 69 found verbatim with date on page (automated). Guide numbers ≠ JSON index. |
| 27–28 (top) | Step 6c: Tasks T1–T14 | Assigned to you; mark completed ones complete; keep the "By medical provider:" prefix exactly. Sidebar on T1: "Clio may create it for you from the matter's limitations date; if so, just mark it complete." | Matches JSON (automated). The guide follows the JSON order here (T1 = JSON T0). |
| 28–29 | Step 6d: Calendar E1–E17 | New event on your calendar linked to the matter. Sorted by date. | **Time zone discrepancy:** the guide shows times with no zone (e.g. "10:00 AM – 10:45 AM"), while the JSON values are UTC (`10:00:00Z`). Hand entry in a non-UTC Clio account would shift them relative to an API-seeded matter (**INFERRED** impact). |
| 30 | Step 6e: Expenses X1–X5 | Quantity 1, no tax, amount as price, note pasted exactly. Sorted by date. | Matches JSON. |

No raster images exist in the PDF (`pdfimages -list` is empty). I viewed pp1–2 as rendered images: the cover cards and the stage bar highlighting Litigation. Every table is text-native.

**Guide row ↔ JSON index mapping** (notes: JSON→guide): N0→1, N1→3, N2→5, N3→6, N4→7, N5→8, N6→9, N7→10, N8→11, N9→12, N10→13, N11→15, N12→16, N13→17, N14→18, N15→19, N16→20, N17→32, N18→33, N19→34, N20→35, N21→42, N22→2, N23→4, N24→14, N25→36, N26→38, N27→40, N28→41, N29→24, N30→25, N31→26, N32→27, N33→28, N34→29, N35→30, N36→31, N37→37, N38→21, N39→22, N40→23, N41→39.

Communications (JSON→guide): M0→1, M1→2, M2→3, M3→4, M4→5, M5→6, M6→7, M7→8, M8→9, M9→10, M10→13, M11→17, M12→18, M13→19, M14→20, M15→11, M16→12, M17→14, M18→15, M19→16, M20→21, M21→22, M22→23, M23→24, M24→25, M25→26, M26→28, M27→29, M28→42, M29→47, M30→48, M31→49, M32→50, M33→51, M34→54, M35→52, M36→53, M37→56, M38→64, M39→69, M40→27, M41→55, M42/M64→57/58 (identical bodies, ambiguous), M43→59, M44→60, M45→61, M46→62, M47→63, M48→65, M49→66, M50→68, M51→67, M52→34, M53→35, M54→36, M55→37, M56→38, M57→39, M58→40, M59→41, M60→43, M61→44, M62→45, M63→46, M65→30, M66→31, M67→32, M68→33.

#### Internal discrepancies found (JSON and guide agree with each other; these conflict *within* the case data)

1. **Coverage:** self-insured with "no stated ceiling / no limit to confirm" (N22, F4) vs. $100k/$300k as Ferrara's personal policy (N1) vs. $100k/$300k as BI limits confirmed by Metro-North's TPA (M42, M64, N37, F6/F7).
2. **SOL rule:** C8 says "Three-year statute of limitations expires" 2026-04-22. N22 says the shortened public-benefit-corporation period applies, "not the ordinary three years". The field is DOI + 1095 days, one day before DOI + 3 calendar years (**INFERRED** computation).
3. **Litigation order:** the summons and complaint were received 2024-03-08 (D2), *before* the demand (2024-04-12, M40/N14) and before the right-shoulder recommendation (2024-05-27). But N19 says the demand and negotiation were "overtaken by the right shoulder recommendation, the Presentation of Claim was served… and the action is now in discovery". The filing-fee expense X4 is dated 2024-07-21, after the answer (D3, 2024-04-17).
4. **Bill of particulars:** the BoP was received 2024-05-27 (D4), but N38 (2024-10-19) says "We have served the bill of particulars" as a new event.
5. **IMEs:**
   - N20, dated 2026-09-02, reports *both* IMEs (the neuro IME is 09-07) "four days apart"; the calendar has them 5 days apart.
   - X2 (2026-09-03) bills the observer for "the two completed" exams before the second one.
   - M37 (2026-09-07) books the watchdog for "both examinations" after the first had happened.
   - N20, T11 and T12 say the watchdog attended both and the ortho exam ran "under fifteen minutes". M44 says the watchdog attended only the ortho exam and the *neuro* exam lasted "under ten minutes".
6. **Expert reports:** N26 (2026-09-13) says both defence reports were served and Katzman's "followed a few days later and has been saved". The documents arrived later: Hostin 09-14, Tsao 09-20, Katzman 09-22 (D12–D14, M45, M47, M48).
7. **Right-shoulder chase count:** C9 (2026-10-10) says "Fourth attempt", but N27 and M46 (2026-09-17/18) already say "fifth approach".
8. **Treatment frequency:** chiro three times weekly (N23, 2023) → PT and chiro once weekly (N29, M52 "PT on Tuesdays and the chiropractor on Thursdays", M58) → PT twice a week (N27, M51, 2026-09) → calendar shows weekly PT on Saturdays (C14, C16) and chiro on a Friday (C15).
9. **M65** (2024-10-07), titled "Post-operative check-in", comes 14 months after the left surgery and *after* the right shoulder was already recommended (N16, 2024-05-27). It says the right shoulder "now bothers him more", as if that were new.
10. **Specials vs. bills:** N12 (2024-02-17) books Montefiore ER at $9,087.00, yet M28 (2025-12-06) is still asking Montefiore for the itemised charges. N12's 8 line items sum exactly to $118,400.00 (38,500 + 9,087 + 24,600 + 6,200 + 17,400 + 14,900 + 4,850 + 2,863).
11. **Duplicates:** the no-fault exhaustion notice was sent twice (M20 2023-12-19, M67 2025-01-10). The identical coverage email has two subjects (M42 and M64). The Medicaid lien is "asserted" in N13 and T13 (2024-03-28) but first told to the client in M68 (2025-03-01), even though M23 (2024-02-17) already explains the lien.
12. **CSB's file-review email** M34 (2026-08-23) asks for medical records "as it becomes available", as if the claim were pre-suit, two years into litigation.
13. **Letter of representation:** T9 is due and complete on 2023-05-14, but the email M4 is dated 2023-05-15.
14. **Venue (INFERRED oddity):** X4 gives "New York County index 160000/2024", while the accident location is Westchester County.

## Part 2: Case PDFs (`Sapini documents/`, 15 files, 640 pp)

Scope: the 15 PDFs under `Sapini Case Materials/Sapini documents/`. Folders `07 Insurance` and `09 Settlement` do not exist on disk.
Not covered here: `sapini-clio-data.json` and the setup guide (another agent has them).
Method: `pdftotext -layout` for text-native files. The scanned files were read with tesseract OCR (`Sapini Case Materials/_ocr/<tag>/pNNNN.txt`; complete, 522 pages) plus page images. Bill pages were checked against 200 dpi renders.
Labels: **INFERRED** marks my own reading rather than something printed on the page. **ILLEGIBLE** marks something I could not read. All numbers below are copied from the documents. Nothing is estimated.
Everything is filed under Index No. 160000/2024 (N.Y. Co. Sup. Ct.), *Sapini v. Anthony F. Ferrara and Metro-North Commuter Railroad*, unless noted. The earlier, dismissed action was Index No. 150940/2024, which also named MTA. Large parts of doc-19 and doc-20 are exhibits re-filed from that earlier action.

### (a) Per-file table

| Folder | File | Pages | Type | Summary |
|---|---|---|---|---|
| 01 Intake and Retainer | 01-intake__created__hipaa-authorization.pdf | 1 | text-native | HIPAA release signed by Justin W. Sapini on May 7, 2023. Address: 7 Valley Drive, Nanuet NY. It names 7 providers: Montefiore Nyack Hospital; Advanced Rockland Chiropractic (Kevin M. Haggerty DC); McCulloch Orthopaedic Surgical Services / Dr. David Capiola; SportsCare PT / Michael Ludena PT; Dr. Vadim Abramov; Dr. Peter C. Kwan; New Horizon Surgical Center. It covers itemized bills and payment records starting one year before the incident. No amounts. |
| 01 Intake and Retainer | 01-intake__created__photo-id.pdf | 1 | scanned | Photo of a New York State driver license (Class D) on a dark background. Some fields are already blurred in the image. ID number and DOB deliberately not transcribed. |
| 02 Pleadings | 02-pleadings__doc-01__summons-complaint.pdf | 8 | scanned (OCR'd) | Summons and Verified Complaint dated Oct 15, 2024 (NYSCEF doc 1, filed 10/11/2024, received 10/29/2024). It describes the April 23, 2023 collision at about 8:30 a.m. on Cedar St at Garden St, New Rochelle, Westchester. Defendants' vehicle: 2019 Chevrolet utility vehicle, PA plate ZMP3277, "MTA Metro-North Railroad" badging, unit E2858D. Plaintiff's vehicle: 2012 VW, NY plate KYR1393. Ferrara's address: 12 Daisy Farm Dr, Brookfield CT. Pleads serious injury under Ins. Law §5102(d) and §5104, and says plaintiff does not seek no-fault-reimbursable damages. Damages pleaded only as exceeding lower-court limits; no dollar amount. A footnote recites the earlier action 150940/2024 (filed Feb 1, 2024), its dismissal by Tsai J. for no Presentation of Claim, a new Presentation of Claim served Sept 10, 2024, and recommission under CPLR 205. **Paragraphs 6-16 are missing**: page 2 ends at ¶5 and page 3 starts at ¶17. |
| 02 Pleadings | 02-pleadings__doc-05__verified-answer-demands.pdf | 27 | text-native | Defendants' Verified Answer dated Dec 2, 2024, from Milber Makris Plousadis & Seiden (file 1805CS-28142M). Nine affirmative defenses: comparative negligence, assumption of risk, seatbelt, collateral source (CPLR 4545), failure to mitigate, emergency doctrine, Pub. Auth. Law §1276, statute of limitations, another action pending. The package also contains: EBT notice for Mar 5, 2025; demand for a verified bill of particulars (Nov 15, 2024); discovery demand, including CPLR 3101(f) insurance disclosure and Medicare questions; social-media demand; 3101(d) expert demand; CPLR 2103(5) notice; CPLR 3017 demand for the damages amount; demand for trial authorizations. No amounts or policy data. |
| 02 Pleadings | 02-pleadings__doc-07__bill-of-particulars.pdf | 14 | text-native | Plaintiff's Verified Bill of Particulars dated Jan 2, 2025. Current address: Cypress TX. Accident Apr 23, 2023 at 8:30 a.m., both vehicles southbound; the defendant's passenger-side door struck the plaintiff's driver door and fender. Injuries: L shoulder labral tear with 7/26/2023 arthroscopic repair by Capiola at New Horizon Surgical Center; R shoulder RC/labral tears with surgery recommended; L wrist; concussion and post-concussion syndrome with abnormal DTI; bilateral medial meniscus tears; C5-6 and L5-S1 bulges. ER at Montefiore Nyack on Apr 24, 2023. Confined to bed about 1 week plus 1 week after surgery, and to home continuing. Totally disabled from work since the date of accident; was a commission-only financial advisor at Northwestern Mutual. Lost earnings "to be provided" (no figure). 10 providers listed. Special damages: "contained within the providers' records" (**no dollar totals**). VTL sections alleged. |
| 02 Pleadings | 02-pleadings__doc-41__bop-affirmative-defenses.pdf | 3 | text-native | Defendants' Bill of Particulars as to Affirmative Defenses, Sept 30, 2025 (Stephen F. Zaklukiewicz). It particularizes culpable conduct, seatbelt, serious injury (objects), failure to mitigate, collateral source and emergency doctrine. Boilerplate refers to the plaintiff as "her". No amounts. |
| 03 Discovery | 03-discovery__doc-08__response-discovery-demands.pdf | 10 | text-native | Plaintiff's Response to Discovery Demands, Jan 2, 2025. No witnesses beyond the parties and the police report. A 50-h transcript was provided. Prior lawsuit: 150940/2024. 22 photos. No-fault paid through **Progressive Insurance Company**, PO Box 2930, Clinton IA 52733; the claim number field is **blank in the PDF**. Plaintiff receives **NYS Medicaid**. SSD authorization to follow. Insurance demand "not applicable to plaintiff". **Damages "not to exceed $10,000,000."** |
| 03 Discovery | 03-discovery__doc-40__defendants-response-demand.pdf | 11 | text-native, partly scanned images | Defendants' response, Sept 30, 2025. Witness: Kyle Pullano, a Metro-North employee who was a passenger in the defense vehicle. "Insurance coverage information to be provided under separate cover." Attachments: Metro-North IR-1 incident report (p3, location "I 95 Southbound Exit# 16 ramp", Ferrara "Assistant Foreman", refused medical attention); Accident Report Cover Sheet (p4) showing **Automobile Policy # HC2ECAP477M0330TCT19, Travelers Indemnity**, distributed to Claims Service Bureau, file M23-042, location "Cedar St & Garden St, New Rochelle"; handwritten MV accident report (p5-6, liability-insurance fields blank); 5 photos of the vehicles (p7-11). |
| 03 Discovery | 03-discovery__doc-43__subpoena-kyle-pullano.pdf | 2 | text-native | Plaintiff's subpoena ad testificandum to Kyle Pullano for a virtual EBT on Dec 8, 2025 at 10:00 a.m. Dated Nov 2, 2025 (T. J. Cortelli). Recites the $50 statutory penalty only. |
| 04 Medical Records | 04-medical-records__doc-19__records-bundle-part1-haggerty-imaging.pdf | 250 | scanned (OCR'd) | NYSCEF doc 19 (filed 4/28/2025), Exhibit "C". Contains the 150940/2024 cross-motion papers (notice, affirmation, memo of law) and their exhibits: plaintiff's affidavit, scene/vehicle photos, Semble no-fault IME, Abramov, Capiola, Haggerty chiro chart (exam, SOAP notes, re-exams, disability certificates), Progressive NF-2/NF-3/NF-10 forms, HVRA/Mid Rockland MRIs, Kwan neurology, Lenox Hill brain MRI/DTI/NeuroQuant, EMG/NCV (Miller), the Montefiore records request with the Ciox invoice, the **Montefiore itemized statement**, and ED chart pages 1-6. 72 segments; see (b). |
| 05 Medical Bills and Liens | 05-medical-bills__doc-20__records-and-bills-part2-pt-ortho-er-operative.pdf | 262 | scanned (OCR'd) | NYSCEF doc 20 (filed 4/28/2025). It continues the Montefiore ED chart (pages 7-57), then a **SportsCare PT invoice**, SportsCare PT records (West Nyack and Nanuet), the Kwan 12/12/23 follow-up, and Capiola's **"Surgical Breakdown" estimate** for the R shoulder. Exhibits B-L of the earlier action follow: Google street views, police report MV-104A, MTA rules, Claims Service Bureau letter, emails, operative report 7/26/23, Presentation of Claim letter ($5,000,000 demand), plaintiff affidavit, Semble IME, NYC Transit and Comptroller claim forms, Progressive NF-10, redlined and proposed amended complaints, and the Notice of Claim. 35 segments; see (b). |
| 06 Correspondence | 06-correspondence__doc-12__letter-to-judge.pdf | 1 | scanned (OCR'd) | Letter from StolzenbergCortelli (T. J. Cortelli) to Hon. Christopher Chin, Apr 16, 2025. The RJI and PC request were filed Jan 2, 2025, but no PC date or scheduling order has issued; the clerk was contacted Apr 15-16. It asks for a PC date or a Case Scheduling Order. |
| 08 Experts | 08-experts__doc-47__radiology-review-katzman.pdf | 10 | text-native | Defense 3101(d) exchange (Feb 4, 2026) of Dr. Marc J. Katzman's radiology reviews dated Dec 8, 2025. The cover also says "report dated February 11, 2025", an internal date inconsistency. Findings: R and L knee MRI 7/3/23 show no recent injury or derangement; R shoulder MRI 5/24/23 unremarkable; chest x-ray 9/10/2018 predates the accident; brain MRI, DTI and NeuroQuant 8/8/23 normal, with a footnote doubting the use of advanced imaging. Claim number 1805CS28142M; D&D file 22725030856. CV included. |
| 08 Experts | 08-experts__doc-55__expert-exchange-neuro-tsao.pdf | 47 | text-native | Defense exchange (Mar 24, 2026) of Dr. Jack W. Tsao's neurological IME, done Mar 4, 2026 for D&D Associates, **Claim# SIR068120**, File# 22726002907. All conditions "objectively resolved": post-concussion, post-traumatic headache, TBI, and cervical, thoracic and lumbar strain. Incidental bilateral carpal tunnel. Can work without restrictions. An IME watchdog was present. Pages 8-46 are the CV; p47 is the affirmation of service. |
| 08 Experts | 08-experts__doc-56__ime-orthopedic-hostin.pdf | 15 | text-native | Defense exchange (Apr 9, 2026) of Dr. Emmanuel Hostin's orthopedic IME, done Mar 31, 2026. "Rescheduled Liability"; **Claim No SIR068120, Carrier#: Claims Service Bureau**, D&D Acct 22726002906-1. The history notes PT and chiro once weekly, tramadol and ibuprofen, and a planned R shoulder arthroscopy. The records list includes prior IMEs (Semble 9/13/23 and **Alleyne 10/31/2025**, which is not in this set), a 2011 L ankle/foot x-ray (avulsion fracture) and EMG/NCV results. Diagnosis: all sprains resolved. Opinions: subjective complaints do not correlate with objective findings; can return to work without restrictions. ROM tables included. |

### (b) Page-range index for the two scanned bundles

Provider and date come from OCR text and page images. **INFERRED** means I grouped pages by appearance without reading every page's date. Handwritten SOAP dates are approximate.

#### doc-19 (250 pages)

| Pages | Provider / author | Doc type | Date(s) of service / doc date | Notes |
|---|---|---|---|---|
| 1-1 | NYSCEF | Exhibit "C" slip sheet | filed 4/28/2025 | |
| 2-2 | StolzenbergCortelli | Notice of Cross Motion (150940/2024) | 4/8/2024 | asks leave for late Notice of Claim and to amend |
| 3-12 | Howard B. Stolzenberg | Affirmation in support of cross motion | 4/8/2024 | p8: "no fault benefits have been exhausted and he has since obtained Medicaid" |
| 13-22 | StolzenbergCortelli | Memorandum of Law | 4/8/2024 | |
| 23-23 | NYSCEF | Exhibit "A" slip sheet | | |
| 24-27 | Justin Sapini | Affidavit (late notice of claim) | Mar 2024 | car damage "in excess of $9,000"; no-fault exhausted; Medicaid |
| 28-31 | Google Maps / photos | Scene map and vehicle photos | | 25 Garden St; Metro-North truck; plaintiff's car |
| 32-33 | Montefiore Nyack ED | After-visit summary (photos) | 4/24/2023 | |
| 34-36 | Richard Semble MD | No-fault orthopedic IME for Progressive | 9/13/2023 | Claim 233582428.01; moderate partial disability; PT 2x/wk |
| 37-37 | Montefiore Nyack | Photo of CT results page | 4/24/2023 | |
| 38-40 | Vadim Abramov MD (Interventional PM&R) | Initial evaluation | 5/4/2023 | temporarily totally disabled |
| 41-43 | McCulloch Ortho / David Capiola MD | Initial ortho exam | 5/17/2023 | insurance shown as "NF - Progressive" |
| 44-44 | Advanced Rockland Chiro (Haggerty) | X-ray report (cervical/lumbar) | 4/26/2023 | |
| 45-50 | Advanced Rockland Chiro (Haggerty) | Initial exam narrative and treatment plan | 4/26/2023 | DOS 4/23/23; Acct NF 2278 |
| 51-52 | Advanced Rockland Chiro | SOAP notes | 4/28/2023, 5/2/2023 | Ins Co: PROGRESSIVE, Claim 23 3582428 |
| 53-53 | Advanced Rockland Chiro | Referral letter to Dr. Capiola (rotated, handwritten) | ~5/2023 (INFERRED) | |
| 54-54 | Advanced Rockland Chiro | MRI referral to HVRA | 5/2/2023 (INFERRED from OCR "5 {2") | |
| 55-55 | Advanced Rockland Chiro | SOAP note | 5/3/2023 | |
| 56-56 | NYS DMV | Police accident report MV-104A (rotated) | 4/23/2023 | |
| 57-58 | Advanced Rockland Chiro | Fax confirmation and cover sheet to Progressive | 5/5/2023 | Progressive claim 23-3582428 |
| 59-61 | Advanced Rockland Chiro | NF-3 verification of treatment | 4/26/2023 | charge block reads "SEE BILL ATTACHED"; no amount on these pages |
| 62-62 | Mitchell J. Schroeder PC | Letter to Progressive: no-fault application and UM/UIM notice | 5/4/2023 | Claim # 23-3582428 |
| 63-65 | Justin Sapini / Progressive | NF-2 application for no-fault benefits (+ rotated authorization) | 5/4/2023 | Policy # 950478050; Claim 23-3582428 |
| 66-67 | NYS DMV / USPS | Police report (rotated) and certified mail receipt | 4/23/2023 | p67 postage ILLEGIBLE |
| 68-69 | Advanced Rockland Chiro | SOAP notes | 5/5/2023, 5/8/2023 | |
| 70-73 | Hudson Valley Radiology (HVRA Rockland) | MRI cervical (70-71) and lumbar (72-73) | 5/8/2023 | C5-6 bulge; L5-S1 bulge |
| 74-74 | Advanced Rockland Chiro | Disability certificate | 5/9/2023 | 4/24/23 to 5/24/23 |
| 75-79 | Advanced Rockland Chiro | SOAP notes | 5/9/2023 to 5/17/2023 | |
| 80-80 | Advanced Rockland Chiro | Prescription / medical necessity (cervical traction, LSO) | 5/22/2023 | |
| 81-82 | Advanced Rockland Chiro | SOAP notes | 5/22/2023, 5/23/2023 | |
| 83-83 | Advanced Rockland Chiro | Disability certificate | 5/23/2023 | |
| 84-84 | Advanced Rockland Chiro | SOAP note | 5/30/2023 | |
| 85-88 | HVRA / Mid Rockland Imaging | MRI R shoulder (85-86) and L shoulder (87-88) | 5/24/2023 | Paruchuri |
| 89-89 | Advanced Rockland Chiro | SOAP note | 6/2/2023 | |
| 90-97 | HVRA | Duplicate faxed MRI reports, rotated: cervical, L shoulder, lumbar, R shoulder | 5/8/2023 and 5/24/2023 | duplicates of 70-73 and 85-88 |
| 98-99 | New Horizon Surgical Center / Capiola | Operative report (upside-down scan) | 7/26/2023 | L shoulder arthroscopy |
| 100-105 | Peter C. Kwan MD | Neurology follow-up | 10/31/2023 | |
| 106-111 | Peter C. Kwan MD | Comprehensive neuro exam | 9/6/2023 | |
| 112-116 | Peter C. Kwan MD | Comprehensive neuro exam | 5/31/2023 | |
| 117-119 | Vadim Abramov MD | Initial evaluation (duplicate) | 5/4/2023 | |
| 120-120 | Vadim Abramov MD | Post-operative note | 9/7/2023 | |
| 121-121 | Advanced Rockland Chiro | SOAP note | 6/5/2023 | |
| 122-122 | Advanced Rockland Chiro | Disability certificate | 6/7/2023 | |
| 123-127 | Advanced Rockland Chiro | SOAP notes | 6/7/2023 to 6/14/2023 | |
| 128-128 | Advanced Rockland Chiro | Disability certificate | 6/23/2023 | |
| 129-130 | Advanced Rockland Chiro | SOAP notes | 6/23/2023, 6/27/2023 | |
| 131-134 | Advanced Rockland Chiro | Re-examination narrative | 6/27/2023 | |
| 135-146 | Advanced Rockland Chiro | SOAP notes | 6/28/2023 to ~8/8/2023 (INFERRED) | p144 notes the L shoulder surgery of 7/26/23 |
| 147-147 | Advanced Rockland Chiro | Disability certificate | 8/9/2023 | 8/4/23 to 8/23/23 |
| 148-154 | Advanced Rockland Chiro | SOAP notes | 8/9/2023 to 8/29/2023 | |
| 155-155 | Advanced Rockland Chiro | Disability certificate | 8/30/2023 | |
| 156-159 | Advanced Rockland Chiro | Re-examination narrative | 8/30/2023 | |
| 160-164 | Advanced Rockland Chiro | SOAP notes | 8/30/2023 to 9/20/2023 | |
| 165-169 | Melinda L. Miller MD (at Advanced Rockland) | EMG/NCV lower extremity | 9/20/2023 | bilateral L5-S1 radiculopathy |
| 170-170 | Advanced Rockland Chiro | SOAP note | 9/27/2023 | |
| 171-175 | Melinda L. Miller MD | EMG/NCV upper extremity | 8/23/2023 | L C5-6 radiculopathy |
| 176-179 | Progressive Max Ins Co | NF-10 denial of claim, partial, based on Semble IME | 2023 (exact date ILLEGIBLE) | PT allowed 2x/wk through 10/25/2023 |
| 180-183 | Progressive Max Ins Co | NF-10 denial of claim, partial, based on Sean A. Higgins DC IME | 2023 (exact date ILLEGIBLE) | chiro allowed 2x/wk through 11/09/2023; lost earnings denied |
| 184-188 | Advanced Rockland Chiro | SOAP notes | 10/10/2023 to 11/21/2023 | |
| 189-189 | Advanced Rockland Chiro | Disability certificate | 8/30/2023 | duplicate |
| 190-190 | NY Sports & Joints / Capiola | Disability evaluation | 12/6/2023 | totally disabled |
| 191-204 | Advanced Rockland Chiro | Disability certificates (series) | 5/9/2023 to 11/21/2023 | covers 4/24/23 to 12/5/23 |
| 205-224 | McCulloch Ortho / Capiola (and PAs) | Ortho follow-ups | 7/5, 8/16, 9/20, 10/18, 12/6/2023, 1/3/2024 | R shoulder arthroscopy recommended |
| 225-226 | HVRA / Mid Rockland | MRI R shoulder (duplicate fax) | 5/24/2023 | |
| 227-227 | Vadim Abramov MD | Post-operative note (duplicate) | 9/7/2023 | |
| 228-231 | Lenox Hill Radiology (Buono) | MRI brain with DTI | 8/8/2023 | abnormal DTI |
| 232-234 | Lenox Hill Radiology (Buono) | 3D volumetric (NeuroQuant) brain | 8/8/2023 | |
| 235-240 | Mitchell J. Schroeder PC | Fax to Montefiore: records-and-bills request (includes blank pages) | 6/20/2023 | |
| 241-242 | Justin Sapini | OCA HIPAA authorization to Montefiore | 6/19/2023 | p241 shows the SSN field; not transcribed |
| 243-243 | Ciox Health | Records copy invoice | 6/22/2023 | $45.50 |
| 244-244 | Montefiore Nyack Hospital | Itemized hospital statement | DOS 4/24/2023 | see (c) |
| 245-250 | Montefiore Nyack Hospital | ED chart pages 1-6 | 4/24/2023 | continues at doc-20 p1 |

#### doc-20 (262 pages)

| Pages | Provider / author | Doc type | Date(s) of service / doc date | Notes |
|---|---|---|---|---|
| 1-51 | Montefiore Nyack Hospital | ED chart pages 7-57 (notes, CT C-spine and head, orders, flowsheets, consents, AVS) | 4/24/2023 | dx: neck spasm, MVA, L shoulder strain; CTs negative; Flexeril and ibuprofen |
| 52-56 | SportsCare Physical Therapy of NY | Itemized patient invoice #1159038319 | DOS 6/29/2023 to 12/14/2023; invoice dated 12/21/2023 | see (c); payer "Progressive Auto" |
| 57-62 | SportsCare PT - West Nyack (Ludena) | PT initial exam, QuickDASH, outcomes report | 9/14/2023 | |
| 63-64 | SportsCare PT - West Nyack | Daily note / billing sheet | 9/14/2023 | CPT 97110, 97140, 97163, 97010, G0283 |
| 65-122 | SportsCare PT - Nanuet | Daily notes, flowsheets, progress notes, outcomes, missed-appointment notes | 9/16/2023 to 12/19/2023 | p67 NY Sports & Joints referral (rotated); progress notes 11/1 and 12/14/2023 |
| 123-123 | SportsCare of America PC | Records certification | 12/21/2023 | "does not possess any films" |
| 124-130 | SportsCare PT | Intake: medical history, privacy, assignment of benefits, referral | 6/21/2023 to 6/23/2023 | |
| 131-138 | SportsCare PT - Nanuet | Missed appt 6/26; initial exam addendum; outcomes; QuickDASH | 6/26/2023 to 7/10/2023 | |
| 139-157 | SportsCare PT - Nanuet | Daily notes and flowsheets, missed appointments, discharge note | 6/29/2023 to 9/14/2023 | missed appts 7/25 (surgery), 7/27, 8/2, 9/5; discharge 9/14/2023 |
| 158-162 | SportsCare PT | Intake: medical history, privacy, assignment of benefits | 6/21/2023 and 9/14/2023 | |
| 163-164 | NY Sports & Joints / Capiola | PT referral forms (rotated) | 7/5/2023 | |
| 165-170 | Peter C. Kwan MD | Neurology follow-up | 12/12/2023 | |
| 171-171 | NY Sports & Joints / Capiola | "Surgical Breakdown": cost estimate for proposed R shoulder surgery | 1/3/2024 | addressed to Mitchell J. Schroder; see (c) |
| 172-175 | NYSCEF / Google | Exhibit "B": street-view images | | 89 Cedar St, New Rochelle |
| 176-178 | NYSCEF / NYPD-type MV-104A | Exhibit "C": police accident report | 4/23/2023 (report 4/28/2023) | |
| 179-189 | MTA | Exhibit "D": MTA Rules & Regulations (Ch. 8, Ch. 1) | 2016 edition | |
| 190-190 | NYSCEF | Exhibit "E" slip (medical records attached to Exh A) | | |
| 191-193 | Claims Service Bureau of NY (Carlene Schultz) | Exhibit "F": TPA letter to plaintiff's counsel | 2/20/2024 | File SIR068120; insured Metro North Railroad |
| 194-196 | StolzenbergCortelli / CSB | Exhibit "G": emails | 2/20/2024 | claim # SIR068120 |
| 197-198 | New Horizon Surgical Center / Capiola | Operative report | 7/26/2023 | |
| 199-200 | StolzenbergCortelli | Exhibit "H": Presentation of Claim letter to MTA/Metro-North | 3/14/2024 | **demands $5,000,000**; refers to no-fault "policy has been exhausted" |
| 201-205 | Justin Sapini | Affidavit (rotated) and Google map | Mar 2024 | duplicate of doc-19 pp24-28 |
| 206-208 | Richard Semble MD | No-fault IME (duplicate) | 9/13/2023 | |
| 209-211 | Photos | Vehicle photos | | |
| 212-219 | NYC Transit Dept of Law | Personal Injury Claim Forms (2 copies) | incident 4/23/2023 | Progressive "Policy # 23-3582428 (CLAIM #)" |
| 220-221 | NYS DMV | Police accident report MV-104A (amended) | 4/23/2023 | |
| 222-225 | NYC Transit Dept of Law | Personal Injury Claim Form (3rd copy, completed) | incident 4/23/2023 | **Total Amount Claimed $5,000,000** |
| 226-230 | NYC Comptroller | Personal Injury Claim Form | incident 4/23/2023 | insurance company Progressive, PO Box 22016; **Total Amount Claimed $5,000,000.00** |
| 231-234 | Progressive Max Ins Co | NF-10 denial of claim and instructions | 01/29/2024 | Claim 233582428-A121105; policy 950478050-3 |
| 235-235 | NYSCEF | Exhibit "I" slip | | |
| 236-236 | StolzenbergCortelli | Email to defense counsel (W. Morrissey) | 3/26/2024, fwd 4/8/2024 | |
| 237-246 | StolzenbergCortelli | Redlined amended summons and complaint | ~Mar 2024 | |
| 247-248 | NYSCEF / email | Exhibit "J": Morrissey reply refusing the stipulation | 3/26/2024 | |
| 249-257 | StolzenbergCortelli | Exhibit "K": proposed amended verified complaint (150940/2024) | 4/7/2024 | |
| 258-262 | StolzenbergCortelli / Sapini | Exhibit "L": Notice of Claim and verification | ~2024 (INFERRED) | against MTA, MTA Metro-North and Ferrara |

Tiling check: see the end of this file.

### (c) Bills and charges

| Source (file, page) | Provider | DOS | Line items (code: amount) | Printed total | Legibility / my check |
|---|---|---|---|---|---|
| doc-19 p244 | Montefiore Nyack Hospital, acct 8102502568 | 4/24/2023 | rev 0250 diazepam 5mg: 0.17; rev 0260 CPT 96372 injection: 281.00; rev 0351 CPT 70450 CT head: 3,323.00; rev 0352 CPT 72125 CT neck: 3,677.00; rev 0450 CPT 99284 ED visit lvl 4: 2,087.00; rev 0636 ketorolac x2: 1.99 | Total charges **$9,370.16**; "No Fault Adjustments" 05/01/23 **-$8,688.37**; current balance **$681.79** | All legible at 200 dpi. The line items add to 9,370.16 and the balance arithmetic matches. Coverage shown: "No Fault - Generic No Fault Non Elector List". |
| doc-20 pp52-56 | SportsCare Physical Therapy of NY, invoice #1159038319, acct 36737880 | 6/29/2023 to 12/14/2023 (21 visit dates) | Descriptions only, no CPT codes on the invoice. Recurring amounts: eval $331; manual therapy $300 (one $150); ther ex $177 or $354; neuromuscular re-ed $166; e-stim $105; hot/cold packs $81 | Printed "PLEASE PAY **$11,542.00**" | Typed and legible. I extracted 83 charge lines from OCR and spot-checked them against 200 dpi images (pp52, 54). Charges sum to $16,560.00. Progressive Auto payments total $580.14 and adjustments $4,437.86, all on the 6/29-7/20/2023 lines. 16,560.00 - 580.14 - 4,437.86 = 11,542.00, which matches the printed balance. CPT codes appear separately on the PT daily notes: 97110, 97140, 97112, 97010, G0283, 97163/97162. |
| doc-20 p171 | NY Sports & Joints / McCulloch Ortho (Capiola): **estimate for proposed** R shoulder arthroscopy, not a bill | proposed; dated 1/3/2024 | Surgeon $7,500; PA $500 (McCulloch); facility $3,800 (Bronx SC LLC); anesthesia $500 (Centurion Anesthesia); lab $250 (McCulloch); transportation no fee | No total printed | Legible at 200 dpi. My sum of the components is $12,550 (not printed on the page). |
| doc-19 p243 | Ciox Health (records copying, not medical) | invoice 6/22/2023 | 58 pages × $0.75 = 43.50; e-archive fee 2.00 | **$45.50** | Legible. |
| doc-19 pp59-61 | Advanced Rockland Chiropractic: NF-3 | 4/26/2023 | none: "SEE BILL ATTACHED" | none | No chiropractic bill is attached anywhere in either bundle. |

**Per-provider totals with every component legible:** Montefiore Nyack $9,370.16 charged and $681.79 balance; SportsCare PT $16,560.00 charged and $11,542.00 balance.
**Not found in any PDF:** bills or ledgers for Advanced Rockland Chiropractic, McCulloch/Capiola office visits, New Horizon Surgical Center (the 7/26/2023 surgery), HVRA/Mid Rockland MRIs, Lenox Hill Radiology, Kwan, Abramov, Miller EMG, or Montefiore physician professional fees. There are no UB-04 or CMS-1500 forms, no lien letters, and no Medicaid lien amount.

### (d) Facts that appear only in the scans

No text-native PDF contains any of these:
- **Medical charges and payments**: Montefiore $9,370.16 / -$8,688.37 / $681.79; SportsCare $11,542 balance; the $12,550 R shoulder surgery estimate components.
- **No-fault details**: Progressive policy no. 950478050(-3), claim 23-3582428, NAIC number (24279 in the doc-20 p231 OCR; doc-19 OCR reads 24273, so one digit is uncertain). Two partial NF-10 denials cut off PT after 10/25/2023 and chiro after 11/09/2023 and deny lost earnings; another NF-10 is dated 1/29/2024. Both the affidavit and the cross-motion affirmation say no-fault was **exhausted**. Doc-08 (text-native) names Progressive but not exhaustion.
- **Earlier settlement demand**: the 3/14/2024 Presentation of Claim demanded $5,000,000, and the NYC Transit and Comptroller claim forms say $5,000,000. The text-native PDFs only state the $10,000,000 cap in doc-08.
- **Third-party administrator**: Claims Service Bureau of NY (Carlene Schultz), file SIR068120, insured Metro North Railroad. Doc-56 shows the claim number and carrier name, but the TPA letter is only in the scans.
- **Procedure and venue**: the earlier action's history (Tsai J. dismissal, the cross motion, the refused stipulation emails), the Notice of Claim, and the letter to Judge Chin.
- **Plaintiff's own account**: hit the sidewalk; airbag malfunction; car damage over $9,000; Medicaid obtained after no-fault exhaustion; the defense passenger was "female" per the affidavit, while doc-40 names Kyle Pullano.
- **Clinical record**: treating-provider records (ED chart, chiro, PT, Kwan, Abramov, Capiola, EMG, MRI reports, operative report). The text-native files only describe these through the BOP and the defense IME record lists.
- **Prior attorney**: Mitchell J. Schroeder PC (Nyack) represented or assisted the plaintiff in 2023 before StolzenbergCortelli.
- **Missing pages**: complaint ¶¶6-16 are absent from the doc-01 scan.

### (e) Insurance carrier, policy number and coverage-limit mentions

| File | Page | Mention |
|---|---|---|
| doc-40 | p1 | "Insurance coverage information to be provided under separate cover." |
| doc-40 | p4 | Accident Report Cover Sheet: **Automobile Policy # HC2ECAP477M0330TCT19 - Travelers Indemnity** - Code 354 State of NY; distribution includes Claims Service Bureau and MTA Risk/Insurance Mgmt |
| doc-40 | p5 | MV accident report: "Company in which liability insurance carried / Policy No." fields are blank |
| doc-08 | p5 | No-fault through **Progressive Insurance Company**, PO Box 2930, Clinton IA; claim number blank |
| doc-08 | p7-8 | Plaintiff is a NYS Medicaid recipient; insurance demand "not applicable to plaintiff" |
| doc-05 | p12-14 | Defense demands for collateral-source and no-fault carrier information; CPLR 3101(f) insurance disclosure (primary, excess, umbrella) |
| doc-47 | p3-7 | Claim number 1805CS28142M (defense counsel file) |
| doc-55 | p3 | Claim# SIR068120 (D&D Associates) |
| doc-56 | p4 | Claim No SIR068120; **Carrier#: Claims Service Bureau** |
| doc-01 | p6 | Pleads that no-fault-reimbursable damages are not sought |
| doc-19 | p8 | Affirmation: no-fault benefits exhausted; Medicaid obtained |
| doc-19 | p26 | Affidavit: no-fault exhausted; Medicaid obtained |
| doc-19 | p34 | Semble IME addressed to Progressive, Claim 233582428.01 |
| doc-19 | p41-43, 205-224 | Capiola notes: insurance "NF - Progressive" |
| doc-19 | p51 ff. | Chiro SOAP header: Ins Co PROGRESSIVE, Claim 23 3582428 |
| doc-19 | p62 | Schroeder letter to Progressive: no-fault application and **under/uninsured motorist notice**; Claim 23-3582428 |
| doc-19 | p63 | NF-2: Progressive, policyholder Justin Sapini, **policy 950478050**, claim 23-3582428 |
| doc-19 | p176-183 | NF-10 partial denials, Progressive Max Ins Co, PO Box 2930 Clinton IA |
| doc-19 | p244 | Montefiore visit coverage: "No Fault - Generic No Fault Non Elector List" |
| doc-20 | p52-56 | SportsCare payments and adjustments by "Progressive Auto" |
| doc-20 | p192 | Claims Service Bureau: Third-Party Claims Administrator for Metro North Railroad, File SIR068120 |
| doc-20 | p200 | Presentation of Claim: encloses "a letter from the no fault carrier explaining that the policy has been exhausted" |
| doc-20 | p212-225 | NYC Transit claim forms: Progressive "Policy # 23-3582428 (CLAIM #)" |
| doc-20 | p230 | Comptroller form: Progressive Insurance, PO Box 22016 |
| doc-20 | p231 | NF-10, Progressive Max Ins Co, 01/29/2024, claim 233582428-A121105, policy 950478050-3 |

**No document states a coverage limit** (bodily-injury limit, no-fault/PIP limit, UM/SUM limit or excess/umbrella amount). The only policy numbers are Travelers HC2ECAP477M0330TCT19 (Metro-North auto) and Progressive 950478050 (plaintiff's auto/no-fault). Exhaustion of no-fault is stated, but the exhausted amount is not.

---

# COVERAGE LEDGER

## L1. Clio seed JSON and setup guide
| Input | Status | How |
|---|---|---|
| `about` | read fully | full JSON dump |
| `matter_stages` | read fully | full dump |
| `custom_fields` (16) | read fully | full dump |
| `contacts` (10) | read fully | full dump |
| `matter` | read fully | full dump |
| `relationships` (9) | read fully | full dump |
| `folders` (9) | read fully | full dump |
| `documents` (15) | read fully (metadata) + sha256/bytes verified for all 15 | file *contents* skipped by instruction (another agent) |
| `notes` (42) | read fully | every detail printed |
| `communications` (69) | read fully | every body printed |
| `tasks` (14) | read fully | full dump |
| `calendar_entries` (17) | read fully | every entry printed |
| `expenses` (5) | read fully | full dump |
| Guide pp1–2 | read fully | pdftotext + rendered images |
| Guide pp3–7 | read fully | pdftotext; values cross-checked automatically against JSON |
| Guide pp8–10, 16, 18 | read fully | pdftotext |
| Guide pp11–15, 17 (notes) | text-verified, not read line by line | automated check: every JSON note's detail, subject and date found on the page; row numbers mapped |
| Guide p19 (comms header) | read fully | pdftotext |
| Guide pp20–25 (comms) | text-verified, not read line by line | automated check: every body, subject and date matched; from → to direction checked only by the count of "You (firm user)" (70 = 69 rows + 1 tip), not row by row |
| Guide pp26–30 | read fully | pdftotext |
| `Sapini documents/*` contents | skipped | per instructions (sha256 only) |
| `_ocr/` folder | skipped | not an input to this task |

## L2. Case PDFs
| File | Status | How / dpi |
|---|---|---|
| hipaa-authorization | read fully | pdftotext |
| photo-id | read fully (as an image) | 120 dpi; identifying numbers deliberately not transcribed |
| doc-01 summons-complaint | read fully | OCR text (complete) for all 8 pages, plus all 8 pages viewed at about 120 dpi |
| doc-05 | read fully | pdftotext |
| doc-07 | read fully | pdftotext |
| doc-41 | read fully | pdftotext |
| doc-08 | read fully | pdftotext |
| doc-40 | read fully | pdftotext; pages 3-11 also viewed as images at 60 dpi (forms and photos) |
| doc-43 | read fully | pdftotext |
| doc-19 (250 pp) | every page viewed; segmented in full; selected pages read closely | 45 dpi contact sheets of 20 pages each, all 13 viewed; OCR (complete) headers parsed for every page; 110-200 dpi on pp 59, 60, 64, 90-97, 177, 243, 244. Chiro SOAP note bodies sampled, not read line by line. |
| doc-20 (262 pp) | every page viewed; segmented in full; selected pages read closely | 45 dpi contact sheets, all 14 viewed; OCR (complete) headers parsed for every page; 200 dpi on pp 52-56, 171, 232. ED chart and PT note bodies sampled, not read line by line. |
| doc-12 letter-to-judge | read fully | OCR plus image |
| doc-47 | read fully | pdftotext |
| doc-55 | case pages (1-7, 47) read fully; CV pp 8-46 skimmed | pdftotext; grepped the CV for case terms (none found) |
| doc-56 | read fully | pdftotext |

OCR status: tesseract OCR is **complete** for all 522 scanned pages (doc-01 8, doc-12 1, photo-id 1, doc-19 250, doc-20 262).

### Page-range tiling (scanned bundles)
The script reads both page-range tables above and confirms each one covers pages 1..N with no gaps or overlaps. It was run on this file:

```
$ python3 tile.py brief/_sapini-map-docs.md
doc-19: segments=72 N=250 gaps=[] overlaps=[] bad=[] -> PASS
doc-20: segments=35 N=262 gaps=[] overlaps=[] bad=[] -> PASS
```

Independent re-check by the orchestrator (separate regex parser over Part 2 tables):
```
doc-19 72 segments; pages 250 unique 250 missing [] dupes 0
doc-20 35 segments; pages 262 unique 262 missing [] dupes 0
```
Small scanned files tile trivially: doc-01 summons pp1-8, photo-id p1, doc-12 letter-to-judge p1 (all viewed + OCR'd).

## L3. Slides, transcript, and cross-checks
| Input | Status | How |
|---|---|---|
| `LDG - 8_30 LDG Hackathon.pdf` slides 1-20 | read fully | every slide viewed as image (110 dpi); slides 6, 11-13 at 200 dpi in 4 quadrants; see `slides-inventory.md` |
| `raw.md` (95 lines) | read fully | see `slides-inventory.md` "Said in raw.md but not on slides" |
| Folders `07 Insurance`, `09 Settlement` | n/a | defined in JSON `folders`, absent on disk (no directory, no files) |
| `.DS_Store` files | skipped | OS metadata |
| OCR `_ocr/` (522 txt) | complete | tesseract 300 dpi gray, one txt per page; 0 files under 50 bytes; verified by count |
| Spot-checks by orchestrator | done | JSON: SOL 2026-04-22, DOI 2023-04-23, Policy Limits custom-field text, Estimated Case Value 375000.0, expenses sum $1,410.00. OCR: ER p244 totals $9,370.16 / -$8,688.37 / $681.79; SportsCare doc-20 pp52-56 "PLEASE PAY $11,542.00" |
