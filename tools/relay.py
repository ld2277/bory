"""
Bory relay — runs on GitHub Actions, not in the Claude sandbox.

The Friday-evening Claude run writes the week's plan as JSON into a shared
Drive folder; this collects whatever is new and publishes it. Anything already
in weeks.json is skipped, so re-running is harmless and a missed week is picked
up by the next run.

Environment:
    BORY_OUTBOX     Drive folder id holding the week JSON (required)
    GDRIVE_API_KEY  optional; without it, the public folder view is scraped
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bory_publish import Repo  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.environ.get("BORY_OUTBOX", "").strip()
API_KEY = os.environ.get("GDRIVE_API_KEY", "").strip()

UA = {"User-Agent": "Mozilla/5.0 (bory relay)"}


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def list_outbox():
    """[(file_id, name)] for week-*.json in the outbox, oldest name first.

    The API key path is the supported one. The scrape exists so setup needs no
    Google Cloud project on day one; it reads the legacy embedded folder view,
    which returns plain HTML for any folder shared 'anyone with the link'.
    """
    if not OUTBOX:
        raise SystemExit("BORY_OUTBOX is not set")

    if API_KEY:
        query = urllib.parse.quote(f"'{OUTBOX}' in parents and trashed = false")
        url = (f"https://www.googleapis.com/drive/v3/files?q={query}"
               f"&key={API_KEY}&fields=files(id,name)&pageSize=200")
        found = [(f["id"], f["name"]) for f in json.loads(_get(url))["files"]]
    else:
        html = _get(f"https://drive.google.com/embeddedfolderview?id={OUTBOX}#list")
        found = re.findall(
            r'id="entry-([A-Za-z0-9_-]{20,})".*?flip-entry-title[^>]*>([^<]+)<',
            html.decode("utf-8", "replace"), re.S)

    weeks = [(i, n) for i, n in found
             if n.startswith("week-") and n.endswith(".json")]
    weeks.sort(key=lambda pair: pair[1])
    return weeks


def fetch(file_id):
    url = (f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={API_KEY}"
           if API_KEY else
           f"https://drive.google.com/uc?export=download&id={file_id}")
    return json.loads(_get(url))


def already_published(date):
    manifest = os.path.join(REPO_ROOT, "weeks.json")
    if not os.path.exists(manifest):
        return False
    with open(manifest) as fh:
        return any(w["date"] == date for w in json.load(fh))


def main():
    weeks = list_outbox()
    print(f"outbox: {len(weeks)} week file(s)")

    repo = Repo.at(REPO_ROOT)
    published = []

    for file_id, name in weeks:
        try:
            week = fetch(file_id)
        except Exception as exc:  # noqa: BLE001
            print(f"  {name}: could not fetch — {exc}")
            continue

        missing = [k for k in ("date", "dateline", "groceries", "meals")
                   if k not in week]
        if missing:
            print(f"  {name}: malformed, missing {missing} — skipped")
            continue

        if already_published(week["date"]):
            print(f"  {name}: already published")
            continue

        repo.publish(week)
        published.append(name)
        print(f"  {name}: published")

    print(f"published {len(published)}" if published else "nothing new")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"published={len(published)}\n")


if __name__ == "__main__":
    main()
