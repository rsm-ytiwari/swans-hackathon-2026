"""Background AI analysis per matter, so a page never blocks on a model call.

The first view of a new matter starts one thread that computes the bottom line and the red flags (both
cached afterwards). Pages render the code-computed blocks immediately and show "AI analysis running…"
until the thread finishes. Also usable from the command line to pre-compute:
    uv run python -m app.core.jobs --matter <id>
"""

import argparse
import threading
import time
from datetime import date

from app.core import digest, facts, flags

_lock = threading.Lock()
_state: dict[int, dict] = {}  # mid -> {"status": running|done|error, "started": t, "error": str}


def _run(mid: int, today: date) -> None:
    try:
        con = facts.connect()
        digest.bottom_line(con, mid, today)
        flags.compute(con, mid, today)
        status = {"status": "done"}
    except Exception as e:  # never let a model failure take the page down
        status = {"status": "error", "error": f"{type(e).__name__}: {str(e)[:200]}"}
    with _lock:
        _state[mid].update(status, finished=time.time())


def ensure(mid: int, today: date) -> dict:
    """Start the analysis for this matter if it has not run in this process; return its state."""
    with _lock:
        st = _state.get(mid)
        if st is None:
            st = _state[mid] = {"status": "running", "started": time.time()}
            threading.Thread(target=_run, args=(mid, today), daemon=True).start()
        return dict(st)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Pre-compute AI analysis (bottom line + red flags) for a matter.")
    ap.add_argument("--matter", type=int, required=True)
    args = ap.parse_args(argv)
    t0 = time.time()
    _state[args.matter] = {"status": "running"}
    _run(args.matter, date.today())
    print(_state[args.matter], f"{time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
