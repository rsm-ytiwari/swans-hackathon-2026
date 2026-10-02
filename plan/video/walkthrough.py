"""Record the product walkthrough (video beats after slide 9) straight from the running app, with on-screen cards.

Runs on a throwaway COPY of the repo (app data included) on port 8001, so sharing in the video never touches the
live demo, and the McCulloch share can be reset to "Not shared" every run. Frame by frame (30 fps, 1920x1080), so
the cursor, cards and scrolls are smooth no matter how slow the machine is.

    uv run --no-project --with playwright --with imageio-ffmpeg python plan/video/walkthrough.py
    -> plan/video/walkthrough.mp4 + plan/video/walk-*.jpg stills

Elements are found by visible text, so it survives restyling; if a label changes, fix the string below.
"""
import os, shutil, sqlite3, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PORT, FPS = 8001, 30
SAPINI, OKAFOR = 1811198093, 3410403215382988
BLOCKER_PROVIDER = "McCulloch"
C1, C2, C3, CN = "#ffb547", "#3ee6b0", "#ff7aa8", "#8fb6ff"   # same colours as slide9-thesis.html

LAYER_JS = r"""
window.__rec = (() => {
  let L;
  const css = `
    #__rec { position: fixed; inset: 0; width: 100vw; height: 100vh; max-width: none; max-height: none; margin: 0; padding: 0;
             border: 0; background: transparent; pointer-events: none; overflow: visible; color-scheme: light; }
    #__rec * { box-sizing: border-box; font-family: "SF Pro Display", -apple-system, system-ui, "Helvetica Neue", Arial, sans-serif; }
    #__rec .card { position: absolute; width: 560px; padding: 18px 22px 19px; border-radius: 16px; background: #010034; color: #fff;
             border: 2px solid var(--c); box-shadow: 0 14px 44px rgba(1,0,52,.35); display: flex; gap: 16px; opacity: 0; }
    #__rec .card b { flex: none; width: 38px; height: 38px; border-radius: 50%; background: var(--c); color: #010034; display: grid;
             place-items: center; font-size: 21px; font-weight: 800; }
    #__rec .card h3 { margin: 4px 0 0; font-size: 23px; line-height: 1.15; font-weight: 750; letter-spacing: -.01em; }
    #__rec .card p { margin: 7px 0 0; font-size: 16.5px; line-height: 1.35; color: #c9cdf0; }
    #__rec .ring { position: absolute; border: 3px solid var(--c); border-radius: 12px; opacity: 0;
             box-shadow: 0 0 0 6px color-mix(in srgb, var(--c) 22%, transparent), 0 0 30px color-mix(in srgb, var(--c) 45%, transparent); }
    #__rec .cur { position: absolute; width: 26px; height: 26px; left: 0; top: 0; filter: drop-shadow(0 2px 3px rgba(0,0,0,.35)); }
    #__rec .rip { position: absolute; width: 44px; height: 44px; margin: -22px 0 0 -22px; border-radius: 50%; border: 3px solid #3b2fe0; opacity: 0; }
    #__rec .end { position: absolute; inset: 0; background: #010034; color: #fff; opacity: 0; display: grid; place-content: center; text-align: center; }
    #__rec .end h1 { font-size: 64px; font-weight: 800; letter-spacing: -.02em; margin: 0; }
    #__rec .end .row { display: flex; gap: 14px; justify-content: center; margin-top: 30px; }
    #__rec .end .row span { padding: 9px 16px; border-radius: 999px; border: 2px solid var(--c); font-size: 18px; font-weight: 650; }
    #__rec .end p { margin: 30px 0 0; font-size: 20px; color: #aab0d8; }`;
  function layer() {
    if (L && L.isConnected) return L;
    L = document.createElement("div"); L.id = "__rec"; L.setAttribute("popover", "manual");
    L.innerHTML = `<style>${css}</style><div class="ring"></div><div class="card"></div><div class="rip"></div>
      <svg class="cur" viewBox="0 0 24 24"><path d="M4 2.5v17.2l4.6-4.4 3 6.6 3-1.4-3-6.4h6.3z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>
      <div class="end"></div>`;
    document.body.appendChild(L); L.showPopover(); return L;
  }
  const q = s => layer().querySelector(s);
  return {
    top() { const l = layer(); l.hidePopover(); l.showPopover(); },              // re-stack above a just-opened <dialog>
    cursor(x, y) { const c = q(".cur"); c.style.left = (x - 4) + "px"; c.style.top = (y - 2) + "px"; c.style.display = ""; },
    hideCursor() { q(".cur").style.display = "none"; },
    ripple(x, y, k) { const r = q(".rip"); r.style.left = x + "px"; r.style.top = y + "px";
                      r.style.opacity = 1 - k; r.style.transform = `scale(${0.4 + k})`; },
    card(html, color, pos, o) { const c = q(".card"); if (html !== null) { c.innerHTML = html; c.style.setProperty("--c", color);
        c.style.left = c.style.right = c.style.top = c.style.bottom = "";
        for (const [k, v] of Object.entries(pos)) c.style[k] = v + "px"; }
      c.style.opacity = o; c.style.transform = `translateY(${(1 - o) * 14}px)`; },
    ring(r, color, o) { const g = q(".ring"); if (r) { const p = 7; g.style.left = (r.x - p) + "px"; g.style.top = (r.y - p) + "px";
        g.style.width = (r.width + 2 * p) + "px"; g.style.height = (r.height + 2 * p) + "px"; g.style.setProperty("--c", color); }
      g.style.opacity = o; },
    end(html, o) { const e = q(".end"); if (html !== null) e.innerHTML = html; e.style.opacity = o; },
  };
})();
"""


class Rec:
    """Writes numbered JPEG frames; every helper advances video time by whole frames."""

    def __init__(self, page, frames: Path):
        self.page, self.dir, self.n, self.last = page, frames, 0, None
        self.cx, self.cy = 720, 430
        self.marks = {}

    def js(self, expr, *args):
        return self.page.evaluate(expr, list(args) if len(args) != 1 else args[0])

    def shot(self):
        path = self.dir / f"f{self.n:05d}.jpg"
        self.page.screenshot(path=path, type="jpeg", quality=93)
        self.last, self.n = path, self.n + 1

    def hold(self, sec):
        if self.last is None:
            self.shot()
        for _ in range(round(sec * FPS)):
            dst = self.dir / f"f{self.n:05d}.jpg"
            os.link(self.last, dst)
            self.n += 1

    def mark(self, name):              # remember a frame for a still
        self.shot(); self.marks[name] = self.last

    def ready(self):                   # after any navigation: overlay back, cursor where it was
        self.page.wait_for_load_state("networkidle")
        self.page.add_style_tag(content="html { scroll-behavior: auto !important; }")
        self.js("([x, y]) => __rec.cursor(x, y)", self.cx, self.cy)

    def move(self, x, y, dur=0.55):
        x0, y0, steps = self.cx, self.cy, max(1, round(dur * FPS))
        for i in range(1, steps + 1):
            k = i / steps; e = k * k * (3 - 2 * k)
            self.cx, self.cy = x0 + (x - x0) * e, y0 + (y - y0) * e
            self.js("([x, y]) => __rec.cursor(x, y)", self.cx, self.cy)
            self.shot()
        self.page.mouse.move(x, y)

    def box(self, loc):
        loc.scroll_into_view_if_needed()
        return loc.bounding_box()

    def click(self, loc, settle=0.6, dur=0.55):
        b = self.box(loc)
        x, y = b["x"] + min(b["width"] / 2, 60), b["y"] + b["height"] / 2
        self.move(x, y, dur)
        for i in range(5):
            self.js("([x, y, k]) => __rec.ripple(x, y, k)", x, y, i / 5); self.shot()
        self.js("([x, y]) => __rec.ripple(x, y, 1)", x, y)
        loc.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(int(settle * 1000))
        self.ready()
        self.js("() => __rec.top()")
        self.shot()

    def card(self, color, title, sub, num=None, pos=None, fade=0.3):
        pos = pos or {"left": 24, "bottom": 24}
        badge = f"<b>{num}</b>" if num else ""
        html = f"{badge}<div><h3>{title}</h3><p>{sub}</p></div>"
        steps = round(fade * FPS)
        for i in range(1, steps + 1):
            self.js("([h, c, p, o]) => __rec.card(h, c, p, o)", html if i == 1 else None, color, pos, i / steps); self.shot()

    def uncard(self, fade=0.2):
        steps = round(fade * FPS)
        for i in range(steps - 1, -1, -1):
            self.js("o => __rec.card(null, '', {}, o)", i / steps); self.shot()

    def ring(self, loc, color, fade=0.25):
        b = self.box(loc)
        steps = round(fade * FPS)
        for i in range(1, steps + 1):
            self.js("([r, c, o]) => __rec.ring(r, c, o)", b if i == 1 else None, color, i / steps); self.shot()

    def unring(self):
        self.js("() => __rec.ring(null, '', 0)")

    def scroll_to(self, y, dur=0.8):
        y0 = self.js("() => scrollY")
        steps = max(1, round(dur * FPS))
        for i in range(1, steps + 1):
            k = i / steps; e = k * k * (3 - 2 * k)
            self.js("y => scrollTo(0, y)", y0 + (y - y0) * e); self.shot()

    def scroll_to_el(self, loc, offset=90, dur=0.8):
        b = loc.bounding_box()
        top = b["y"] + self.js("() => scrollY") if b else 0
        self.scroll_to(max(0, top - offset), dur)


def prepare_copy(tmp: Path) -> subprocess.Popen:
    dst = tmp / "app-copy"
    subprocess.run(["rsync", "-a", "--exclude", ".venv", "--exclude", ".git", "--exclude", "Sapini Case Materials",
                    "--exclude", "prototype", "--exclude", "plan", f"{REPO}/", f"{dst}/"], check=True)
    con = sqlite3.connect(dst / "app/data/app.db")
    ids = [r[0] for r in con.execute("SELECT DISTINCT provider_id FROM publication WHERE matter_id = ? AND packet LIKE ?",
                                     (SAPINI, f"%{BLOCKER_PROVIDER}%"))]
    for pid in ids:
        toks = [r[0] for r in con.execute("SELECT token FROM publication WHERE matter_id = ? AND provider_id = ?", (SAPINI, pid))]
        con.executemany("DELETE FROM publication_view WHERE token = ?", [(t,) for t in toks])
        con.execute("DELETE FROM publication WHERE matter_id = ? AND provider_id = ?", (SAPINI, pid))
        con.execute("DELETE FROM share_policy WHERE matter_id = ? AND provider_id = ?", (SAPINI, pid))
    con.commit(); con.close()
    env = {**os.environ, "APP_PASSWORD": "", "APP_TODAY": "2026-10-02"}
    srv = subprocess.Popen(["uv", "run", "uvicorn", "app.web.main:app", "--port", str(PORT)], cwd=dst, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=2); return srv
        except Exception:
            time.sleep(1)
    srv.kill(); sys.exit("recording copy of the app did not start")


def warm(page, base):
    """Load each case until the AI blocks are filled from cache, so nothing is 'running' on camera."""
    for mid in (SAPINI, OKAFOR):
        for _ in range(40):
            page.goto(f"{base}/m/{mid}"); page.wait_for_load_state("networkidle")
            if "AI analysis running" not in page.content():
                break
            time.sleep(3)
        else:
            sys.exit(f"AI analysis for matter {mid} never finished; check the AI provider")


def film(r: Rec, base: str):
    pg = r.page
    # --- Matters home: every case, worst first
    pg.goto(f"{base}/"); r.ready()
    r.hold(0.6)
    r.card(CN, "Every case, worst first", "Read live from Clio, read-only. Each case says what's overdue and who it's waiting on.",
           pos={"right": 24, "bottom": 24})
    r.hold(2.6)
    r.uncard()
    r.click(pg.locator(f'a[href="/m/{SAPINI}"]').first)

    # --- 1. The case stalls, and nobody notices
    r.hold(0.5)
    r.ring(pg.get_by_text("BLOCKED", exact=True).first.locator(".."), C1)
    r.card(C1, "The case stalls, and nobody notices",
           "Top of the page: what's blocking it. The surgeon owes records and a surgery date, 38 days late.", num=1,
           pos={"left": 24, "bottom": 24})
    r.mark("1-blocked"); r.hold(3.4)
    r.unring(); r.uncard()
    r.scroll_to_el(pg.get_by_text("The case in 3 lines", exact=False).first, offset=70)
    r.card(C1, "The whole case in 3 lines, then what to do next",
           "AI writes the story once per update and caches it. Dates, deadlines and money are plain code.", num=1,
           pos={"right": 24, "bottom": 24})
    r.mark("2-three-lines"); r.hold(3.2)
    r.uncard()
    since = pg.locator("#since summary")
    r.scroll_to_el(pg.locator("#since"), offset=260)
    r.click(since, settle=0.5)
    r.card(C1, "Back after two weeks off?", "Only what changed since you last looked.", num=1, pos={"right": 24, "top": 24})
    r.hold(2.6)
    r.uncard()

    # --- 2. A fact nobody can check
    r.scroll_to(0, dur=0.7)
    r.click(pg.get_by_role("button", name="Open source").first, settle=0.9)
    r.card(C2, "A fact nobody can check", "Every line opens the note, email or PDF it came from.", num=2,
           pos={"left": 24, "bottom": 24})
    r.mark("3-source"); r.hold(2.8)
    r.uncard()
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300); r.shot()
    r.click(pg.get_by_text("Compare", exact=False).first, settle=0.7)
    r.card(C2, "Red flags you can verify", "AI reads the whole file for contradictions. A flag shows only if both quotes "
           "are found word for word in the records.", num=2, pos={"left": 24, "bottom": 24})
    r.mark("4-red-flag"); r.hold(3.6)
    r.uncard()
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300); r.shot()

    # --- 3. A provider left in the dark, or handed the whole file
    r.click(pg.get_by_text("Share with a provider").first)
    r.click(pg.get_by_text(BLOCKER_PROVIDER).first, settle=0.8)
    r.card(C3, "A provider left in the dark, or handed the whole file",
           "The attorney picks what each provider sees, with a live preview of their page.", num=3,
           pos={"right": 24, "bottom": 24})
    r.hold(2.8)
    r.uncard()
    never = pg.get_by_text("Never shared", exact=True).first.locator("..")
    r.ring(never, C3)
    r.card(C3, "Strategy never leaves the firm", "Notes, emails and case value can't be shared at all. "
           "Enforced on the server, not just hidden.", num=3, pos={"right": 24, "bottom": 24})
    r.mark("5-never-shared"); r.hold(3.2)
    r.unring(); r.uncard()
    r.click(pg.get_by_role("button", name="Approve & create link"), settle=1.0)
    r.card(C3, "Nothing leaves until the attorney approves", "Approve, and the provider gets a secure link.", num=3,
           pos={"right": 24, "bottom": 24})
    r.hold(2.4)
    r.uncard()
    link = pg.get_by_role("link", name="Open").first
    href = link.get_attribute("href")
    r.click(link, settle=0.3)
    pg.goto(href if href.startswith("http") else base + href); r.ready()
    r.hold(0.4)
    r.card(C3, "What the surgeon sees", "Is the case alive, what the firm needs from their office, their own bills. "
           "Nothing else.", num=3, pos={"right": 24, "bottom": 24})
    r.mark("6-provider-page"); r.hold(3.4)
    r.uncard()
    pg.goto(f"{base}/m/{SAPINI}"); r.ready()
    row = pg.locator("tr, li, div").filter(has_text=BLOCKER_PROVIDER).filter(has_text="opened").last
    r.scroll_to_el(row, offset=300, dur=0.7)
    r.ring(row, C3)
    r.card(C3, "And the firm sees it was opened", "What we shared with each provider, and whether anyone opened it.", num=3,
           pos={"left": 24, "top": 24})
    r.mark("7-opened"); r.hold(2.8)
    r.unring(); r.uncard()

    # --- Proof: nothing hardcoded
    pg.goto(f"{base}/m/{OKAFOR}"); r.ready()
    r.hold(0.4)
    r.click(pg.get_by_text("Compare", exact=False).first, settle=0.7)
    r.card(CN, "Nothing hardcoded", "A second, fictional case we wrote ourselves: a fresh brief, and the contradiction "
           "we planted, caught.", pos={"left": 24, "bottom": 24})
    r.mark("8-okafor"); r.hold(3.2)

    # --- End card
    r.js("() => __rec.hideCursor()")
    end = (f"<h1>Case Brief</h1><div class='row'><span style='--c:{C1}'>1 · Stalls get noticed</span>"
           f"<span style='--c:{C2}'>2 · Every fact checkable</span><span style='--c:{C3}'>3 · Providers informed, strategy kept</span></div>"
           "<p>Read-only from Clio · any matter · AI runs once per update, cached</p>")
    for i in range(1, 10):
        r.js("([h, o]) => __rec.end(h, o)", end if i == 1 else None, i / 9); r.shot()
    r.mark("9-end"); r.hold(3.0)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); frames = tmp / "frames"; frames.mkdir()
        srv = prepare_copy(tmp)
        try:
            with sync_playwright() as p:
                b = p.chromium.launch()
                ctx = b.new_context(viewport={"width": 1440, "height": 810}, device_scale_factor=4 / 3)
                ctx.add_init_script(LAYER_JS)
                page = ctx.new_page()
                base = f"http://127.0.0.1:{PORT}"
                warm(page, base)
                r = Rec(page, frames)
                film(r, base)
                b.close()
            print(f"{r.n} frames = {r.n / FPS:.1f} s")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                            "-i", str(frames / "f%05d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                            "-movflags", "+faststart", str(OUT / "walkthrough.mp4")], check=True)
            for old in OUT.glob("walk-*.jpg"):
                old.unlink()
            for name, f in r.marks.items():
                shutil.copy(f, OUT / f"walk-{name}.jpg")
        finally:
            srv.terminate()


if __name__ == "__main__":
    main()
