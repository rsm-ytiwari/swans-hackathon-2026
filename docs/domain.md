# Personal injury (PI) law: what you need to sound credible

## Case lifecycle (pre-litigation is where most ops pain lives)
1. **Intake:** a lead calls or fills a form. Screen for liability (who's at fault), injury + treatment,
   insurance and policy limits, statute of limitations (SOL), conflicts. Speed-to-lead decides who signs the client.
2. **Sign-up:** contingency-fee retainer (typically 33–40%) + HIPAA authorizations.
3. **Investigation:** police report, photos, witnesses; letters of representation (LOR) to insurers; claims opened.
4. **Treatment monitoring:** ER → primary care → PT/chiro → imaging → specialist, until MMI. The case
   manager watches for **treatment gaps**: adjuster software (Colossus) cuts value for gaps.
5. **Records & bills:** request records + itemized bills from ~6–8 providers per case.
   - **California:** an attorney holding a signed authorization must be given records within **5 days**,
     with costs for non-compliance (CA Evid Code §1158).
   - HIPAA's 30 days is the *patient's own* right of access, and *Ciox v. Azar* (2020) narrowed the
     third-party directive.
   - Reality: often 45–90 days. Staff chase incomplete productions.
   - Treat a request older than 30 days as a red flag, and anything past the CA 5-day deadline as leverage
     for a follow-up letter.
6. **Demand package:** medical chronology + specials total + pain-and-suffering narrative + demand, sent to the adjuster.
7. **Negotiation** with the adjuster.
8. **Litigation**, if it doesn't settle; must be filed before the SOL (CA: 2 years).
9. **Settlement → liens:** Medicare (conditional payment letter), Medicaid, ERISA plans (full
   reimbursement after *McCutchen*), provider LOP liens negotiated down.
10. **Disbursement:** settlement statement → fee, costs, liens, client net, paid from the IOLTA trust account.

**Roles:**
- Intake specialist: leads.
- **Case manager:** the most operationally consequential role. Owns records, treatment, client
  communication and demand-readiness. Carries 30–60 cases, or 60–100 with an assistant.
- Paralegal: chronologies, drafting.
- Attorney: valuation, negotiation.
- Lit team: once the case is filed.

## Money levers: how the firm gets paid
`Fee revenue = signed cases × avg settlement × fee % × % resolved` · Cost ≈ staff + marketing per signed case

| Lever | Typical pain | Metric |
|---|---|---|
| 1. More signed cases | Slow follow-up. Clio 2024: 40% of firms answered the phone, 33% email, 48% neither | conversion %, minutes to response |
| 2. Higher case value | Treatment gaps, missing bills, incomplete specials | $ value protected, gaps caught (days) |
| 3. Faster cycle time | Demand stuck waiting on records | days to demand / settlement |
| 4. Capacity per head | Case managers drowning | cases per case manager, payroll avoided |
| 5. Risk avoided | Missed SOL; PI plaintiff work is at or near the top for malpractice claims, ~⅓ of them deadline errors | deadlines at risk caught |
| 6. Client experience | "What's my status?" calls; communication failure is the #1 bar complaint; reviews drive referrals | calls deflected, update frequency, review score |

**Framing:** prefer capacity ("same team carries 25% more cases") and cycle time over raw "hours saved."
Hours saved still matter for burnout and turnover; just tie them to a lever.

## Time/leak numbers (mostly vendor-sourced, so treat as directional and say "industry estimates")
- Medical chronology: ~10–15 h for 400 pages from 6 providers; 40–60 h for 5,000 pages
- Demand drafting: 3–5 h of writing, 8–20 h including file assembly (most of it reconciling records)
- Treatment gaps are often discovered months after they form (EvenUp guide)

## Competitors: don't rebuild these in 6 hours
| Player | What it does |
|---|---|
| EvenUp | ~$2B valuation; demands, chronologies, claims intelligence |
| Eve | $1B valuation; plaintiff "AI OS": intake, chronologies, demands, nightly case audits |
| Supio | Records analysis, demands |
| Filevine LOIS | AI inside the case-management system |
| Precedent, CaseMark | Demand drafting |
| Finch | Pre-litigation ops with human paralegals |
| LlamaLab, ChartRequest | Records retrieval |
| Many vendors | Intake voice agents |

**Gaps:** operations and orchestration across many cases (open-loop tracking, actually sending the
follow-ups, exception alerts), firm-owned automations inside the firm's own stack, and cents-per-case cost.

## Vocabulary
- **BI** (bodily injury) liability coverage · **policy limits** (e.g. CA 15/30) · **PIP / MedPay** · **UM/UIM**
- **LOR** (letter of representation) · **specials** (economic damages) vs **generals** (pain and suffering)
- **MMI** (maximum medical improvement) · **treatment gap** · **LOP** (letter of protection) · **lien**
- **subrogation** · **CMS / MSP / CPL** (Medicare) · **ERISA** · **SOL** · **pre-lit vs lit**
- **demand package** · **medical chronology** · **UB-04 / CMS-1500** (bill forms) · **ICD-10 / CPT** codes
- **Colossus** · **adjuster** · **time-limited demand** · **IOLTA** · **speed-to-lead** · **cost per signed case**

## Compliance: one line in every pitch
- A human approves anything that leaves the firm (ABA Formal Op. 512; Rule 1.4 duty to communicate).
- Client-facing bots never give legal advice or case valuations (unauthorized practice of law).
- PHI goes only to vendors under a BAA with zero data retention, or stays local. The demo uses synthetic data only.
- Automated texts and calls to leads need consent (TCPA; Rule 7.3 solicitation).
