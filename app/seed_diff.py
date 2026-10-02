"""Compare an ingested matter against the local seed file (D-008). Reference only; the app never reads
the seed. Prints documents and expenses that are in live Clio but not in the seed, plus text-layer status.

    uv run python -m app.seed_diff --matter <id>
"""

import argparse
import hashlib
import json
from pathlib import Path

from app import store

SEED = Path(__file__).resolve().parents[1] / "Sapini Case Materials" / "sapini-clio-data.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matter", type=int, required=True)
    args = ap.parse_args(argv)
    seed = json.loads(SEED.read_text())
    seed_docs = {i["body"]["name"]: i for i in seed["documents"]["items"]}
    seed_exp = {(e["body"]["date"], float(e["body"]["price"])) for e in seed["expenses"]["items"]}

    con = store.connect()
    docs = con.execute("SELECT * FROM documents WHERE matter_id = ? ORDER BY folder_name, name", (args.matter,)).fetchall()
    print(f"DOCUMENTS live={len(docs)} seed={len(seed_docs)}")
    print(f"{'':4}{'clio_id':>12}  {'folder':<26} {'pages':>5} {'text':>5}  name")
    for d in docs:
        tag = "NEW" if d["name"] not in seed_docs else ""
        if not tag and d["local_path"]:
            if _sha256(store.DATA_DIR / d["local_path"]) != seed_docs[d["name"]]["sha256"]:
                tag = "CHG"  # same name, different bytes
        layer = "-" if d["page_count"] is None else ("none" if d["text_pages"] == 0 else f"{d['text_pages']}")
        print(f"{tag:4}{d['clio_id']:>12}  {(d['folder_name'] or ''):<26} {d['page_count'] or '':>5} {layer:>5}  {d['name']}")
    missing = set(seed_docs) - {d["name"] for d in docs}
    if missing:
        print("IN SEED BUT NOT LIVE:", sorted(missing))

    exps = con.execute(
        "SELECT * FROM activities WHERE matter_id = ? AND type = 'ExpenseEntry' ORDER BY date", (args.matter,)
    ).fetchall()
    print(f"\nEXPENSES live={len(exps)} seed={len(seed_exp)}")
    for e in exps:
        tag = "" if (e["date"], float(e["price"] or 0)) in seed_exp else "NEW"
        note = (e["note"] or "").splitlines()[0][:90]
        print(f"{tag:4}{e['clio_id']:>12}  {e['date']}  {e['total'] or e['price']:>10}  {note}")


if __name__ == "__main__":
    main()
