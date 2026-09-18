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
    events:past        the archive, newest first, grouped by year,
                       without ticket links
    video              the page's video from data/videos.csv, matched on the
                       page key (about, guitar, lute, dates, contact, home)

Paths are relative rather than root-relative because the site is served from
a project subpath (…github.io/site/), where /assets/… would 404. In the shared
parts {{base}} resolves per page; inside a page's own content just write the
real relative path.
"""

import csv
import html
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events  # noqa: E402

HOME_LIMIT = 4  # upcoming events shown on the home page
VIDEOS_CSV = "data/videos.csv"  # override with the VIDEOS_CSV env var

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


# A YouTube id is 11 characters of this alphabet. Validated because it is
# interpolated straight into a URL and an iframe src.
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{8,16}$")


def video_id(value):
    """Accept a bare id or any of the usual YouTube URL shapes."""
    value = value.strip()
    m = re.search(r"(?:youtu\.be/|v=|/embed/|/shorts/)([A-Za-z0-9_-]{8,16})", value)
    if m:
        return m.group(1)
    return value if VIDEO_ID.match(value) else ""


def load_videos():
    """{page key: {video_id, caption}} from data/videos.csv, or None if unreadable."""
    path = os.environ.get("VIDEOS_CSV", "").strip() or VIDEOS_CSV
    try:
        text = io.open(path, encoding="utf-8-sig").read()
    except OSError as exc:
        events.warn("could not read %s (%s); video blocks left as they are" % (path, exc))
        return None
    out = {}
    for raw in csv.DictReader(io.StringIO(text)):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        page = row.get("page", "").lower()
        vid = video_id(row.get("video_id", ""))
        if not page:
            continue
        if not vid:
            events.warn("%s: %r is not a usable YouTube id, skipping the %s video"
                        % (path, row.get("video_id", ""), page))
            continue
        out[page] = {"id": vid, "caption": row.get("caption", "")}
    return out


def render_video(video, indent="  "):
    """Poster only; main.js swaps in the iframe on click."""
    vid = html.escape(video["id"], quote=True)
    return "\n".join([
        '%s<section class="band">' % indent,
        '%s  <div class="video-card">' % indent,
        '%s    <!-- Poster only. main.js swaps in the YouTube iframe on click, so the' % indent,
        "%s         player's scripts load for people who actually press play. -->" % indent,
        '%s    <button class="video-thumb" id="videoBtn" data-video-id="%s"' % (indent, vid),
        '%s            data-i18n-aria="video.play" aria-label="Reproduzir vídeo">' % indent,
        '%s      <img src="https://i.ytimg.com/vi/%s/maxresdefault.jpg" alt="" loading="lazy">' % (indent, vid),
        '%s      <span class="play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>' % indent,
        '%s    </button>' % indent,
        '%s    <div class="video-caption">' % indent,
        '%s      <span class="vt">%s</span>' % (indent, html.escape(video["caption"])),
        '%s    </div>' % indent,
        '%s  </div>' % indent,
        '%s</section>' % indent,
    ])


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
    videos = load_videos()
    blocks = {}
    if split is not None:
        upcoming, past = split
        blocks = {
            "events:next": events.render(upcoming[:HOME_LIMIT]) if upcoming else EMPTY,
            "events:upcoming": events.render(upcoming) if upcoming else EMPTY,
            # Past ticket links point at closed sales, so they are dropped.
            "events:past": events.render(past, tickets=False, group_years=True) if past else EMPTY_PAST,
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
        if videos is not None:
            # A page with the marker but no CSV row gets an empty block rather
            # than a stale video left over from a previous build.
            vid = videos.get(key)
            body = render_video(vid) if vid else ""
            page, ok = inject(page, "video", body)
            if ok:
                filled.append("video" if vid else "video (none)")

        io.open(path, "w", encoding="utf-8").write(page)
        print("  %-22s %s" % (path, ", ".join(filled) or "no markers"))

    if split is not None:
        print("Done — %d upcoming event(s) (%d on home), %d archived."
              % (len(split[0]), min(HOME_LIMIT, len(split[0])), len(split[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
