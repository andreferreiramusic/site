#!/usr/bin/env python3
"""Render the concert list into index.html from a published Google Sheet.

Run by .github/workflows/deploy.yml before the Pages artifact is uploaded, so
the dates ship as real markup that search engines can read, instead of being
fetched in the visitor's browser. Nothing is committed back: the generated rows
exist only in the deployed artifact, so index.html in git keeps whatever rows
were last hand-written there as a sensible fallback.

Setting up the sheet:
  File -> Share -> Publish to web -> choose the sheet -> Comma-separated
  values (.csv) -> Publish. Paste the resulting URL into SHEET_CSV_URL below,
  or set a repo variable of the same name (Settings -> Secrets and variables
  -> Actions -> Variables), which wins over the constant.

Columns (header row, case-insensitive, any order; only `date` is required):
  date      2026-10-18             ISO yyyy-mm-dd. Past dates are dropped.
  title     Bach Consort Wien      Portuguese / default title
  title_en  Solo recital           optional, falls back to title
  title_de  Solorezital            optional, falls back to title
  venue     Musikverein, Wien, AT  plain text, not translated
  tickets   https://...            optional, the link is omitted when blank

Failure is deliberately soft: if the sheet is unreachable or malformed the
script warns and leaves index.html alone, so a broken sheet degrades to
slightly stale dates rather than a failed deploy.
"""

import csv
import datetime as dt
import html
import io
import os
import re
import sys
import urllib.request

SHEET_CSV_URL = ""  # <- paste the published-to-web CSV URL here

MONTHS = {
    "pt": "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split(),
    "en": "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(),
    "de": "JAN FEB MÄR APR MAI JUN JUL AUG SEP OKT NOV DEZ".split(),
}
LANGS = ("pt", "en", "de")
BLOCK = re.compile(
    r"(<!-- concerts:start.*?-->\n)(.*?)(\s*<!-- concerts:end -->)",
    re.DOTALL,
)


def warn(msg):
    """Surface on the Actions run summary without failing the job."""
    print("::warning title=build_concerts::%s" % msg)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "andreferreira-site-build"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8-sig")


def parse(text):
    rows = []
    today = dt.date.today()
    for raw in csv.DictReader(io.StringIO(text)):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not row.get("date"):
            continue
        try:
            date = dt.date.fromisoformat(row["date"])
        except ValueError:
            warn("skipping row with unreadable date %r" % row["date"])
            continue
        if date < today:
            continue
        rows.append((date, row))
    rows.sort(key=lambda pair: pair[0])
    return rows


def safe_url(value):
    """Sheets are hand-edited; don't let a stray javascript: land in an href."""
    return value if value.lower().startswith(("http://", "https://")) else ""


def render(rows, indent="      "):
    out = ['%s<div class="clist">' % indent]
    for date, row in rows:
        titles = {"pt": row.get("title", "")}
        titles["en"] = row.get("title_en") or titles["pt"]
        titles["de"] = row.get("title_de") or titles["pt"]
        dates = {l: "%02d %s" % (date.day, MONTHS[l][date.month - 1]) for l in LANGS}

        def attrs(values):
            return " ".join('data-%s="%s"' % (l, html.escape(values[l], quote=True)) for l in LANGS)

        out.append('%s  <div class="crow">' % indent)
        out.append(
            '%s    <time class="date" datetime="%s" %s>%s</time>'
            % (indent, date.isoformat(), attrs(dates), html.escape(dates["pt"]))
        )
        out.append(
            '%s    <div class="title" %s>%s</div>'
            % (indent, attrs(titles), html.escape(titles["pt"]))
        )
        out.append('%s    <div class="plus">+</div>' % indent)
        out.append('%s    <div class="venue">%s</div>' % (indent, html.escape(row.get("venue", ""))))
        tickets = safe_url(row.get("tickets", ""))
        if tickets:
            out.append(
                '%s    <a class="tix" href="%s" target="_blank" rel="noopener" '
                'data-i18n="concerts.tickets">Bilhetes →</a>' % (indent, html.escape(tickets, quote=True))
            )
        out.append("%s  </div>" % indent)
    out.append("%s</div>" % indent)
    return "\n".join(out)


def main():
    url = os.environ.get("SHEET_CSV_URL", "").strip() or SHEET_CSV_URL
    if not url:
        print("No SHEET_CSV_URL set; leaving the concert rows in index.html as they are.")
        return 0

    try:
        rows = parse(fetch(url))
    except Exception as exc:
        warn("could not read the sheet (%s); keeping the existing concert rows" % exc)
        return 0

    if not rows:
        warn("the sheet has no upcoming dates; keeping the existing concert rows")
        return 0

    page = io.open("index.html", encoding="utf-8").read()
    if not BLOCK.search(page):
        warn("concerts:start/end markers missing from index.html; nothing written")
        return 0

    page = BLOCK.sub(lambda m: m.group(1) + render(rows) + m.group(3), page, count=1)
    io.open("index.html", "w", encoding="utf-8").write(page)
    print("Wrote %d upcoming concert(s) into index.html." % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
