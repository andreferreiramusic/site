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
    presskit           the download link for the kit that scripts/press_kit.py
                       builds from press_kit/bios.md and the photos beside it
    text:<i18n key>    prose compiled from content/<lang>/*.md — the Portuguese
                       copy is written into the page, and all three languages
                       are compiled into assets/js/content.js

Paths are relative rather than root-relative because the site is served from
a project subpath (…github.io/site/), where /assets/… would 404. In the shared
parts {{base}} resolves per page; inside a page's own content just write the
real relative path.
"""

import csv
import html
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events  # noqa: E402
import press_kit  # noqa: E402

HOME_LIMIT = 4  # upcoming events shown on the home page
VIDEOS_CSV = "data/videos.csv"  # override with the VIDEOS_CSV env var
CONTENT_DIR = "content"         # content/<lang>/<name>.md
CONTENT_JS = "assets/js/content.js"

# Markdown file stem -> the i18n key the site uses for it.
TEXTS = {
    "home-intro": "home.about",
    "about": "bio.body",
    "teaching": "teaching.body",
    "guitar": "guitar.body",
    "lute": "lute.body",
    "contact": "contact.body",
}

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


MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")
MD_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def md_inline(text):
    # Escape first so anything angle-bracketed in the source stays literal;
    # the tags below are added afterwards and so survive.
    text = html.escape(text, quote=False)

    def link(m):
        label, url = m.group(1), m.group(2)
        # An outbound link gets target/rel automatically, which is also what
        # the stylesheet keys off to colour it as leaving the site.
        out = ' target="_blank" rel="noopener"' if url.startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (html.escape(url, quote=True), out, label)

    text = MD_LINK.sub(link, text)
    text = MD_BOLD.sub(r"<strong>\1</strong>", text)
    text = MD_ITALIC.sub(r"<em>\1</em>", text)
    return text


def md_to_html(text):
    """Just enough Markdown for prose: blank-line paragraphs, **bold**,
    *italic* and [links](url). A real parser would mean a pip dependency in
    CI for six short files, which is not a trade worth making."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "".join("<p>%s</p>" % md_inline(" ".join(p.split("\n"))) for p in paras)


def load_content():
    """{lang: {i18n key: html}} from content/<lang>/*.md, or None if absent."""
    root = os.environ.get("CONTENT_DIR", "").strip() or CONTENT_DIR
    if not os.path.isdir(root):
        events.warn("no %s directory; page texts left as they are" % root)
        return None
    out = {}
    for lang in sorted(os.listdir(root)):
        d = os.path.join(root, lang)
        if not os.path.isdir(d):
            continue
        out[lang] = {}
        for stem, key in TEXTS.items():
            f = os.path.join(d, stem + ".md")
            if not os.path.exists(f):
                events.warn("missing %s — %s will fall back to another language" % (f, key))
                continue
            out[lang][key] = md_to_html(io.open(f, encoding="utf-8").read())
    return out


def write_content_js(content):
    """One small file the pages load before main.js, which merges it in."""
    body = json.dumps(content, ensure_ascii=False, indent=1, sort_keys=True)
    io.open(CONTENT_JS, "w", encoding="utf-8").write(
        "// GENERATED by scripts/build.py from %s/<lang>/*.md — do not edit.\n"
        "// Edit the Markdown and run the build; main.js merges this into its\n"
        "// own dictionary of UI strings.\n"
        "window.__content = %s;\n" % (CONTENT_DIR, body))


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


def load_press_kit():
    """The PDF and zip, rebuilt from press_kit/. Wrapped like the CSV readers:
    a press kit that won't build is a warning on the Actions run, not a failed
    deploy — the rest of the site is unaffected and the marker simply stays
    empty, so the contact page offers no link to a file that isn't there."""
    try:
        return press_kit.build()
    except Exception as exc:
        events.warn("could not build the press kit (%s); "
                    "the download link is left out" % exc)
        return None


def main():
    part = parts()
    missing = [k for k in ("head", "header-open", "header-close", "footer") if k not in part]
    if missing:
        events.warn("templates/parts.html is missing part(s): %s" % ", ".join(missing))
        return 1

    split = load_events()
    videos = load_videos()
    kit = load_press_kit()
    content = load_content()
    if content:
        write_content_js(content)
        print("  %-22s %d languages x %d texts" % (CONTENT_JS, len(content), len(TEXTS)))
    blocks = {}
    if kit is not None:
        zip_path, size, pages, photos = kit
        blocks["presskit"] = press_kit.render_link(zip_path, size, photos)
        print("  %-22s %d page(s), %d photo(s), %s"
              % (zip_path, pages, photos, press_kit.human(size)))
    if split is not None:
        upcoming, past = split
        blocks.update({
            "events:next": events.render(upcoming[:HOME_LIMIT]) if upcoming else EMPTY,
            "events:upcoming": events.render(upcoming) if upcoming else EMPTY,
            # Past ticket links point at closed sales, so they are dropped.
            "events:past": events.render(past, tickets=False, group_years=True) if past else EMPTY_PAST,
        })

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
            page, ok = inject(page, name, payload.replace("{{base}}", base))
            if ok:
                filled.append(name)
        if content and "pt" in content:
            # The Portuguese copy is baked into the HTML so the page reads
            # correctly before any JavaScript runs, and for crawlers.
            for text_key, body_html in sorted(content["pt"].items()):
                page, ok = inject(page, "text:" + text_key, "      " + body_html)
                if ok:
                    filled.append(text_key)
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
