"""Local SQLite store for ingested Clio data (D-001, D-006).

`raw` keeps every Clio record verbatim. Normalized tables hold the columns the app uses. Every row keeps
`clio_type` + `clio_id` so a fact can link back to its source record in Clio.
"""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "clio.db"
FILES_DIR = DATA_DIR / "files"

# table -> columns (besides clio_type, clio_id, matter_id, synced_at)
TABLES: dict[str, list[str]] = {
    "matters": [
        "display_number", "description", "status", "client_id", "client_name", "stage_id", "stage_name",
        "practice_area", "responsible_attorney", "originating_attorney", "open_date", "close_date",
        "statute_of_limitations_task_id", "folder_id", "created_at", "updated_at",
    ],
    "matter_stages": ["name", "stage_order", "practice_area_id"],
    "custom_fields": ["name", "parent_type", "field_type", "displayed", "deleted", "picklist_options"],
    "custom_field_values": ["parent_type", "parent_id", "custom_field_id", "field_name", "field_type", "value", "picklist_option"],
    "contacts": [
        "name", "type", "first_name", "last_name", "date_of_birth", "primary_email", "primary_phone",
        "company_name", "is_client", "created_at", "updated_at",
    ],
    "matter_contacts": ["contact_id", "name", "type", "relationship_name", "description", "is_client"],
    "relationships": ["contact_id", "contact_name", "description", "created_at", "updated_at"],
    "notes": ["subject", "detail", "date", "author_name", "contact_id", "created_at", "updated_at"],
    "communications": [
        "type", "subject", "body", "date", "received_at", "user_name", "senders", "receivers",
        "created_at", "updated_at",
    ],
    "tasks": [
        "name", "description", "status", "priority", "due_at", "completed_at", "statute_of_limitations",
        "task_type", "assignee_name", "assignee_type", "created_at", "updated_at",
    ],
    "calendar_entries": [
        "summary", "description", "location", "start_at", "end_at", "all_day", "event_type",
        "calendar_owner", "attendees", "created_at", "updated_at",
    ],
    "activities": [
        "type", "date", "quantity", "price", "total", "note", "expense_category", "activity_description",
        "vendor_id", "vendor_name", "user_name", "billed", "non_billable", "non_billable_total", "created_at",
        "updated_at",
    ],
    "folders": ["name", "parent_id", "root", "created_at", "updated_at"],
    "documents": [
        "name", "filename", "content_type", "size", "folder_id", "folder_name", "category",
        "version_id", "version_number", "received_at", "created_at", "updated_at",
        "local_path", "downloaded_size", "page_count", "text_pages",
    ],
    "users": ["name", "email", "enabled", "roles"],
}


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE IF NOT EXISTS raw (clio_type TEXT NOT NULL, clio_id INTEGER NOT NULL, matter_id INTEGER,"
        " json TEXT NOT NULL, synced_at TEXT NOT NULL, PRIMARY KEY (clio_type, clio_id))"
    )
    for table, cols in TABLES.items():
        extra = ", ".join(f'"{c}"' for c in cols)
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {table} (clio_type TEXT NOT NULL, clio_id INTEGER NOT NULL,"
            f" matter_id INTEGER, {extra}, synced_at TEXT NOT NULL, PRIMARY KEY (clio_type, clio_id))"
        )
    con.execute(
        "CREATE TABLE IF NOT EXISTS ingest_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, matter_id INTEGER,"
        " started_at TEXT, finished_at TEXT, requests INTEGER, api_version TEXT, counts TEXT)"
    )
    return con


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _cell(v):
    return json.dumps(v) if isinstance(v, (dict, list)) else v


def upsert(con, table: str, clio_type: str, records: list[tuple[dict, dict]], matter_id: int | None,
           synced_at: str) -> None:
    """records: (raw Clio record, normalized row). Raw goes to `raw`, the row to `table`."""
    cols = TABLES[table]
    col_sql = ", ".join(["clio_type", "clio_id", "matter_id", *[f'"{c}"' for c in cols], "synced_at"])
    marks = ", ".join("?" * (len(cols) + 4))
    for raw, row in records:
        con.execute(
            "INSERT OR REPLACE INTO raw VALUES (?, ?, ?, ?, ?)",
            (clio_type, raw["id"], matter_id, json.dumps(raw, sort_keys=True), synced_at),
        )
        con.execute(
            f"INSERT OR REPLACE INTO {table} ({col_sql}) VALUES ({marks})",
            (clio_type, raw["id"], matter_id, *[_cell(row.get(c)) for c in cols], synced_at),
        )


def prune(con, table: str, clio_type: str, matter_id: int, keep_ids: set[int]) -> int:
    """Delete this matter's rows that Clio no longer returns, so re-runs mirror Clio exactly."""
    rows = con.execute(
        f"SELECT clio_id FROM {table} WHERE clio_type = ? AND matter_id = ?", (clio_type, matter_id)
    ).fetchall()
    stale = [r[0] for r in rows if r[0] not in keep_ids]
    for cid in stale:
        con.execute(f"DELETE FROM {table} WHERE clio_type = ? AND clio_id = ?", (clio_type, cid))
        con.execute("DELETE FROM raw WHERE clio_type = ? AND clio_id = ?", (clio_type, cid))
    return len(stale)
