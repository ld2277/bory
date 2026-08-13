"""
Bory — publish one week's plan to GitHub Pages.

Same shape as the paperboy publisher, and same reason for existing: the Claude
run cannot push to GitHub, so it writes JSON to a shared Drive folder and this
runs on a GitHub runner to turn that into pages.

    index.html            this week   <- the home-screen target
    archive.html          past weeks, newest first
    weeks.json            manifest — the archive is built from this
    weeks/2026-08-17.html permanent copy of each week
    icon.png · .nojekyll · tools/
"""

import json
import os
import shutil
import subprocess

from bory_render import render_archive, render_week


def _run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"`{' '.join(cmd[:3])}` failed: "
                           f"{(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip()


def make_icon(path):
    """Off-white tile, moss B. The home-screen icon."""
    from PIL import Image, ImageDraw, ImageFont

    size = 180
    img = Image.new("RGB", (size, size), "#FCFBF9")
    draw = ImageDraw.Draw(img)
    font = None
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if os.path.exists(candidate):
            font = ImageFont.truetype(candidate, 104)
            break
    if font is None:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), "B", font=font)
    draw.text(
        ((size - box[2] + box[0]) / 2 - box[0], (size - box[3] + box[1]) / 2 - box[1]),
        "B", fill="#55684F", font=font,
    )
    draw.line([(40, size - 44), (size - 40, size - 44)], fill="#E6E3DD", width=2)
    img.save(path, "PNG")


class Repo:
    def __init__(self, path):
        self.path = path

    @classmethod
    def at(cls, path):
        os.makedirs(path, exist_ok=True)
        return cls(path)

    def publish(self, week):
        """File one week, rebuild index and archive. Returns the issue path."""
        date = week["date"]
        work = self.path
        os.makedirs(os.path.join(work, "weeks"), exist_ok=True)

        # Two renders: the landing copy at the root, the permanent copy one
        # directory down. Getting this wrong is how archive links quietly 404.
        with open(os.path.join(work, "weeks", f"{date}.html"), "w") as fh:
            fh.write(render_week(week, root="../"))
        with open(os.path.join(work, "index.html"), "w") as fh:
            fh.write(render_week(week, root=""))

        manifest = os.path.join(work, "weeks.json")
        weeks = []
        if os.path.exists(manifest):
            with open(manifest) as fh:
                weeks = json.load(fh)
        weeks = [w for w in weeks if w["date"] != date]
        weeks.append({
            "date": date,
            "dateline": week["dateline"],
            "href": f"weeks/{date}.html",
            "opening": week.get("opening", ""),
        })
        weeks.sort(key=lambda w: w["date"], reverse=True)
        with open(manifest, "w") as fh:
            json.dump(weeks, fh, indent=1)

        with open(os.path.join(work, "archive.html"), "w") as fh:
            fh.write(render_archive(weeks))

        open(os.path.join(work, ".nojekyll"), "w").close()
        icon = os.path.join(work, "icon.png")
        if not os.path.exists(icon):
            try:
                make_icon(icon)
            except Exception:
                pass  # an icon is a nicety; never fail a run over it

        return f"weeks/{date}.html"


def copy_tools(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name in ("bory_render.py", "bory_publish.py", "relay.py"):
        if os.path.exists(os.path.join(src, name)):
            shutil.copy(os.path.join(src, name), os.path.join(dst, name))
