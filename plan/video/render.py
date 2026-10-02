"""Render slide9-thesis.html to an MP4 (30 fps, 1080p) plus key stills, frame by frame so it's crisp.
Run: uv run --no-project --with playwright --with imageio-ffmpeg python plan/video/render.py [--stills-only]"""
import subprocess, sys, tempfile
from pathlib import Path
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
DURATION, FPS = 10.0, 30
STILLS = {"1-slide9-verbatim": 1.2, "2-problem1": 3.9, "3-problem2": 5.5, "4-all-three": 9.8}

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1920, "height": 1080})
    page.goto((HERE / "slide9-thesis.html").as_uri())
    page.wait_for_load_state("networkidle")
    for name, t in STILLS.items():
        page.evaluate(f"seek({t})")
        page.screenshot(path=HERE / f"still-{name}.png")
    if "--stills-only" not in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(int(DURATION * FPS)):
                page.evaluate(f"seek({i / FPS})")
                page.screenshot(path=f"{tmp}/f{i:04d}.png")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                            "-i", f"{tmp}/f%04d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
                            str(HERE / "slide9-thesis.mp4")], check=True)
    b.close()
print("done")
