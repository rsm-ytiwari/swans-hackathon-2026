# Demo-day operations checklist

## Bring
- Chargers + an extension cord (a local 26B model drains the battery)
- Phone hotspot (venue wifi with 60 builders is unreliable)
- HDMI/USB-C adapter

## Build these into the app (cheap insurance)
- `DEMO_REPLAY=1` mode serves cached outputs from `app/cache/`. It must work with wifi off.
- An injectable "today" date, so ages and deadlines look the same live and in the video.
- A "Reset demo" button: restore the seed data, clear `st.cache_data` and `session_state`.
- Warm-up before the pitch:
  - Ollama model load (`keep_alive: "2h"`)
  - schema compile
  - prompt cache (1-hour TTL)
- Streamlit:
  - `layout="wide"`
  - browser zoom 125–150%
  - hide the sidebar
  - `client.showErrorDetails = false`
  - test on a mirrored 720p display

## Secrets and screen
- `.env` is gitignored. Before making the repo public: `git log -p | grep -iE "api_key|sk-|AIza"` must be empty.
- Never screen-share the API console. Set a spend limit; rotate keys after the event.
- Do Not Disturb on. Use a clean browser profile (no autofill, no bookmarks bar).

## Live link (only if the submission requires one)
- Streamlit Cloud can't run Ollama, so it needs a cloud provider fallback.
- Hosted apps sleep: open the link before judging.

## Backup video
- 1080p, ≤ 2 min, result on screen within 15 s.
- Upload unlisted; check the link in an incognito window.
