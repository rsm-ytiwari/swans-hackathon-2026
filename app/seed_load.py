"""Load ONE matter from a Clio-shaped seed file (request bodies with {{placeholders}}) into app/data/clio.db.

    uv run python -m app.seed_load <seed.json> [--docs <folder>]

Writes the same tables and clio_type names as app.ingest, so app.core.facts and the web app work unchanged,
with no Clio access. Ids are deterministic synthetic integers (hash of placeholder text + seed file name), so
re-loading is idempotent and two seed files never collide. The raw JSON of every row carries
"_seed": "seed:<filename>" to tell seed-loaded matters from live Clio ones. Sections may be missing or have extra
fields; unknown items are skipped with a warning.
"""

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path

from app import store
from app.ingest import _safe, _text_layer

PLACEHOLDER = re.compile(r"^\{\{\s*([a-z_]+)(?::(.*?))?\s*\}\}$")
SYNTH_USER = "Firm user (seed)"  # MOCK: seed files carry no user names, only {{user_id}}
SYNTH_CALENDAR = "Firm calendar (seed)"  # MOCK: same for {{calendar_id}}


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def synth_id(seed_name: str, key: str) -> int:
    """Stable positive integer < 2^53 from the seed file name plus any key (placeholder text, entity+index)."""
    digest = hashlib.sha256(f"{seed_name}|{key}".encode()).hexdigest()
    return int(digest[:13], 16) % (2**53 - 1) + 1  # 13 hex digits = 52 bits


class Loader:
    def __init__(self, seed: dict, seed_name: str, docs_dir: Path | None = None):
        self.seed = seed if isinstance(seed, dict) else {}
        self.name = seed_name
        self.docs_dir = docs_dir
        self.tag = f"seed:{seed_name}"
        self.matter_id = self.sid("{{matter_id}}")

    def sid(self, key: str) -> int:
        return synth_id(self.name, key)

    def resolve(self, v):
        """Replace every whole-string {{placeholder}} (recursively) with its synthetic integer id."""
        if isinstance(v, str):
            m = PLACEHOLDER.match(v.strip())
            return self.sid(v.strip()) if m else v
        if isinstance(v, list):
            return [self.resolve(x) for x in v]
        if isinstance(v, dict):
            return {k: self.resolve(x) for k, x in v.items()}
        return v

    def section(self, key: str) -> list[dict]:
        sec = self.seed.get(key)
        items = sec.get("items") if isinstance(sec, dict) else sec
        if items is None:
            if key not in ("matter",):
                warn(f"section '{key}' missing; skipped")
            return []
        out = []
        for i, it in enumerate(items if isinstance(items, list) else []):
            body = it.get("body") if isinstance(it, dict) else None
            if not isinstance(body, dict):
                warn(f"{key}[{i}] has no body; skipped")
                continue
            out.append({"index": i, "item": it, "body": body})
        return out

    def raw(self, rid: int, body: dict, **extra) -> dict:
        return {**self.resolve(body), **extra, "id": rid, "_seed": self.tag}

    def user_ref(self, p):
        """Participants as ingest stores them: [{"id","name","type"}], names from the loaded contacts."""
        out = []
        for x in p if isinstance(p, list) else []:
            if not isinstance(x, dict):
                continue
            pid = self.resolve(x.get("id"))
            kind = x.get("type") or "Contact"
            if kind == "User" or pid == self.sid("{{user_id}}"):
                out.append({"id": pid, "name": SYNTH_USER, "type": "User"})
            else:
                c = self.contacts.get(pid)
                out.append({"id": pid, "name": c["name"] if c else None, "type": c["type"] if c else kind})
        return out

    def practice_area_name(self, mb: dict):
        """The seed only has the placeholder; its `about` text names the area, e.g. The "X" practice area."""
        if not mb.get("practice_area"):
            return None
        about = self.seed.get("about") if isinstance(self.seed.get("about"), dict) else {}
        ph = about.get("placeholders") if isinstance(about.get("placeholders"), dict) else {}
        m = re.search(r'"([^"]+)"', str(ph.get("{{practice_area_id}}", "")))
        return mb.get("practice_area_name") or (m.group(1) if m else None)

    # ----- main -----
    def load(self, con) -> dict[str, int]:
        started = store.now()
        mid = self.matter_id
        counts: dict[str, int] = {}

        def save(table, clio_type, records, matter=mid, prune=True):
            store.upsert(con, table, clio_type, records, matter, started)
            if prune and matter is not None:
                store.prune(con, table, clio_type, matter, {r[0]["id"] for r in records})
            counts[table] = len(records)

        practice_area_id = self.sid("{{practice_area_id}}")
        user_id = self.sid("{{user_id}}")

        # stages (global, under the seed's synthetic practice area)
        ms = self.seed.get("matter_stages") if isinstance(self.seed.get("matter_stages"), dict) else {}
        stage_names = [s for s in ms.get("stages_in_order") or [] if isinstance(s, str)]
        save("matter_stages", "MatterStage", [(
            {"id": self.sid(f"{{{{stage:{n}}}}}"), "name": n, "order": i, "practice_area_id": practice_area_id,
             "_seed": self.tag},
            {"name": n, "stage_order": i, "practice_area_id": practice_area_id},
        ) for i, n in enumerate(stage_names)], None, prune=False)
        stage_by_id = {self.sid(f"{{{{stage:{n}}}}}"): n for n in stage_names}

        # custom fields
        cfs = self.section("custom_fields")
        field_by_id = {}
        recs = []
        for c in cfs:
            b = c["body"]
            if not b.get("name"):
                warn(f"custom_fields[{c['index']}] has no name; skipped")
                continue
            fid = self.sid(f"{{{{field:{b['name']}}}}}")
            field_by_id[fid] = b
            recs.append(({**b, "id": fid, "_seed": self.tag}, {
                "name": b["name"], "parent_type": b.get("parent_type"), "field_type": b.get("field_type"),
                "displayed": b.get("displayed"), "deleted": b.get("deleted", False),
                "picklist_options": [o.get("option") if isinstance(o, dict) else o
                                     for o in b.get("picklist_options") or []],
            }))
        save("custom_fields", "CustomField", recs, None, prune=False)

        # users: the seed only has {{user_id}}; one synthetic user so the usual joins have a row
        save("users", "User", [({"id": user_id, "name": SYNTH_USER, "_seed": self.tag},
                                {"name": SYNTH_USER, "email": None, "enabled": 1, "roles": ["seed"]})],
             None, prune=False)

        # contacts
        self.contacts: dict[int, dict] = {}
        client_ref = None
        crecs = []
        for c in self.section("contacts"):
            b, it = c["body"], c["item"]
            ref = it.get("ref")
            if ref is None:
                warn(f"contacts[{c['index']}] has no ref; skipped")
                continue
            cid = self.sid(f"{{{{contact:{ref}}}}}")
            ctype = b.get("type") or ("Company" if b.get("name") and not b.get("last_name") else "Person")
            first, last = b.get("first_name"), b.get("last_name")
            name = b.get("name") or " ".join(x for x in (first, last) if x) or str(ref)
            emails, phones = b.get("email_addresses") or [], b.get("phone_numbers") or []
            pick = lambda xs, flag: next((x for x in xs if isinstance(x, dict) and x.get(flag)),  # noqa: E731
                                         xs[0] if xs and isinstance(xs[0], dict) else {})
            comp = b.get("company")
            self.contacts[cid] = {"name": name, "type": ctype, "ref": ref}
            crecs.append(({**b, "id": cid, "name": name, "_seed": self.tag, "_ref": ref}, {
                "name": name, "type": ctype, "first_name": first, "last_name": last,
                "date_of_birth": b.get("date_of_birth"),
                "primary_email": pick(emails, "default_email").get("address"),
                "primary_phone": pick(phones, "default_number").get("number"),
                "company_name": comp.get("name") if isinstance(comp, dict) else comp,
                "is_client": 0,  # set below once the matter says who the client is
            }))
        mb = (self.seed.get("matter") or {}).get("body") if isinstance(self.seed.get("matter"), dict) else None
        if not isinstance(mb, dict):
            raise SystemExit("seed has no matter.body; nothing to load")
        client_id = self.resolve((mb.get("client") or {}).get("id"))
        for raw, row in crecs:
            row["is_client"] = 1 if raw["id"] == client_id else 0
        save("contacts", "Contact", crecs, None, prune=False)

        # matter
        stage_id = self.resolve((mb.get("matter_stage") or {}).get("id"))
        sol_task = next((t for t in self.section("tasks") if t["body"].get("statute_of_limitations")), None)
        sol_task_id = self.sid(f"tasks|{sol_task['index']}") if sol_task else None
        client = self.contacts.get(client_id)
        last = next((r[1]["last_name"] for r in crecs if r[0]["id"] == client_id), None)
        display = mb.get("display_number") or f"SEED-{str(mid)[-5:]}-{last or (client or {}).get('name') or 'matter'}"
        mrec = self.raw(mid, mb, display_number=display)
        save("matters", "Matter", [(mrec, {
            "display_number": display, "description": mb.get("description"), "status": mb.get("status"),
            "client_id": client_id, "client_name": client["name"] if client else None,
            "stage_id": stage_id, "stage_name": stage_by_id.get(stage_id),
            "practice_area": self.practice_area_name(mb),
            "responsible_attorney": SYNTH_USER, "originating_attorney": None,
            "open_date": mb.get("open_date"), "close_date": mb.get("close_date"),
            "statute_of_limitations_task_id": sol_task_id,
            "folder_id": self.sid("matter_folder"), "created_at": None, "updated_at": None,
        })], mid, prune=False)

        # custom field values on the matter
        recs = []
        for i, v in enumerate(mb.get("custom_field_values") or []):
            fid = self.resolve(((v or {}).get("custom_field") or {}).get("id"))
            f = field_by_id.get(fid)
            if f is None:
                warn(f"matter custom_field_values[{i}] references an unknown field; skipped")
                continue
            recs.append(({"id": self.sid(f"cfv|{f['name']}"), "custom_field": {"id": fid}, "value": v.get("value"),
                          "field_name": f["name"], "_seed": self.tag}, {
                "parent_type": "Matter", "parent_id": mid, "custom_field_id": fid, "field_name": f["name"],
                "field_type": f.get("field_type"), "value": v.get("value"), "picklist_option": None,
            }))
        save("custom_field_values", "CustomFieldValue", recs)

        # relationships + matter_contacts (the client is always linked, as Clio does)
        rrecs, mcrecs = [], []
        for r in self.section("relationships"):
            b = r["body"]
            cid = self.resolve((b.get("contact") or {}).get("id"))
            c = self.contacts.get(cid)
            if c is None:
                warn(f"relationships[{r['index']}] references an unknown contact; skipped")
                continue
            rrecs.append((self.raw(self.sid(f"relationships|{r['index']}"), b), {
                "contact_id": cid, "contact_name": c["name"], "description": b.get("description"),
                "created_at": None, "updated_at": None}))
            mcrecs.append(({"id": cid, "name": c["name"], "type": c["type"], "relationship_name": b.get("description"),
                            "_seed": self.tag}, {
                "contact_id": cid, "name": c["name"], "type": c["type"], "relationship_name": b.get("description"),
                "description": mb.get("description"), "is_client": 0}))
        if client:
            mcrecs = [m for m in mcrecs if m[0]["id"] != client_id]
            mcrecs.insert(0, ({"id": client_id, "name": client["name"], "type": client["type"],
                               "relationship_name": "Client", "_seed": self.tag}, {
                "contact_id": client_id, "name": client["name"], "type": client["type"],
                "relationship_name": "Client", "description": mb.get("description"), "is_client": 1}))
        save("relationships", "Relationship", rrecs)
        save("matter_contacts", "MatterContact", mcrecs)

        # notes
        recs = []
        for n in self.section("notes"):
            b = n["body"]
            cid = self.resolve((b.get("contact") or {}).get("id")) if isinstance(b.get("contact"), dict) else None
            recs.append((self.raw(self.sid(f"notes|{n['index']}"), b), {
                "subject": b.get("subject"), "detail": b.get("detail"), "date": b.get("date"),
                "author_name": SYNTH_USER, "contact_id": cid, "created_at": None, "updated_at": None}))
        save("notes", "Note", recs)

        # communications
        recs = []
        for c in self.section("communications"):
            b = c["body"]
            recs.append((self.raw(self.sid(f"communications|{c['index']}"), b), {
                "type": b.get("type"), "subject": b.get("subject"), "body": b.get("body"), "date": b.get("date"),
                "received_at": b.get("received_at") or b.get("date"), "user_name": SYNTH_USER,
                "senders": self.user_ref(b.get("senders")), "receivers": self.user_ref(b.get("receivers")),
                "created_at": None, "updated_at": None}))
        save("communications", "Communication", recs)

        # tasks
        recs = []
        for t in self.section("tasks"):
            b = t["body"]
            a = b.get("assignee") if isinstance(b.get("assignee"), dict) else {}
            recs.append((self.raw(self.sid(f"tasks|{t['index']}"), b), {
                "name": b.get("name"), "description": b.get("description"), "status": b.get("status"),
                "priority": b.get("priority") or "normal", "due_at": b.get("due_at"),
                "completed_at": b.get("completed_at"), "statute_of_limitations": int(bool(b.get("statute_of_limitations"))),
                "task_type": None, "assignee_name": SYNTH_USER if a else None, "assignee_type": a.get("type"),
                "created_at": None, "updated_at": None}))
        save("tasks", "Task", recs)

        # calendar entries
        recs = []
        for e in self.section("calendar_entries"):
            b = e["body"]
            recs.append((self.raw(self.sid(f"calendar_entries|{e['index']}"), b), {
                "summary": b.get("summary"), "description": b.get("description"), "location": b.get("location"),
                "start_at": b.get("start_at"), "end_at": b.get("end_at"), "all_day": int(bool(b.get("all_day"))),
                "event_type": None, "calendar_owner": SYNTH_CALENDAR, "attendees": self.user_ref(b.get("attendees")),
                "created_at": None, "updated_at": None}))
        save("calendar_entries", "CalendarEntry", recs)

        # expenses -> activities
        recs = []
        for x in self.section("expenses"):
            b = x["body"]
            try:
                qty = float(b.get("quantity") or 1)
                price = float(b["price"]) if b.get("price") is not None else float(b["total"])
            except (KeyError, TypeError, ValueError):
                warn(f"expenses[{x['index']}] has no usable price/total; skipped")
                continue
            total = float(b["total"]) if b.get("total") is not None else round(qty * price, 2)
            recs.append((self.raw(self.sid(f"expenses|{x['index']}"), b, total=total), {
                "type": b.get("type") or "ExpenseEntry", "date": b.get("date"), "quantity": qty, "price": price,
                "total": total, "note": b.get("note"), "expense_category": None, "activity_description": None,
                "vendor_id": None, "vendor_name": None, "user_name": SYNTH_USER, "billed": 0,
                "non_billable": 0, "non_billable_total": None, "created_at": None, "updated_at": None}))
        save("activities", "Activity", recs)
        counts["activities.ExpenseEntry"] = len(recs)

        # folders
        recs, folder_by_id = [], {}
        for f in self.section("folders"):
            b = f["body"]
            if not b.get("name"):
                warn(f"folders[{f['index']}] has no name; skipped")
                continue
            fid = self.sid(f"{{{{folder:{b['name']}}}}}")
            folder_by_id[fid] = b["name"]
            par = b.get("parent") or {}
            parent_id = self.sid("matter_folder") if par.get("type") == "Matter" else self.resolve(par.get("id"))
            recs.append(({**b, "id": fid, "_seed": self.tag}, {
                "name": b["name"], "parent_id": parent_id, "root": 0, "created_at": None, "updated_at": None}))
        save("folders", "Folder", recs)

        # documents (+ copy files into app/data/files/<matter_id>/ as ingest names them)
        self.documents(save, folder_by_id)
        con.execute(
            "INSERT INTO ingest_runs (matter_id, started_at, finished_at, requests, api_version, counts)"
            " VALUES (?, ?, ?, ?, ?, ?)", (mid, started, store.now(), 0, self.tag, json.dumps(counts)))
        return counts

    def documents(self, save, folder_by_id) -> None:
        sec = self.seed.get("documents") if isinstance(self.seed.get("documents"), dict) else {}
        base = self.docs_dir
        recs = []
        for d in self.section("documents"):
            b, it = d["body"], d["item"]
            rel = it.get("local_path") or ""
            did = self.sid(f"documents|{rel or d['index']}")
            filename = Path(rel).name or b.get("name") or f"doc{d['index']}"
            src = None
            if rel and base is not None:
                # local_path is "<docs folder name>/<subfolders>/<file>"; --docs points at that folder itself
                parts = Path(rel).parts
                for cand in (base / Path(*parts[1:]) if len(parts) > 1 else None, base / rel):
                    if cand is not None and cand.is_file():
                        src = cand
                        break
            pf = (b.get("parent") or {}).get("id") if isinstance(b.get("parent"), dict) else None
            folder_id = self.resolve(pf) if pf else None
            row = {
                "name": b.get("name") or filename, "filename": filename,
                "content_type": mimetypes.guess_type(filename)[0], "size": it.get("bytes"),
                "folder_id": folder_id, "folder_name": folder_by_id.get(folder_id), "category": None,
                "version_id": None, "version_number": 1, "received_at": b.get("received_at"),
                "created_at": None, "updated_at": None,
                "local_path": None, "downloaded_size": None, "page_count": None, "text_pages": None,
            }
            if src is not None:
                dest = store.FILES_DIR / str(self.matter_id) / f"{did}__{_safe(filename)}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                    shutil.copyfile(src, dest)
                row["local_path"] = str(dest.relative_to(store.DATA_DIR))
                row["downloaded_size"] = dest.stat().st_size
                try:
                    row["page_count"], row["text_pages"] = _text_layer(dest)
                except Exception as e:  # corrupt PDF: keep the record, no text layer info
                    warn(f"could not read {filename}: {e}")
            else:
                warn(f"file for document '{row['name']}' not found (docs folder: {base}); row kept without a file")
            recs.append(({**self.resolve(b), "id": did, "_seed": self.tag, "local_path": rel}, row))
        save("documents", "Document", recs)
        del sec


def load_seed(seed: dict, seed_name: str, docs_dir: Path | None = None, con=None) -> tuple[int, dict[str, int]]:
    own = con is None
    con = con or store.connect()
    loader = Loader(seed, seed_name, docs_dir)
    counts = loader.load(con)
    con.commit()
    if own:
        con.close()
    return loader.matter_id, counts


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("seed", help="seed JSON file shaped like a Clio request-body export")
    ap.add_argument("--docs", help="folder holding the documents (default: the seed's documents.files_location "
                                   "folder next to the seed file)")
    args = ap.parse_args(argv)
    path = Path(args.seed)
    seed = json.loads(path.read_text(encoding="utf-8"))
    docs = Path(args.docs) if args.docs else None
    if docs is None:
        loc = (seed.get("documents") or {}).get("files_location") if isinstance(seed.get("documents"), dict) else None
        m = re.search(r'"([^"]+)"', loc or "")
        docs = path.parent / m.group(1) if m else None
    mid, counts = load_seed(seed, path.name, docs)
    print(f"matter {mid} loaded from seed:{path.name} -> {store.DB_PATH.relative_to(store.DATA_DIR.parent.parent)}")
    for k, v in counts.items():
        print(f"  {k:<30} {v}")


if __name__ == "__main__":
    main()
