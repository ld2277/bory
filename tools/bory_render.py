"""
Bory — the weekly meal plan as one page.

Four tabs: Groceries, Breakfast, Lunch, Dinner. The grocery list ticks off and
remembers what you ticked, keyed by week, so a new week starts clean without
you clearing anything.

Design is Nordic-minimal: warm off-white, near-black text, one moss accent used
only where it carries meaning (the active tab, a checked line), hairlines
instead of boxes, and a lot of air. No shadows, no cards, no rounded corners
beyond a hint. The restraint is the design.

    render_week(week)  -> str   the plan as a standalone page
    render_archive(ws) -> str   past weeks, newest first
"""

import json
import re
from html import escape

# ---------------------------------------------------------------- palette

PAPER = "#FCFBF9"
INK = "#1A1A18"
MUTED = "#8C8880"
FAINT = "#B4B0A8"
LINE = "#E6E3DD"
ACCENT = "#55684F"
ACCENT_SOFT = "#EEF1EC"

SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', "
        "Helvetica, Arial, sans-serif")

STYLE = f"""
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
  margin: 0; background: {PAPER}; color: {INK};
  font-family: {SANS}; font-size: 16px; line-height: 1.6;
  font-weight: 400; -webkit-font-smoothing: antialiased;
}}
.wrap {{ max-width: 620px; margin: 0 auto; padding: 40px 22px 80px; }}

/* ---- header ---- */
.mast {{
  font-size: 11px; text-transform: uppercase; letter-spacing: 2.4px;
  color: {MUTED}; margin: 0 0 26px;
}}
h1 {{
  font-size: 30px; font-weight: 500; letter-spacing: -0.4px;
  line-height: 1.2; margin: 0 0 14px;
}}
.opening {{ color: {INK}; margin: 0; max-width: 52ch; }}
.meta {{
  font-size: 13px; color: {MUTED}; margin: 18px 0 0;
  display: flex; flex-wrap: wrap; gap: 4px 14px;
}}
.meta b {{ font-weight: 500; color: {INK}; }}

details.prep {{ margin: 26px 0 0; border-top: 1px solid {LINE}; }}
details.prep summary {{
  cursor: pointer; list-style: none; padding: 14px 0;
  font-size: 11px; text-transform: uppercase; letter-spacing: 1.6px;
  color: {MUTED};
}}
details.prep summary::-webkit-details-marker {{ display: none; }}
details.prep summary::after {{ content: " +"; color: {FAINT}; }}
details.prep[open] summary::after {{ content: " \\2212"; }}
details.prep ol {{ margin: 0 0 20px; padding-left: 20px; color: {INK}; }}
details.prep li {{ margin-bottom: 8px; }}

/* ---- tabs ---- */
nav.tabs {{
  position: sticky; top: 0; z-index: 10; background: {PAPER};
  display: flex; gap: 2px; margin: 30px 0 0;
  border-bottom: 1px solid {LINE};
}}
nav.tabs button {{
  flex: 1; appearance: none; background: none; border: 0;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  font-family: inherit; font-size: 11px; text-transform: uppercase;
  letter-spacing: 1.4px; color: {MUTED}; cursor: pointer;
  padding: 15px 2px 12px; min-height: 46px;
}}
nav.tabs button[aria-selected="true"] {{
  color: {INK}; border-bottom-color: {ACCENT};
}}
section[role="tabpanel"] {{ padding-top: 30px; }}
section[hidden] {{ display: none; }}

/* ---- groceries ---- */
.count {{
  font-size: 12px; color: {MUTED}; display: flex;
  justify-content: space-between; align-items: baseline;
  padding-bottom: 14px; border-bottom: 1px solid {LINE};
}}
.count button {{
  appearance: none; background: none; border: 0; padding: 4px 0;
  font-family: inherit; font-size: 12px; color: {MUTED};
  cursor: pointer; text-decoration: underline;
  text-underline-offset: 3px; text-decoration-color: {LINE};
}}
.count button:hover {{ color: {INK}; }}
.sec {{
  font-size: 11px; text-transform: uppercase; letter-spacing: 1.8px;
  color: {ACCENT}; margin: 32px 0 4px;
}}
label.row {{
  display: flex; gap: 14px; align-items: flex-start;
  padding: 13px 0; border-bottom: 1px solid {LINE}; cursor: pointer;
}}
label.row input {{
  appearance: none; flex: 0 0 auto; width: 19px; height: 19px;
  margin: 3px 0 0; border: 1.5px solid {FAINT}; border-radius: 2px;
  background: transparent; cursor: pointer; position: relative;
}}
label.row input:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
label.row input:checked::after {{
  content: ""; position: absolute; left: 5.5px; top: 1.5px;
  width: 4px; height: 9px; border: solid #fff;
  border-width: 0 1.75px 1.75px 0; transform: rotate(45deg);
}}
.txt {{ flex: 1 1 auto; min-width: 0; }}
.item {{ display: block; }}
.amt {{ display: block; font-size: 13.5px; color: {MUTED}; }}
.note {{ display: block; font-size: 12.5px; color: {FAINT}; font-style: italic; }}
.price {{
  flex: 0 0 auto; font-size: 13.5px; color: {MUTED};
  font-variant-numeric: tabular-nums; padding-top: 1px;
}}
label.row.done .item, label.row.done .amt, label.row.done .price {{
  color: {FAINT}; text-decoration: line-through;
  text-decoration-color: {FAINT};
}}
label.row.done .note {{ opacity: .55; }}

.totals {{ margin-top: 36px; border-top: 1.5px solid {INK}; padding-top: 4px; }}
.totals div {{
  display: flex; justify-content: space-between; gap: 16px;
  padding: 9px 0; border-bottom: 1px solid {LINE}; font-size: 14px;
}}
.totals div:last-child {{ border-bottom: 0; font-weight: 500; color: {INK}; }}
.totals span:first-child {{ color: {MUTED}; }}
.totals span:last-child {{ font-variant-numeric: tabular-nums; }}
.totals div:last-child span {{ color: {INK}; }}

/* ---- recipes ---- */
h2 {{ font-size: 23px; font-weight: 500; letter-spacing: -0.3px; margin: 0 0 8px; line-height: 1.25; }}
.rmeta {{
  font-size: 12px; text-transform: uppercase; letter-spacing: 1.3px;
  color: {MUTED}; margin: 0 0 30px;
  display: flex; flex-wrap: wrap; gap: 4px 14px;
}}
h3 {{
  font-size: 11px; text-transform: uppercase; letter-spacing: 1.8px;
  color: {ACCENT}; font-weight: 400; margin: 34px 0 2px;
}}
ul.ing {{ list-style: none; padding: 0; margin: 0; }}
ul.ing li {{ padding: 10px 0; border-bottom: 1px solid {LINE}; }}
ol.method {{ padding-left: 22px; margin: 8px 0 0; }}
ol.method li {{ padding: 7px 0; }}
ol.method li::marker {{ color: {FAINT}; font-size: 13px; }}
.notes {{
  margin: 30px 0 0; padding: 18px 0 0; border-top: 1px solid {LINE};
  font-size: 14px; color: {MUTED};
}}
.notes b {{ color: {INK}; font-weight: 500; }}
.empty {{ color: {MUTED}; font-style: italic; }}

/* ---- footer / archive ---- */
.foot {{
  margin-top: 60px; padding-top: 16px; border-top: 1px solid {LINE};
  font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;
}}
.foot a {{ color: {MUTED}; text-decoration: none; border-bottom: 1px solid {LINE}; }}
.foot a:hover {{ color: {INK}; }}
.week {{ padding: 20px 0; border-bottom: 1px solid {LINE}; }}
.week a {{ font-size: 19px; color: {INK}; text-decoration: none; font-weight: 500; }}
.week a:hover {{ color: {ACCENT}; }}
.week p {{ margin: 5px 0 0; color: {MUTED}; font-size: 14.5px; }}

@media (max-width: 480px) {{
  .wrap {{ padding: 30px 17px 70px; }}
  h1 {{ font-size: 26px; }}
  nav.tabs button {{ font-size: 10px; letter-spacing: 1px; }}
  .price {{ font-size: 13px; }}
}}
"""

SCRIPT = """
(function () {
  var KEY = document.body.dataset.week;
  var tabs = [].slice.call(document.querySelectorAll('nav.tabs button'));
  var panels = [].slice.call(document.querySelectorAll('section[role=tabpanel]'));

  var nav = document.querySelector('nav.tabs');

  function show(name, fromClick) {
    tabs.forEach(function (t) {
      t.setAttribute('aria-selected', String(t.dataset.tab === name));
    });
    panels.forEach(function (p) { p.hidden = p.id !== 'panel-' + name; });
    if (fromClick) {
      if (history.replaceState) history.replaceState(null, '', '#' + name);
      // Park the tab bar at the top rather than jumping to the page top —
      // otherwise every tab switch means scrolling past the header again.
      nav.scrollIntoView({ block: 'start' });
    }
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { show(t.dataset.tab, true); });
  });

  // --- grocery ticks, remembered per week ---
  var boxes = [].slice.call(document.querySelectorAll('label.row input'));
  var counter = document.getElementById('count');

  function store(k, v) {
    try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); }
    catch (e) { /* private mode: ticks work, they just don't persist */ }
  }
  function load(k) {
    try { return localStorage.getItem(k); } catch (e) { return null; }
  }
  function tally() {
    var n = boxes.filter(function (b) { return b.checked; }).length;
    if (counter) {
      counter.textContent = n + ' of ' + boxes.length +
        (n === boxes.length && boxes.length ? ' — done' : ' picked up');
    }
  }
  boxes.forEach(function (b) {
    var k = 'bory:' + KEY + ':' + b.value;
    if (load(k) === '1') { b.checked = true; }
    b.closest('label').classList.toggle('done', b.checked);
    b.addEventListener('change', function () {
      b.closest('label').classList.toggle('done', b.checked);
      store(k, b.checked ? '1' : null);
      tally();
    });
  });
  tally();

  var reset = document.getElementById('reset');
  if (reset) reset.addEventListener('click', function () {
    boxes.forEach(function (b) {
      b.checked = false;
      b.closest('label').classList.remove('done');
      store('bory:' + KEY + ':' + b.value, null);
    });
    tally();
  });

  var initial = (location.hash || '').replace('#', '');
  show(tabs.some(function (t) { return t.dataset.tab === initial; })
       ? initial : 'groceries', false);
})();
"""

TABS = [("groceries", "Groceries"), ("breakfast", "Breakfast"),
        ("lunch", "Lunch"), ("dinner", "Dinner")]


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def _head(title, week_key="", root=""):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Bory">
<meta name="theme-color" content="{PAPER}">
<link rel="apple-touch-icon" href="{root}icon.png">
<title>{escape(title)}</title>
<style>{STYLE}</style>
</head><body data-week="{escape(week_key, quote=True)}"><div class="wrap">
"""


def _meal(meal, label):
    if not meal:
        return f'<p class="empty">No {label.lower()} this week.</p>'
    bits = [b for b in (
        meal.get("servings"), meal.get("time"),
        f'{meal["protein"]} protein' if meal.get("protein") else None,
        f'{meal["fibre"]} fibre' if meal.get("fibre") else None,
        meal.get("cuisine"),
    ) if b]
    out = [f'<h2>{escape(meal["name"])}</h2>']
    if bits:
        out.append('<p class="rmeta">' +
                   "".join(f"<span>{escape(b)}</span>" for b in bits) + "</p>")
    if meal.get("ingredients"):
        out.append("<h3>Ingredients</h3><ul class=\"ing\">")
        out += [f"<li>{escape(i)}</li>" for i in meal["ingredients"]]
        out.append("</ul>")
    if meal.get("method"):
        out.append("<h3>Method</h3><ol class=\"method\">")
        out += [f"<li>{escape(s)}</li>" for s in meal["method"]]
        out.append("</ol>")
    if meal.get("notes"):
        out.append(f'<p class="notes">{escape(meal["notes"])}</p>')
    return "\n".join(out)


def render_week(week, root=""):
    key = week.get("date", "")
    title = f'Bory — {week.get("dateline", "")}'
    out = [_head(title, key, root)]

    out.append('<p class="mast">Meal prep</p>')
    out.append(f'<h1>{escape(week.get("dateline", ""))}</h1>')
    if week.get("opening"):
        out.append(f'<p class="opening">{escape(week["opening"])}</p>')

    meta = week.get("meta") or {}
    if meta:
        pairs = [("Protein", meta.get("protein")), ("Fibre", meta.get("fibre")),
                 ("Till", meta.get("till")), ("Recurring", meta.get("recurring"))]
        out.append('<p class="meta">' + "".join(
            f"<span>{escape(k)} <b>{escape(v)}</b></span>"
            for k, v in pairs if v) + "</p>")

    if week.get("prep_order"):
        out.append('<details class="prep"><summary>Prep order</summary><ol>')
        out += [f"<li>{escape(s)}</li>" for s in week["prep_order"]]
        out.append("</ol></details>")

    out.append('<nav class="tabs" role="tablist">')
    for slug, label in TABS:
        out.append(
            f'<button role="tab" data-tab="{slug}" aria-selected="false" '
            f'aria-controls="panel-{slug}">{label}</button>')
    out.append("</nav>")

    # --- groceries ---
    out.append('<section role="tabpanel" id="panel-groceries" hidden>')
    out.append('<div class="count"><span id="count"></span>'
               '<button id="reset" type="button">Uncheck all</button></div>')
    for section in week.get("groceries", []):
        out.append(f'<p class="sec">{escape(section["section"])}</p>')
        for item in section.get("items", []):
            box_id = _slug(section["section"] + "-" + item["item"])
            price = f'<span class="price">{escape(item["price"])}</span>' \
                if item.get("price") else ""
            amount = f'<span class="amt">{escape(item["amount"])}</span>' \
                if item.get("amount") else ""
            note = f'<span class="note">{escape(item["note"])}</span>' \
                if item.get("note") else ""
            out.append(
                f'<label class="row"><input type="checkbox" value="{box_id}">'
                f'<span class="txt"><span class="item">{escape(item["item"])}</span>'
                f"{amount}{note}</span>{price}</label>")
    if week.get("totals"):
        out.append('<div class="totals">')
        for total in week["totals"]:
            out.append(f'<div><span>{escape(total["label"])}</span>'
                       f'<span>{escape(total["value"])}</span></div>')
        out.append("</div>")
    out.append("</section>")

    meals = week.get("meals") or {}
    for slug, label in TABS[1:]:
        out.append(f'<section role="tabpanel" id="panel-{slug}" hidden>')
        out.append(_meal(meals.get(slug), label))
        out.append("</section>")

    out.append(f'<div class="foot"><a href="{root}archive.html">Past weeks</a></div>')
    out.append(f"</div><script>{SCRIPT}</script></body></html>")
    return "\n".join(out)


def render_archive(weeks, root=""):
    out = [_head("Bory — Past weeks", "", root)]
    out.append('<p class="mast">Meal prep</p><h1>Past weeks</h1>')
    for week in weeks:
        peek = week.get("opening", "")
        if len(peek) > 140:
            peek = peek[:140].rsplit(" ", 1)[0] + "…"
        out.append(
            f'<div class="week">'
            f'<a href="{escape(week["href"], quote=True)}">{escape(week["dateline"])}</a>'
            + (f"<p>{escape(peek)}</p>" if peek else "") + "</div>")
    out.append(f'<div class="foot"><a href="{root}index.html">This week</a></div>')
    out.append("</div></body></html>")
    return "\n".join(out)
