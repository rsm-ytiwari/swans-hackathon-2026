"""Pull one Clio matter completely into app/data/clio.db (+ document files). Read-only (D-001, D-004).

    uv run python -m app.ingest --find Sapini        # list matching matters and their ids
    uv run python -m app.ingest --matter <id>        # ingest that matter; safe to re-run
    uv run python -m app.ingest --matter <id> --no-files

Idempotent: records are upserted by (clio_type, clio_id); matter-scoped rows Clio no longer returns are
pruned; files already downloaded at the same version and size are skipped.
"""

import argparse
import json
import re
import sys

from app import store
from app.clio import fields as F
from app.clio.client import ClioClient


def _name(obj):
    return (obj or {}).get("name")


def _id(obj):
    return (obj or {}).get("id")


def _participants(items):
    return [{"id": p.get("id"), "name": p.get("name"), "type": p.get("type")} for p in items or []]


def _cfv_rows(values, parent_type, parent_id):
    return [
        (v, {
            "parent_type": parent_type, "parent_id": parent_id, "custom_field_id": _id(v.get("custom_field")),
            "field_name": v.get("field_name"), "field_type": v.get("field_type"), "value": v.get("value"),
            "picklist_option": (v.get("picklist_option") or {}).get("option"),
        })
        for v in values or []
    ]


def find_matters(client: ClioClient, query: str) -> list[dict]:
    return client.list("matters.json", query=query, fields=F.MATTER_LIST)


def resolve_matter_id(client: ClioClient, matter: str) -> int:
    if matter.isdigit():
        return int(matter)
    hits = find_matters(client, matter)
    if len(hits) != 1:
        listing = "\n".join(f"  {m['id']}  {m.get('display_number')}  {m.get('description')}" for m in hits)
        sys.exit(f"'{matter}' matched {len(hits)} matters; pass a numeric id:\n{listing}")
    return hits[0]["id"]


def _text_layer(path):
    """(page_count, pages_with_text) for PDFs, else (None, None)."""
    if path.suffix.lower() != ".pdf":
        return None, None
    import pymupdf

    with pymupdf.open(path) as doc:
        return doc.page_count, sum(1 for p in doc if len(p.get_text().strip()) >= 20)


def _safe(name: str) -> str:
    return re.sub(r"[^\w.\- ]+", "_", name).strip() or "file"


def ingest(client: ClioClient, matter_id: int, download_files: bool = True) -> dict[str, int]:
    con = store.connect()
    started = store.now()
    counts: dict[str, int] = {}

    def save(table, clio_type, records, mid=matter_id, prune=True):
        store.upsert(con, table, clio_type, records, mid, started)
        if prune and mid is not None:
            store.prune(con, table, clio_type, mid, {r[0]["id"] for r in records})
        counts[table] = len(records)

    # Matter + its custom field values + stage
    m = client.get(f"matters/{matter_id}.json", fields=F.MATTER)["data"]
    save("matters", "Matter", [(m, {
        "display_number": m.get("display_number"), "description": m.get("description"),
        "status": m.get("status"), "client_id": _id(m.get("client")), "client_name": _name(m.get("client")),
        "stage_id": _id(m.get("matter_stage")), "stage_name": _name(m.get("matter_stage")),
        "practice_area": _name(m.get("practice_area")),
        "responsible_attorney": _name(m.get("responsible_attorney")),
        "originating_attorney": _name(m.get("originating_attorney")),
        "open_date": m.get("open_date"), "close_date": m.get("close_date"),
        "statute_of_limitations_task_id": _id(m.get("statute_of_limitations")),
        "folder_id": _id(m.get("folder")), "created_at": m.get("created_at"), "updated_at": m.get("updated_at"),
    })])
    save("custom_field_values", "CustomFieldValue", _cfv_rows(m.get("custom_field_values"), "Matter", matter_id))

    stages = client.list("matter_stages.json", fields=F.MATTER_STAGE)
    save("matter_stages", "MatterStage", [(s, {"name": s.get("name"), "stage_order": s.get("order"),
                                               "practice_area_id": s.get("practice_area_id")}) for s in stages], None)
    cfs = client.list("custom_fields.json", fields=F.CUSTOM_FIELD)
    save("custom_fields", "CustomField", [(c, {
        "name": c.get("name"), "parent_type": c.get("parent_type"), "field_type": c.get("field_type"),
        "displayed": c.get("displayed"), "deleted": c.get("deleted"),
        "picklist_options": [o.get("option") for o in c.get("picklist_options") or []],
    }) for c in cfs], None)
    users = client.list("users.json", fields=F.USER)
    save("users", "User", [(u, {"name": u.get("name"), "email": u.get("email"), "enabled": u.get("enabled"),
                                "roles": u.get("roles")}) for u in users], None)

    # Contacts and how they relate to the matter
    rels = client.list("relationships.json", matter_id=matter_id, fields=F.RELATIONSHIP)
    save("relationships", "Relationship", [(r, {
        "contact_id": _id(r.get("contact")), "contact_name": _name(r.get("contact")),
        "description": r.get("description"), "created_at": r.get("created_at"), "updated_at": r.get("updated_at"),
    }) for r in rels])
    mcs = client.list(f"matters/{matter_id}/contacts.json", fields=F.MATTER_CONTACT)
    save("matter_contacts", "MatterContact", [(c, {
        "contact_id": c.get("id"), "name": c.get("name"), "type": c.get("type"),
        "relationship_name": c.get("relationship_name"), "description": c.get("description"),
        "is_client": c.get("is_client"),
    }) for c in mcs])

    # Matter records
    notes = client.list("notes.json", matter_id=matter_id, type="Matter", fields=F.NOTE)
    save("notes", "Note", [(n, {
        "subject": n.get("subject"), "detail": n.get("detail"), "date": n.get("date"),
        "author_name": _name(n.get("author")), "contact_id": _id(n.get("contact")),
        "created_at": n.get("created_at"), "updated_at": n.get("updated_at"),
    }) for n in notes])
    comms = client.list("communications.json", matter_id=matter_id, fields=F.COMMUNICATION)
    save("communications", "Communication", [(c, {
        "type": c.get("type"), "subject": c.get("subject"), "body": c.get("body"), "date": c.get("date"),
        "received_at": c.get("received_at"), "user_name": _name(c.get("user")),
        "senders": _participants(c.get("senders")), "receivers": _participants(c.get("receivers")),
        "created_at": c.get("created_at"), "updated_at": c.get("updated_at"),
    }) for c in comms])
    tasks = client.list("tasks.json", matter_id=matter_id, fields=F.TASK)
    save("tasks", "Task", [(t, {
        "name": t.get("name"), "description": t.get("description"), "status": t.get("status"),
        "priority": t.get("priority"), "due_at": t.get("due_at"), "completed_at": t.get("completed_at"),
        "statute_of_limitations": t.get("statute_of_limitations"), "task_type": _name(t.get("task_type")),
        "assignee_name": _name(t.get("assignee")), "assignee_type": (t.get("assignee") or {}).get("type"),
        "created_at": t.get("created_at"), "updated_at": t.get("updated_at"),
    }) for t in tasks])
    events = client.list("calendar_entries.json", matter_id=matter_id, fields=F.CALENDAR_ENTRY)
    save("calendar_entries", "CalendarEntry", [(e, {
        "summary": e.get("summary"), "description": e.get("description"), "location": e.get("location"),
        "start_at": e.get("start_at"), "end_at": e.get("end_at"), "all_day": e.get("all_day"),
        "event_type": _name(e.get("calendar_entry_event_type")),
        "calendar_owner": _name(e.get("calendar_owner")), "attendees": _participants(e.get("attendees")),
        "created_at": e.get("created_at"), "updated_at": e.get("updated_at"),
    }) for e in events])
    acts = client.list("activities.json", matter_id=matter_id, fields=F.ACTIVITY)
    save("activities", "Activity", [(a, {
        "type": a.get("type"), "date": a.get("date"), "quantity": a.get("quantity"), "price": a.get("price"),
        "total": a.get("total"), "note": a.get("note"), "expense_category": _name(a.get("expense_category")),
        "activity_description": _name(a.get("activity_description")), "vendor_id": _id(a.get("vendor")),
        "vendor_name": _name(a.get("vendor")), "user_name": _name(a.get("user")), "billed": a.get("billed"),
        "non_billable": a.get("non_billable"), "non_billable_total": a.get("non_billable_total"), "created_at": a.get("created_at"), "updated_at": a.get("updated_at"),
    }) for a in acts])
    for kind in sorted({a.get("type") for a in acts}):
        counts[f"activities.{kind}"] = sum(1 for a in acts if a.get("type") == kind)

    # Folders + documents. Union of matter_id filter and root-folder descendants, so nothing nested is missed.
    folders = client.list("folders.json", matter_id=matter_id, fields=F.FOLDER)
    if m.get("folder"):
        folders += client.list("folders.json", parent_id=m["folder"]["id"], scope="descendants", fields=F.FOLDER)
    folders = list({f["id"]: f for f in folders}.values())
    save("folders", "Folder", [(f, {"name": f.get("name"), "parent_id": _id(f.get("parent")), "root": f.get("root"),
                                    "created_at": f.get("created_at"), "updated_at": f.get("updated_at")})
                               for f in folders])
    docs = {d["id"]: d for d in client.list("documents.json", matter_id=matter_id, fields=F.DOCUMENT)}
    if m.get("folder"):
        for d in client.list("documents.json", parent_id=m["folder"]["id"], scope="descendants", fields=F.DOCUMENT):
            docs.setdefault(d["id"], d)
    prior = {r["clio_id"]: dict(r) for r in con.execute(
        "SELECT clio_id, version_id, local_path, downloaded_size, page_count, text_pages FROM documents"
        " WHERE matter_id = ?", (matter_id,))}
    doc_rows = []
    for d in docs.values():
        v = d.get("latest_document_version") or {}
        row = {
            "name": d.get("name"), "filename": d.get("filename"), "content_type": d.get("content_type"),
            "size": d.get("size"), "folder_id": _id(d.get("parent")), "folder_name": _name(d.get("parent")),
            "category": _name(d.get("document_category")), "version_id": v.get("id"),
            "version_number": v.get("version_number"), "received_at": d.get("received_at"),
            "created_at": d.get("created_at"), "updated_at": d.get("updated_at"),
        }
        old = prior.get(d["id"], {})
        path = store.FILES_DIR / str(matter_id) / f"{d['id']}__{_safe(d.get('filename') or d.get('name') or '')}"
        if download_files:
            fresh = (old.get("version_id") == v.get("id") and path.exists()
                     and path.stat().st_size == old.get("downloaded_size"))
            if not fresh:
                client.download(d["id"], path)
            row["local_path"] = str(path.relative_to(store.DATA_DIR))
            row["downloaded_size"] = path.stat().st_size
            row["page_count"], row["text_pages"] = (
                (old.get("page_count"), old.get("text_pages")) if fresh else _text_layer(path))
        else:
            row.update({k: old.get(k) for k in ("local_path", "downloaded_size", "page_count", "text_pages")})
        doc_rows.append((d, row))
    save("documents", "Document", doc_rows)

    # Full contact records for everyone linked to the matter
    contact_ids = {c.get("id") for c in mcs} | {_id(r.get("contact")) for r in rels} | {_id(m.get("client"))}
    contact_ids |= {_id(a.get("vendor")) for a in acts} | {_id(n.get("contact")) for n in notes}
    for c in comms:
        contact_ids |= {p.get("id") for p in (c.get("senders") or []) + (c.get("receivers") or [])
                        if p.get("type") == "Contact"}
    contact_ids.discard(None)
    contacts = []
    ids = sorted(contact_ids)
    for i in range(0, len(ids), 50):
        contacts += client.list("contacts.json", **{"ids[]": ids[i:i + 50]}, fields=F.CONTACT)
    save("contacts", "Contact", [(c, {
        "name": c.get("name"), "type": c.get("type"), "first_name": c.get("first_name"),
        "last_name": c.get("last_name"), "date_of_birth": c.get("date_of_birth"),
        "primary_email": c.get("primary_email_address"), "primary_phone": c.get("primary_phone_number"),
        "company_name": _name(c.get("company")), "is_client": c.get("is_client"),
        "created_at": c.get("created_at"), "updated_at": c.get("updated_at"),
    }) for c in contacts], None)
    contact_cfvs = [row for c in contacts for row in _cfv_rows(c.get("custom_field_values"), "Contact", c["id"])]
    store.upsert(con, "custom_field_values", "CustomFieldValue", contact_cfvs, None, started)
    counts["custom_field_values.Contact"] = len(contact_cfvs)

    con.execute(
        "INSERT INTO ingest_runs (matter_id, started_at, finished_at, requests, api_version, counts)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (matter_id, started, store.now(), client.request_count, client.api_version, json.dumps(counts)),
    )
    con.commit()
    con.close()
    return counts


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--matter", help="Clio matter id (or a search string that matches exactly one matter)")
    g.add_argument("--find", help="search matters by number/description and print their ids")
    ap.add_argument("--no-files", action="store_true", help="skip document downloads")
    args = ap.parse_args(argv)

    client = ClioClient()
    if args.find is not None:
        for mt in find_matters(client, args.find):
            print(f"{mt['id']}\t{mt.get('display_number')}\t{_name(mt.get('matter_stage'))}\t{mt.get('description')}")
        return
    matter_id = resolve_matter_id(client, args.matter)
    counts = ingest(client, matter_id, download_files=not args.no_files)
    print(f"matter {matter_id} ingested -> {store.DB_PATH.relative_to(store.DATA_DIR.parent.parent)}")
    for k, v in counts.items():
        print(f"  {k:<30} {v}")
    print(f"  {'(api requests)':<30} {client.request_count}")


if __name__ == "__main__":
    main()
