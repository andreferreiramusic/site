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
                                   Several nights that are NOT consecutive go
                                   in this one cell separated by ; or , —
                                   "2026-10-16; 2026-10-18" shows as "16 & 18
                                   OUT", and each night drops off once played.
  end_date  2026-10-18             optional, for a run of CONSECUTIVE days; the
                                   row shows as "16-18 OUT" and stays listed in
                                   full until the last day is past. Ignored if
                                   `date` already lists several dates.
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

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1-1bQn9qvNd3qO9F6_xqg5GrS9e9eqLN9YrKgq2iVgsg/edit?usp=drivesdk"  # <- paste the published-to-web CSV URL here

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


def read_date(value, where):
    """ISO only. Sheets exports a real date cell in the sheet's locale format
    (16/10/2026), which is ambiguous, so the column must be plain text."""
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        warn("%s: %r is not yyyy-mm-dd. If the sheet shows it as a date, set that "
             "column to Format -> Number -> Plain text and retype it." % (where, value))
        return None


def parse(text):
    rows = []
    today = dt.date.today()
    for raw in csv.DictReader(io.StringIO(text)):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not row.get("date"):
            continue

        # One date, or several separated by ; or , for nights that aren't
        # consecutive. A run of consecutive days uses end_date instead.
        parts = [p.strip() for p in row["date"].replace(";", ",").split(",") if p.strip()]
        days = [d for d in (read_date(p, "row %s" % row["date"]) for p in parts) if d]
        if not days:
            continue
        days.sort()

        kind = "list" if len(days) > 1 else "range"
        if row.get("end_date"):
            if kind == "list":
                warn("row %s lists several dates, so end_date is ignored" % row["date"])
            else:
                end = read_date(row["end_date"], "row %s end_date" % row["date"])
                if end is None:
                    pass
                elif end < days[0]:
                    warn("row %s: end_date is before date, showing it as a single day" % row["date"])
                else:
                    days = [days[0], end]

        if kind == "range":
            # A consecutive run stays listed, in full, until its last day is
            # past — it reads as one engagement spanning those days.
            if days[-1] < today:
                continue
        else:
            # Separate nights are separate performances, so the ones already
            # played drop off individually.
            days = [d for d in days if d >= today]
            if not days:
                continue

        rows.append((days[0], kind, days, row))
    rows.sort(key=lambda t: (t[0], t[2][-1]))
    return rows


def join_parts(parts):
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " & " + parts[-1]


def date_label(kind, days, lang, this_year):
    """Year is shown only when it isn't the current one, so the common case
    stays short ("07 NOV") while anything further out is unambiguous
    ("04 JUN 2028"). When every date in a row shares that year it is written
    once at the end ("29 JAN & 02 FEV 2027"); when a row straddles new year
    each side carries its own ("28 DEZ - 02 JAN 2027")."""
    months = MONTHS[lang]
    years = {d.year for d in days}

    if len(years) == 1:
        # One year for the whole row: state it once, at the end, or not at all.
        suffix = "" if days[0].year == this_year else " %d" % days[0].year
        yr = lambda d: ""
    else:
        suffix = ""
        yr = lambda d: " %d" % d.year if d.year != this_year else ""

    def day(d):
        return "%02d %s%s" % (d.day, months[d.month - 1], yr(d))

    if kind == "range":
        start, end = days[0], days[-1]
        if end == start:
            label = day(start)
        elif (start.year, start.month) == (end.year, end.month):
            label = "%02d–%02d %s" % (start.day, end.day, months[start.month - 1])
        else:
            label = "%s – %s" % (day(start), day(end))
    elif len({(d.year, d.month) for d in days}) == 1:
        label = "%s %s" % (
            join_parts(["%02d" % d.day for d in days]), months[days[0].month - 1],
        )
    else:
        label = join_parts([day(d) for d in days])

    return label + suffix


def safe_url(value):
    """Sheets are hand-edited; don't let a stray javascript: land in an href."""
    return value if value.lower().startswith(("http://", "https://")) else ""


def render(rows, indent="      "):
    this_year = dt.date.today().year
    out = ['%s<div class="clist">' % indent]
    for _, kind, days, row in rows:
        titles = {"pt": row.get("title", "")}
        titles["en"] = row.get("title_en") or titles["pt"]
        titles["de"] = row.get("title_de") or titles["pt"]
        dates = {l: date_label(kind, days, l, this_year) for l in LANGS}

        def attrs(values):
            return " ".join('data-%s="%s"' % (l, html.escape(values[l], quote=True)) for l in LANGS)

        out.append('%s  <div class="crow">' % indent)
        # datetime carries the first day; per spec it is the machine-readable
        # value and the visible text is free to be a range or a list. The extra
        # attribute is there for the schema.org markup if we add it later.
        span = ""
        if kind == "range" and days[-1] != days[0]:
            span = ' data-end="%s"' % days[-1].isoformat()
        elif kind == "list":
            span = ' data-dates="%s"' % " ".join(d.isoformat() for d in days)
        out.append(
            '%s    <time class="date" datetime="%s"%s %s>%s</time>'
            % (indent, days[0].isoformat(), span, attrs(dates), html.escape(dates["pt"]))
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
