"""Shared web helpers: templates, 'today', formatting filters."""

import os
import re
from datetime import date
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.core import facts

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def today() -> date:
    """Real date by default. APP_TODAY=YYYY-MM-DD pins it, so a recorded demo replays identically."""
    pinned = os.getenv("APP_TODAY")
    return date.fromisoformat(pinned) if pinned else date.today()


def _as_date(v) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def money(v) -> str:
    try:
        return f"${float(v):,.2f}".replace(".00", "")
    except (TypeError, ValueError):
        return "—"


def nice_date(v) -> str:
    if not v:
        return "—"
    d = v if isinstance(v, date) else _as_date(v)
    if d is None:
        return str(v)  # not a date: show what the source says rather than fail
    return d.strftime("%b %-d, %Y")


def relative(days) -> str:
    if days is None:
        return ""
    if days == 0:
        return "today"
    return f"in {days} days" if days > 0 else f"{-days} days overdue"


def jdate(v) -> str:
    """"Apr 23 ’23" for compact timelines."""
    if not v:
        return "—"
    d = v if isinstance(v, date) else _as_date(v)
    if d is None:
        return str(v)  # not a date: show what the source says rather than fail
    return d.strftime("%b %-d ’%y")


def kmoney(v) -> str:
    """$375k / $118.4k / $950 for chart labels."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(v) >= 1000:
        k = v / 1000
        return f"${k:,.0f}k" if round(k, 1) == int(k) else f"${k:,.1f}k"
    return f"${v:,.0f}"


def doc_label(name) -> str:
    """Readable name for a stored file: "05-medical-bills__created__sportscare-pt-itemized-bill-2023-12-14.pdf"
    -> "Sportscare pt itemized bill". Display only; the source dialog still shows the real file."""
    s = str(name or "")
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    s = s.split("__")[-1]                          # drop "NN-folder__created__" / "doc-01__"
    s = re.sub(r"[-_ ]?\d{4}-\d{2}-\d{2}$", "", s)  # trailing date
    s = re.sub(r"^doc-\d+[-_ ]?", "", s)
    words = re.sub(r"[-_]+", " ", s).split()
    words = [_ABBREV.get(w.lower(), w) for w in words]
    # A last word that isn't a common document word is usually the author's surname: "(Katzman)".
    if len(words) >= 3 and words[-1].isalpha() and words[-1].lower() not in _DOC_WORDS and words[-1].islower():
        words = words[:-1] + [f"({words[-1].capitalize()})"]
    s = " ".join(words).strip()
    return (s[:1].upper() + s[1:]) if s else str(name or "")


_ABBREV = {"ime": "IME", "neuro": "neurology", "ortho": "orthopedic", "mri": "MRI", "emg": "EMG", "ncv": "NCV",
           "pt": "PT", "er": "ER", "pmr": "PM&R", "hipaa": "HIPAA", "id": "ID", "bop": "BOP"}
_DOC_WORDS = {"bill", "bills", "records", "record", "report", "reports", "complaint", "demands", "particulars",
              "answer", "authorization", "notes", "summary", "letter", "exchange", "review", "therapy", "center",
              "care", "imaging", "radiology", "neurology", "orthopedic", "orthopaedic", "surgery", "chart",
              "ledger", "statement", "photos", "photo", "retainer", "agreement", "notice", "claim", "deposition",
              "transcript", "order", "motion", "affidavit", "itemized", "itemised", "electrodiagnostics", "hospital",
              "discovery", "responses", "response", "interrogatories", "subpoena", "medical", "evaluation", "exam",
              "defenses", "defences", "demand", "judge", "court", "plaintiff", "defendant", "defendants", "client",
              "conference", "stipulation", "settlement", "release", "lien", "liens", "expenses", "costs", "intake"}


def short_name(name) -> str:
    """Display name without legal suffixes: "Acme Orthopaedic Surgical Services, PLLC" -> "Acme Orthopaedic
    Surgical". Display only; the record keeps the full name."""
    s = str(name or "")
    s = re.sub(r",?\s*\b(PLLC|P\.C\.|LLC|L\.L\.C\.)(?=$|[\s,.)])\.?", "", s)
    s = re.sub(r"\s*\bServices\b", "", s)
    return re.sub(r"\s{2,}", " ", s).strip(" ,") or str(name or "")


def sentence(text) -> str:
    """Sentence case for Title Case headlines ("Physical Therapy Discharge Status" -> "Physical therapy
    discharge status"). Titles already in sentence case keep their proper nouns untouched."""
    s = str(text or "")
    words = s.split()
    long_words = [w for w in words[1:] if len(w) > 3]
    if not long_words or sum(w[:1].isupper() for w in long_words) / len(long_words) < 0.6:
        return s
    out = [words[0]] + [w.lower() if w[:1].isupper() and w[1:] == w[1:].lower() else w for w in words[1:]]
    return " ".join(out)


def mdate(v) -> str:
    """"Oct 9" (no year) for near dates."""
    if not v:
        return "—"
    d = v if isinstance(v, date) else _as_date(v)
    if d is None:
        return str(v)  # not a date: show what the source says rather than fail
    return d.strftime("%b %-d")


templates.env.filters.update(short_name=short_name, sentence=sentence, mdate=mdate)
templates.env.filters.update(money=money, nice_date=nice_date, relative=relative, jdate=jdate,
                             kmoney=kmoney, doc_label=doc_label)


def serve_document(doc_id: int) -> FileResponse:
    path = facts.document_path(facts.connect(), doc_id)
    if not path or not Path(path).exists():
        raise HTTPException(404, "file not downloaded; run app.ingest")
    return FileResponse(path, media_type="application/pdf", content_disposition_type="inline")
