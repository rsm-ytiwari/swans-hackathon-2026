# Diagram brief (paste into Claude Design)

Make ONE slide-sized diagram (16:9) titled: **"<problem in ≤ 8 words>"**

## Layout
- Two horizontal bands, top to bottom:
  - **TODAY** (as-is)
  - **WITH <product name>** (to-be)
- Inside each band, steps flow left → right. **Max 7 boxes per band.**
- Swim lanes only inside the to-be band, max 3:
  - Firm staff
  - Our system
  - External: providers / insurers / client
- Box labels ≤ 5 words.

## Encoding (exactly 4 styles, legend in the bottom-right corner)
| Style | Meaning |
|---|---|
| Gray solid | Code (rules, dates, math) |
| Blue solid | AI (decide / extract / draft) |
| Orange solid, person icon | Human approves |
| Dashed outline, clock icon | Waiting on someone outside the firm |

## Annotations
- Under each box: time, e.g. `15 min` or `45 days wait`. In the to-be band, show `before → after`.
- Mark the 1–3 leaks in the TODAY band with a red marker and a short label.
- Right edge: 2 big numbers, e.g. **"45 → 3 days to catch a gap"**, **"+25% cases per case manager"**.

## Steps
TODAY:
1. <actor>: <action> · <time> · <leak?>
2. …

WITH <product>:
1. <lane>: <action> · <type: Code|AI|Human|Wait> · <before → after>
2. …

## Style
Clean and minimal, white background, one accent color per type, no gradients, readable from the back
of a room. No logos of real firms or vendors.

---
Fallback if Claude Design is unavailable: render the same steps as a Mermaid `flowchart LR` with two
`subgraph`s (TODAY / WITH), `classDef` for the 4 styles, and export to SVG.
