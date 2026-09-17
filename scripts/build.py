#!/usr/bin/env python3
"""Writes the shared chrome and the concert rows into the pages, in place.

    python3 scripts/build.py

There is one file per page and it is the file you edit: index.html and
pages/*.html are real, complete, openable pages. The build only rewrites the
regions between marker comments:

    <!-- nav:start -->   …replaced…   <!-- nav:end -->

Everything outside those markers is yours and is never touched, so editing a
page needs no build at all. Run the build after changing templates/parts.html
(the shared head, header and footer) or data/events.csv.

It is also run by .github/workflows/deploy.yml, which is what keeps "upcoming"
honest: which events qualify is decided on the deploy date, not when the file
was last hand-edited.

Markers, all optional per page:
    head        the charset/viewport/stylesheet links
    nav         the whole <header>, with the current page marked
    footer      the <footer> and the script tag
    events:next        the next HOME_LIMIT upcoming events
    events:upcoming    every upcoming event
    events:past        the archive, newest first, without ticket links

Paths are relative rather than root-relative because the site is served from
a project subpath (…github.io/site/), where /assets/… would 404. In the shared
parts {{base}} resolves per page; inside a page's own content just write the
real relative path.
"""

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events  # noqa: E402

HOME_LIMIT = 4  # upcoming events shown on the home page

# key, file, i18n key, Portuguese fallback shown before main.js runs
NAV = [
    ("home",    "index.html",           "nav.home",    "Início"),
    ("about",   "pages/about.html",     "nav.about",   "Sobre"),
    ("guitar",  "pages/guitar.html",    "nav.guitar",  "Guitarra"),
    ("lute",    "pages/lute.html",      "nav.lute",    "Alaúde"),
    ("dates",   "pages/dates.html",     "nav.dates",   "Datas"),
    ("contact", "pages/contact.html",   "nav.contact", "Contacto"),
]

EMPTY = ('      <p class="note" data-i18n="concerts.none">'
         'Sem concertos anunciados de momento.</p>')
EMPTY_PAST = ('      <p class="note" data-i18n="dates.past.none">'
              'Ainda sem atuações em arquivo.</p>')


def parts():
    """Split templates/parts.html on its <!-- part:name --> headings."""
    text = io.open("templates/parts.html", encoding="utf-8").read()
    chunks = re.split(r"<!-- part:([\w-]+) -->\n", text)
    # chunks[0] is the file's leading comment; then name, body, name, body…
    return {chunks[i]: chunks[i + 1].strip("\n") for i in range(1, len(chunks) - 1, 2)}


def nav_links(current_key, base, indent="      "):
    out = []
    for key, path, i18n_key, label in NAV:
        href = base + path
        current = ' aria-current="page"' if key == current_key else ""
        out.append('%s<a href="%s"%s data-i18n="%s">%s</a>'
                   % (indent, href, current, i18n_key, label))
    return "\n".join(out)


def inject(text, name, payload):
    """Replace what sits between <!-- name:start --> and <!-- name:end -->.

    Returns (text, found). A page that doesn't carry the marker is left alone —
    that is how index.html gets events:next while pages/dates.html gets the
    other two, with no per-page configuration anywhere.
    """
    pat = re.compile(r"(<!-- %s:start -->\n)(.*?)([ \t]*<!-- %s:end -->)"
                     % (re.escape(name), re.escape(name)), re.DOTALL)
    if not pat.search(text):
        return text, False
    return pat.sub(lambda m: m.group(1) + payload + "\n" + m.group(3), text, count=1), True


def load_events():
    path = os.environ.get("EVENTS_CSV", "").strip() or events.EVENTS_CSV
    try:
        text = io.open(path, encoding="utf-8-sig").read()
    except OSError as exc:
        events.warn("could not read %s (%s); event blocks left as they are" % (path, exc))
        return None
    try:
        return events.split(events.parse(text))
    except Exception as exc:
        events.warn("could not parse %s (%s); event blocks left as they are" % (path, exc))
        return None


def main():
    part = parts()
    missing = [k for k in ("head", "header-open", "header-close", "footer") if k not in part]
    if missing:
        events.warn("templates/parts.html is missing part(s): %s" % ", ".join(missing))
        return 1

    split = load_events()
    blocks = {}
    if split is not None:
        upcoming, past = split
        blocks = {
            "events:next": events.render(upcoming[:HOME_LIMIT]) if upcoming else EMPTY,
            "events:upcoming": events.render(upcoming) if upcoming else EMPTY,
            # Past ticket links point at closed sales, so they are dropped.
            "events:past": events.render(past, tickets=False) if past else EMPTY_PAST,
        }

    for key, path, _i18n_key, _label in NAV:
        if not os.path.exists(path):
            events.warn("%s is listed in NAV but does not exist" % path)
            continue
        base = "" if key == "home" else "../"
        page = io.open(path, encoding="utf-8").read()
        filled = []

        page, ok = inject(page, "head", part["head"].replace("{{base}}", base))
        if ok:
            filled.append("head")
        nav = "\n".join([
            part["header-open"].replace("{{base}}", base),
            nav_links(key, base),
            part["header-close"].replace("{{base}}", base),
        ])
        page, ok = inject(page, "nav", nav)
        if ok:
            filled.append("nav")
        page, ok = inject(page, "footer", part["footer"].replace("{{base}}", base))
        if ok:
            filled.append("footer")
        for name, payload in blocks.items():
            page, ok = inject(page, name, payload)
            if ok:
                filled.append(name)

        io.open(path, "w", encoding="utf-8").write(page)
        print("  %-22s %s" % (path, ", ".join(filled) or "no markers"))

    if split is not None:
        print("Done — %d upcoming event(s) (%d on home), %d archived."
              % (len(split[0]), min(HOME_LIMIT, len(split[0])), len(split[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
