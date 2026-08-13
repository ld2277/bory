# Bory

Weekly meal prep plans, written by the `bory-assistant` Claude skill and
published here as a single page: four tabs — Groceries, Breakfast, Lunch,
Dinner — with a grocery list that ticks off and remembers what you ticked.

- **This week:** https://ld2277.github.io/bory/
- **Past weeks:** https://ld2277.github.io/bory/archive.html

## How it gets here

The Claude run cannot push to GitHub — its sandbox proxies git and refuses
credentials for repos outside the session's authorised set. So the plan travels
as JSON through a shared Google Drive folder, and
`.github/workflows/publish.yml` collects it and publishes.

    Claude run (Fri 18:00 ET)  ->  Drive outbox/week-YYYY-MM-DD.json
    GitHub Action (18:20)      ->  weeks/*.html + index + archive

`tools/bory_render.py` owns the design. Change the layout there, not in the
skill.

## The tick state

Checkboxes persist in the browser's localStorage, keyed by the week's date, so
a new week starts clean and you never have to clear last week's ticks. The
state lives on the device you shop with — ticking on your phone does not tick
on your laptop, which is the behaviour you want for a shopping list.

## Configuration

- Repository **variable** `BORY_OUTBOX` — the Drive folder id holding the week
  JSON. The folder must be shared "anyone with the link".
- Repository **secret** `GDRIVE_API_KEY` — optional. Without it the relay reads
  the folder's public listing, which works but is unofficial.
