#!/usr/bin/env python3
"""Reads data/events.csv and renders concert rows as HTML.

A library, not a script — scripts/build.py calls it while assembling the site.
The CSV is the full history: parse() returns every row it can read, and
split() divides them into upcoming and past against today's date, so the home
page can show the next few while the dates page also carries the archive.

Columns (header row, case-insensitive, any order; only `date` is required):
  date       2026-10-18            ISO yyyy-mm-dd.
                                   Several nights that are NOT consecutive go
                                   in this one cell separated by ; or , —
                                   "2026-10-16; 2026-10-18" shows as "16 & 18
                                   OUT", and each night drops off once played.
  end_date   2026-10-18            optional, for a run of CONSECUTIVE days; the
                                   row shows as "25 OUT - 03 NOV" and stays
                                   listed in full until the last day is past.
                                   Ignored if `date` already lists several.
  title      Concerto de Natal     Portuguese / default title
  title_en   Christmas Concert     optional, falls back to title
  title_de   Weihnachtskonzert     optional, falls back to title
  performers Bach Consort Wien     optional, shown under the title
  venue      Wiener Musikverein    optional
  city       Vienna                optional
  country    AT                    optional; venue/city/country are joined with
                                   commas, so any of them may be blank
  tickets    https://...           optional, the link is omitted when blank
"""

import csv
import datetime as dt
import html
import io
import sys

EVENTS_CSV = "data/events.csv"  # override with the EVENTS_CSV env var

MONTHS = {
    "pt": "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split(),
    "en": "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(),
    "de": "JAN FEB MÄR APR MAI JUN JUL AUG SEP OKT NOV DEZ".split(),
}
LANGS = ("pt", "en", "de")
# The site's own language: the one written into the HTML as plain text, which
# is what a search engine indexes and what shows before main.js has decided
# anything. Every other language rides along in data-pt/en/de attributes and
# the toggle swaps to it. One constant, read by build.py and press_kit.py too,
# so changing the site's language is this line plus the hand-written <title>
# and <meta name="description"> on each page.
SITE_LANG = "en"
# Prefix before the performer names. The names themselves never translate, so
# the whole string is carried inline per language rather than via a dictionary
# key — the same data-pt/en/de mechanism the dates and titles already use.
WITH = {"pt": "com", "en": "with", "de": "mit"}


def warn(msg):
    """Surface on the Actions run summary without failing the job."""
    print("::warning title=site-build::%s" % msg)


def read_date(value, where):
    """ISO only — 03/04 is ambiguous between two continents, so it is rejected
    rather than guessed at."""
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        warn("%s: %r is not yyyy-mm-dd, skipping it" % (where, value))
        return None


def parse(text):
    """Every readable row, sorted earliest first. No date filtering here.

    Sorting happens here rather than being left to the sheet: the CSV is
    hand-edited and new concerts get appended wherever there is room, so file
    order means nothing. Every caller gets date order whatever the file looks
    like, and split() keeps it that way.

    skipinitialspace because `, "Bach Consort Wien, Rubén Dubrovsky"` is the
    easy typo to make — a quote only opens a field when it is the very first
    character, so that stray space turns one quoted cell into three and shifts
    every column after it."""
    rows = []
    # A row with more cells than the header puts the surplus under the None
    # key as a list. One such row used to raise and take the whole list with
    # it — build.py caught that and left every page's concerts as they were,
    # so a single typo silently froze the dates rather than announcing itself.
    reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)
    for raw in reader:
        surplus = raw.pop(None, None)
        if surplus:
            warn("data row on line %d has %d cell(s) more than the %d columns "
                 "in the header (an unquoted comma?), skipping it: %r"
                 % (reader.line_num, len(surplus), len(reader.fieldnames or []),
                    raw.get("date") or raw.get("title") or ""))
            continue
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

        rows.append((days[0], kind, days, row))
    rows.sort(key=lambda t: (t[0], t[2][-1]))
    return rows


def split(rows, today=None):
    """Divide into (upcoming, past).

    A consecutive run counts as upcoming until its final day, and keeps its
    whole span on show — it reads as one engagement spanning those days.
    Separate nights are separate performances, so an upcoming row drops the
    ones already played and only becomes past once every night is behind it.
    """
    today = today or dt.date.today()
    upcoming, past = [], []
    for start, kind, days, row in rows:
        if days[-1] < today:
            past.append((start, kind, days, row))
        elif kind == "range":
            upcoming.append((start, kind, days, row))
        else:
            future = [d for d in days if d >= today]
            upcoming.append((future[0], kind, future, row))
    upcoming.sort(key=lambda t: (t[0], t[2][-1]))
    past.sort(key=lambda t: t[2][-1], reverse=True)  # most recent first
    return upcoming, past


def date_label(kind, days, lang, this_year, show_year=True):
    """Year is shown only when it isn't the current one, so the common case
    stays short ("07 NOV") while anything further out is unambiguous
    ("04 JUN 2028"). When every date in a row shares that year it is written
    once at the end ("29 JAN & 02 FEV 2027"); when a row straddles new year
    each side carries its own ("28 DEZ - 02 JAN 2027").

    show_year=False drops it entirely — used by the archive, where a year
    heading already stands above each group and repeating it on every row
    would just be noise."""
    months = MONTHS[lang]
    years = {d.year for d in days}

    if not show_year:
        suffix = ""
        yr = lambda d: ""
    elif len(years) == 1:
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
    else:
        # State each month once and list its days against it, so a set of
        # nights reads "26, 27, 29 OUT, 03 NOV" rather than repeating OUT.
        groups = []
        for d in days:
            key = (d.year, d.month)
            if groups and groups[-1][0] == key:
                groups[-1][1].append(d)
            else:
                groups.append((key, [d]))
        label = ", ".join(
            "%s %s%s" % (", ".join("%02d" % d.day for d in ds),
                         months[mm - 1], yr(ds[0]))
            for (_yy, mm), ds in groups
        )

    return label + suffix


def safe_url(value):
    """The CSV is hand-edited; don't let a stray javascript: land in an href."""
    return value if value.lower().startswith(("http://", "https://")) else ""


def render(rows, indent="      ", tickets=True, group_years=False,
           tickets_label="Bilhetes →"):
    """`tickets_label` is the Portuguese on the ticket link, which build.py
    passes in from content/site/tickets_pt.md — every other language comes
    from the dictionary at runtime, keyed by the data-i18n attribute.

    group_years inserts a heading whenever the year changes. Rows must
    already be ordered, which split() guarantees — the archive comes back
    newest first, so the headings count backwards."""
    this_year = dt.date.today().year
    out = ['%s<div class="clist">' % indent]
    seen_year = None
    for _, kind, days, row in rows:
        if group_years:
            # Grouped on the last day, the same key the archive is sorted by,
            # so a run that straddles new year files under the year it ended.
            year = days[-1].year
            if year != seen_year:
                out.append('%s  <h3 class="cyear">%d</h3>' % (indent, year))
                seen_year = year
        titles = {"pt": row.get("title", "")}
        titles["en"] = row.get("title_en") or titles["pt"]
        titles["de"] = row.get("title_de") or titles["pt"]
        # Grouped by year means a heading carries it, so the rows don't.
        dates = {l: date_label(kind, days, l, this_year, not group_years)
                 for l in LANGS}

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
        # Date and place share the first column, place on the line below.
        # Any of venue/city/country may be blank — a recording session has none.
        place = ", ".join(
            p for p in (row.get("venue", ""), row.get("city", ""), row.get("country", "")) if p
        )
        out.append('%s    <div class="when">' % indent)
        out.append(
            '%s      <time class="date" datetime="%s"%s %s>%s</time>'
            % (indent, days[0].isoformat(), span, attrs(dates), html.escape(dates[SITE_LANG]))
        )
        if place:
            out.append('%s      <div class="venue">%s</div>' % (indent, html.escape(place)))
        out.append("%s    </div>" % indent)
        performers = row.get("performers", "")
        out.append('%s    <div class="title">' % indent)
        out.append(
            '%s      <span class="tname" %s>%s</span>'
            % (indent, attrs(titles), html.escape(titles[SITE_LANG]))
        )
        if performers:
            withs = {l: "%s %s" % (WITH[l], performers) for l in LANGS}
            out.append(
                '%s      <span class="performers" %s>%s</span>'
                % (indent, attrs(withs), html.escape(withs[SITE_LANG]))
            )
        out.append("%s    </div>" % indent)
        href = safe_url(row.get("tickets", "")) if tickets else ""
        if href:
            out.append(
                '%s    <a class="tix" href="%s" target="_blank" rel="noopener" '
                'data-i18n="concerts.tickets">%s</a>'
                % (indent, html.escape(href, quote=True), html.escape(tickets_label))
            )
        out.append("%s  </div>" % indent)
    out.append("%s</div>" % indent)
    return "\n".join(out)
