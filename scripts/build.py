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
    text:<i18n key>    text compiled from content/<page>/<block>_<lang>.md — the Portuguese
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

# Where the site is served from, with the trailing slash. Link previews need
# absolute URLs — a chat app fetches the page from its own servers, so a
# relative og:image resolves against nothing and the preview falls back to the
# favicon. Override with SITE_URL when the custom domain lands.
SITE_URL = os.environ.get(
    "SITE_URL", "https://andreferreiramusic.github.io/site/").rstrip("/") + "/"

HOME_LIMIT = 4  # upcoming events shown on the home page
VIDEOS_CSV = "data/videos.csv"  # override with the VIDEOS_CSV env var
CONTENT_DIR = "content"         # content/<page>/<block>_<lang>.md
CONTENT_JS = "assets/js/content.js"

# Every word of the site that changes with the language, and nothing else
# does: content/<page>/<block>_<lang>.md -> the i18n key the markup asks for.
#
# PROSE is wrapped in a <p> per paragraph and lands inside a .prose block.
# LABEL goes in exactly as written, because it lands inside an <a>, an <h2> or
# an aria-label, where a <p> would break the markup. That is the only
# difference between the two, and it is why the kind is declared here rather
# than guessed from the file's length.
#
# site/ holds what isn't a page's own: the menu, and the wording the concert
# rows and the video poster are generated with.
PROSE, LABEL = "prose", "label"
TEXTS = [
    # folder     file               i18n key            kind
    ("home",    "main",             "home.about",       PROSE),
    ("home",    "hero-eyebrow",     "hero.eyebrow",     LABEL),
    ("home",    "hero-cta",         "hero.cta",         LABEL),
    ("home",    "dates-heading",    "home.dates.h",     LABEL),
    ("home",    "dates-all",        "home.dates.all",   LABEL),
    ("home",    "link-about",       "home.about.d",     LABEL),
    ("home",    "link-guitar",      "home.guitar.d",    LABEL),
    ("home",    "link-lute",        "home.lute.d",      LABEL),
    ("about",   "main",             "bio.body",         PROSE),  # teaching included
    ("guitar",  "main",             "guitar.body",      PROSE),
    ("lute",    "main",             "lute.body",        PROSE),
    ("dates",   "upcoming-heading", "dates.upcoming",   LABEL),
    ("dates",   "past-heading",     "dates.past",       LABEL),
    ("dates",   "past-none",        "dates.past.none",  LABEL),
    ("contact", "main",             "contact.body",     PROSE),
    ("contact", "email-label",      "contact.email",    LABEL),
    ("contact", "press-heading",    "press.h",          LABEL),
    ("contact", "press-body",       "press.d",          LABEL),
    ("contact", "press-cta",        "press.cta",        LABEL),
    ("contact", "photo-credit",     "press.credit",     LABEL),
    ("site",    "nav-home",         "nav.home",         LABEL),
    ("site",    "nav-about",        "nav.about",        LABEL),
    ("site",    "nav-guitar",       "nav.guitar",       LABEL),
    ("site",    "nav-lute",         "nav.lute",         LABEL),
    ("site",    "nav-dates",        "nav.dates",        LABEL),
    ("site",    "nav-contact",      "nav.contact",      LABEL),
    ("site",    "tickets",          "concerts.tickets", LABEL),
    ("site",    "concerts-none",    "concerts.none",    LABEL),
    ("site",    "video-play",       "video.play",       LABEL),
]
KINDS = {key: kind for _folder, _stem, key, kind in TEXTS}

# page key, file, the i18n key its menu entry uses. The wording itself lives
# in content/site/nav-<page>_<lang>.md like everything else.
NAV = [
    ("home",    "index.html",           "nav.home"),
    ("about",   "pages/about.html",     "nav.about"),
    ("guitar",  "pages/guitar.html",    "nav.guitar"),
    ("lute",    "pages/lute.html",      "nav.lute"),
    ("dates",   "pages/dates.html",     "nav.dates"),
    ("contact", "pages/contact.html",   "nav.contact"),
]


def note(pt, key, indent="      "):
    """The line shown where a concert list is empty. Generated rather than
    kept as a constant so its wording lives in content/ with everything
    else."""
    return '%s<p class="note" data-i18n="%s">%s</p>' % (indent, key, pt.get(key, ""))


# The page's own <title> and meta description, which sit outside every marker
# and are written by hand. Reused for the link preview rather than restated in
# a second set of tags, so a page's wording still lives in exactly one place.
PAGE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
PAGE_DESC = re.compile(r'<meta\s+name="description"\s+content="(.*?)"\s*/?>', re.S)
# Optional, and only for the link preview: a page that wants the card to say
# something other than its meta description says it here. See index.html.
PAGE_SHARE = re.compile(r'<meta\s+name="share-description"\s+content="(.*?)"\s*/?>', re.S)


def meta_text(pattern, page, fallback=""):
    """The text of one hand-written head tag, collapsed to a single line.

    It comes out of the file already HTML-escaped and goes straight back into
    an attribute, so it is unescaped and re-escaped rather than passed through:
    an apostrophe written raw in a <title> is fine there and fine in a
    content="…" too, but only html.escape decides that consistently."""
    m = pattern.search(page)
    if not m:
        return fallback
    return html.escape(html.unescape(" ".join(m.group(1).split())), quote=True)


def fill_head(head, base, page, page_url):
    """The shared head, with this page's own wording in its preview tags."""
    title = meta_text(PAGE_TITLE, page, "André Ferreira")
    desc = meta_text(PAGE_SHARE, page) or meta_text(PAGE_DESC, page, title)
    return (head.replace("{{base}}", base)
                .replace("{{site}}", SITE_URL)
                .replace("{{page_url}}", page_url)
                .replace("{{og_title}}", title)
                .replace("{{og_desc}}", desc))


def parts():
    """Split templates/parts.html on its <!-- part:name --> headings."""
    text = io.open("templates/parts.html", encoding="utf-8").read()
    chunks = re.split(r"<!-- part:([\w-]+) -->\n", text)
    # chunks[0] is the file's leading comment; then name, body, name, body…
    return {chunks[i]: chunks[i + 1].strip("\n") for i in range(1, len(chunks) - 1, 2)}


def nav_links(current_key, base, pt, indent="      "):
    """`pt` is the Portuguese text map: the menu ships readable before any
    JavaScript runs, and for crawlers, exactly as the page prose does."""
    out = []
    for key, path, i18n_key in NAV:
        href = base + path
        current = ' aria-current="page"' if key == current_key else ""
        out.append('%s<a href="%s"%s data-i18n="%s">%s</a>'
                   % (indent, href, current, i18n_key, pt.get(i18n_key, "")))
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


# An element carrying data-i18n, with its own closing tag. The tag name is
# captured so the match ends at that tag and not at the first </…> inside it:
# a label is allowed to contain markup, because **bold** and [links](url) work
# here the same as in the prose.
#
# The content may not cross a line, which is what keeps the prose blocks out —
# they hold their marker comments on lines of their own and have their own
# mechanism. Labels are one line by nature.
LABEL_TEXT = re.compile(r'(<(\w+)\b[^<>]*\sdata-i18n="([\w.]+)"[^<>]*>)([^\n]*?)(</\2>)')


def fill_labels(text, pt, where=""):
    """Rewrite the Portuguese of every label in the page.

    Prose has start/end markers; a label is a word or two inside an anchor or
    a heading, where a marker comment would mean a line break in a spot where
    whitespace shows. Keying off the attribute instead leaves the markup as
    someone would write it by hand, and still means content/site/nav-dates_pt.md
    is the only place the menu's wording lives."""
    def swap(m):
        tag, key = m.group(2).lower(), m.group(3)
        if KINDS.get(key) != LABEL or key not in pt:
            return m.group(0)
        body = pt[key]
        if tag == "a" and "<a " in body:
            # An <a> inside an <a> is not markup any browser will keep; the
            # label is already inside a link, so it needs no link of its own.
            events.warn("%s: %s sits inside a link, so the [markdown](link) in "
                        "it would nest one anchor in another — use plain text"
                        % (where or "page", key))
            return m.group(0)
        return m.group(1) + body + m.group(5)
    return LABEL_TEXT.sub(swap, text)


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


def render_video(video, play_label, indent="  "):
    """Poster only; main.js swaps in the iframe on click. `play_label` is the
    Portuguese from content/site/video-play_pt.md — it is an attribute, so the
    label pass can't reach it and it is written in here instead."""
    vid = html.escape(video["id"], quote=True)
    return "\n".join([
        '%s<section class="band">' % indent,
        '%s  <div class="video-card">' % indent,
        '%s    <!-- Poster only. main.js swaps in the YouTube iframe on click, so the' % indent,
        "%s         player's scripts load for people who actually press play. -->" % indent,
        '%s    <button class="video-thumb" id="videoBtn" data-video-id="%s"' % (indent, vid),
        '%s            data-i18n-aria="video.play" aria-label="%s">'
        % (indent, html.escape(play_label, quote=True)),
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


MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$")


def md_to_html(text, where=""):
    """Just enough Markdown for prose: blank-line paragraphs, ## headings,
    **bold**, *italic* and [links](url). A real parser would mean a pip
    dependency in CI for a handful of short files, which is not a trade worth
    making.

    A heading is its own line, and the hashes give the level as they do
    everywhere else — ## is an <h2>. It need not be surrounded by blank
    lines: the line below one starts the paragraph under it, which is how
    people write headings without thinking about it."""
    out, para = [], []

    def flush():
        if para:
            out.append("<p>%s</p>" % md_inline(" ".join(para)))
            del para[:]

    for block in re.split(r"\n\s*\n", text.strip()):
        for line in block.strip().split("\n"):
            line = line.strip()
            m = MD_HEADING.match(line)
            if not m:
                if line:
                    para.append(line)
                continue
            flush()
            level = len(m.group(1))
            if level == 1:
                # Every page already opens with its own <h1>; a second one
                # muddles the outline for search engines and screen readers.
                events.warn("%s: a # heading makes a second <h1> on the page — "
                            "## is the one to use inside a text" % (where or "content"))
            out.append("<h%d>%s</h%d>" % (level, md_inline(m.group(2)), level))
        flush()
    return "".join(out)


def md_label(text):
    """A label goes in as one line of inline HTML: no <p>, because it lands
    inside an <a>, an <h2> or an aria-label. Line breaks in the file are just
    wrapping and collapse to spaces."""
    return md_inline(" ".join(text.split()))


def load_content():
    """{lang: {i18n key: html}} from content/<page>/<block>_<lang>.md, or None
    if the directory is absent.

    Every translatable word on the site is one of these files — the prose and
    the one-word labels alike — so a text is changed in one place and nothing
    is edited in JavaScript. Which languages exist is read off the filenames,
    so a fourth means dropping <block>_fr.md beside the others.
    """
    root = os.environ.get("CONTENT_DIR", "").strip() or CONTENT_DIR
    if not os.path.isdir(root):
        events.warn("no %s directory; page texts left as they are" % root)
        return None
    found, langs = {}, set()
    for folder, stem, key, _kind in TEXTS:
        d = os.path.join(root, folder)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not name.startswith(stem + "_") or not name.endswith(".md"):
                continue
            lang = name[len(stem) + 1:-3].lower()
            found[(key, lang)] = os.path.join(d, name)
            langs.add(lang)
    out = {lang: {} for lang in sorted(langs)}
    for folder, stem, key, kind in TEXTS:
        for lang in sorted(langs):
            path = found.get((key, lang))
            if not path:
                events.warn("missing %s/%s/%s_%s.md — %s falls back to another "
                            "language" % (root, folder, stem, lang, key))
                continue
            text = io.open(path, encoding="utf-8").read()
            out[lang][key] = (md_to_html(text, path) if kind == PROSE
                              else md_label(text))
    return out


def write_content_js(content):
    """One small file the pages load before main.js, which merges it in."""
    body = json.dumps(content, ensure_ascii=False, indent=1, sort_keys=True)
    io.open(CONTENT_JS, "w", encoding="utf-8").write(
        "// GENERATED by scripts/build.py from %s/<page>/<block>_<lang>.md — do not edit.\n"
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

    content = load_content()
    # Portuguese is what gets written into the HTML: the site reads correctly
    # before any JavaScript runs, and for crawlers. Everything below that
    # needs a word of it — the menu, the empty-list notes, the ticket links —
    # takes it from here rather than carrying a copy.
    pt = (content or {}).get("pt", {})
    if content:
        write_content_js(content)
        print("  %-22s %d languages x %d texts" % (CONTENT_JS, len(content), len(TEXTS)))
    split = load_events()
    videos = load_videos()
    kit = load_press_kit()
    blocks = {}
    if kit is not None:
        zip_path, size, pages, photos = kit
        blocks["presskit"] = press_kit.render_link(zip_path, size, photos)
        print("  %-22s %d page(s), %d photo(s), %s"
              % (zip_path, pages, photos, press_kit.human(size)))
    if split is not None:
        upcoming, past = split
        tix = pt.get("concerts.tickets", "")
        none_now = note(pt, "concerts.none")
        blocks.update({
            "events:next": events.render(upcoming[:HOME_LIMIT], tickets_label=tix) if upcoming else none_now,
            "events:upcoming": events.render(upcoming, tickets_label=tix) if upcoming else none_now,
            # Past ticket links point at closed sales, so they are dropped.
            "events:past": (events.render(past, tickets=False, group_years=True)
                            if past else note(pt, "dates.past.none")),
        })

    for key, path, _i18n_key in NAV:
        if not os.path.exists(path):
            events.warn("%s is listed in NAV but does not exist" % path)
            continue
        base = "" if key == "home" else "../"
        page = io.open(path, encoding="utf-8").read()
        filled = []

        # index.html is the site root, so its canonical URL is the bare
        # domain rather than …/index.html — two URLs for one page otherwise.
        page_url = SITE_URL + ("" if key == "home" else path)
        page, ok = inject(page, "head", fill_head(part["head"], base, page, page_url))
        if ok:
            filled.append("head")
        nav = "\n".join([
            part["header-open"].replace("{{base}}", base),
            nav_links(key, base, pt),
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
        for text_key, body_html in sorted(pt.items()):
            if KINDS.get(text_key) != PROSE:
                continue
            page, ok = inject(page, "text:" + text_key, "      " + body_html)
            if ok:
                filled.append(text_key)
        if videos is not None:
            # A page with the marker but no CSV row gets an empty block rather
            # than a stale video left over from a previous build.
            vid = videos.get(key)
            body = render_video(vid, pt.get("video.play", "")) if vid else ""
            page, ok = inject(page, "video", body)
            if ok:
                filled.append("video" if vid else "video (none)")

        if pt:
            page = fill_labels(page, pt, path)
        io.open(path, "w", encoding="utf-8").write(page)
        print("  %-22s %s" % (path, ", ".join(filled) or "no markers"))

    if split is not None:
        print("Done — %d upcoming event(s) (%d on home), %d archived."
              % (len(split[0]), min(HOME_LIMIT, len(split[0])), len(split[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
