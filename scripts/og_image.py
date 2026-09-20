#!/usr/bin/env python3
"""Render the home page into assets/img/og.jpg — the link-preview card.

    python3 scripts/og_image.py            # the site's own language
    python3 scripts/og_image.py --lang pt  # or pt / de

This is the picture WhatsApp, Telegram, Signal, Messenger, Slack and iMessage
show when someone pastes the address. It is a real screenshot of the home page
rather than a picture made to look like one, so the card can never drift from
the site: change the hero photo or the name's size and the card follows on the
next run.

Not part of scripts/build.py, and deliberately: it needs a browser, and the
GitHub Actions runner that builds the site has none. Run it by hand when the
hero changes, and commit the JPEG. It takes a few seconds; if Chrome is busy
it falls back to a private profile, which can take a minute or two the first
time it builds one.

The frame is the hero photo below the navbar, at its own 3:2 — 1200x800. That
is wide enough for every one of those apps to read as "big card" rather than a
thumbnail; under 300 KB is what WhatsApp will actually fetch, so the JPEG
quality is tuned down until it fits rather than left at whatever the encoder
felt like.
"""

import argparse
import functools
import http.server
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events  # noqa: E402  — for SITE_LANG

# The hero photo's own 3:2, at the width the chat apps want. The card is the
# picture below the navbar and nothing else, so it is the hero's shape rather
# than the 1.91:1 that a screenshot of the whole first screenful had.
WIDTH, HEIGHT = 1200, 800
SCALE = 2               # render at 2x and downsample: kinder to the type
MAX_BYTES = 300 * 1024  # WhatsApp gives up above roughly this
QUALITIES = (86, 80, 72, 64, 55)
TIMEOUT = 120           # seconds to give the browser before calling it stuck
OUT = "assets/img/og.jpg"

# The card carries the same words as the <title> and og:description beside it,
# so it renders in the site's own language. Read from events rather than
# restated here, so changing the site's language changes the card with it.
DEFAULT_LANG = events.SITE_LANG
ACCEPT_LANG = {"pt": "pt-PT,pt", "en": "en-GB,en", "de": "de-AT,de"}

# Injected into the page for the capture and never written to disk: the bar is
# chrome, not the picture, and the hero is pinned to its own 3:2 so the whole
# photo lands in the frame instead of the first 630px of it. hero-inner follows
# the hero rather than 88vh, which keeps the name at the foot of the photo.
CARD_CSS = """
  .topbar{ display:none !important; }
  .hero{ aspect-ratio:3/2 !important; min-height:0 !important; }
  .hero-inner{ height:100% !important; }
"""

CHROMES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def find_chrome():
    """Chrome, wherever it lives; CHROME wins if it is set."""
    explicit = os.environ.get("CHROME")
    if explicit:
        return explicit
    for name in ("google-chrome", "chromium", "chromium-browser", "brave-browser"):
        found = shutil.which(name)
        if found:
            return found
    for path in CHROMES:
        if os.path.exists(path):
            return path
    sys.exit("no Chrome/Chromium found — install one, or set CHROME=/path/to/it")


def card_page(root):
    """index.html with the capture's own CSS appended — in memory only.

    The alternative is a card-shaped stylesheet living in the site, shipped to
    every visitor to serve one screenshot. This keeps the page exactly as it is
    published and still photographs the part of it the card wants."""
    page = io.open(os.path.join(root, "index.html"), encoding="utf-8").read()
    style = "<style>%s</style>\n</head>" % CARD_CSS
    if "</head>" not in page:
        return page
    return page.replace("</head>", style, 1)


def serve(root):
    """A throwaway server on a free port.

    Over file:// the language toggle can't read localStorage and some browsers
    refuse the generated content.js, so the card would render in whatever the
    fallback happens to be. http:// makes the page behave as it does live."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # one line per asset is noise, not news

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                body = card_page(root).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    handler = functools.partial(Quiet, directory=root)
    # Threaded, not the one-at-a-time server: Chrome opens several connections
    # to an origin before it has requests to put on them, and a single-threaded
    # server blocks on the first idle one — every asset then queues behind a
    # socket that never speaks, the page never finishes loading, and the
    # screenshot never arrives. It looks exactly like a slow render.
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def shoot(chrome, url, lang, png, profile):
    """One screenshot of the hero, at exactly the card's size.

    --accept-lang rather than the machine's own locale: on a first visit the
    site follows the browser's language preferences, so without this the card
    would come out in whatever language the person running the script reads."""
    base = [
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        # None of this has anything to do with the page, and a profile that is
        # setting itself up will sit in the middle of it for a long time.
        "--disable-background-networking", "--disable-component-update",
        "--disable-client-side-phishing-detection", "--disable-sync",
        "--disable-default-apps", "--disable-extensions",
        "--metrics-recording-only", "--no-pings",
        "--accept-lang=" + ACCEPT_LANG.get(lang, lang),
        "--window-size=%d,%d" % (WIDTH, HEIGHT),
        "--force-device-scale-factor=%d" % SCALE,
        # Long enough for the webfonts to arrive — the name is Cormorant, and
        # a card rendered in the Georgia fallback is the wrong picture.
        "--virtual-time-budget=10000",
        "--screenshot=" + png, url,
    ]
    # Chrome's own profile first, because a brand-new --user-data-dir can spend
    # minutes on first-run setup before it renders anything — often longer than
    # anyone will wait. The private profile is the fallback, for when Chrome is
    # already running and won't share: slow, but it does finish. Extensions and
    # background networking are off either way, so the real profile's contents
    # can't reach the picture.
    attempts = [("Chrome's own profile", base),
                ("a private profile", base + ["--user-data-dir=" + profile])]
    problems = []
    for label, cmd in attempts:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            problems.append("%s: no screenshot within %ds" % (label, TIMEOUT))
            continue
        if os.path.exists(png):
            return
        problems.append("%s: %s" % (label, (proc.stderr or "").strip()[-300:] or
                                    "exited %d without writing one" % proc.returncode))
    sys.exit("chrome wrote no screenshot.\n  " + "\n  ".join(problems))


def to_jpeg(png, out):
    """Down to 1200 wide and into JPEG, small enough for WhatsApp to fetch."""
    for quality in QUALITIES:
        subprocess.run(
            ["sips", "-Z", str(WIDTH), "--setProperty", "format", "jpeg",
             "--setProperty", "formatOptions", str(quality), png, "--out", out],
            check=True, capture_output=True)
        size = os.path.getsize(out)
        if size <= MAX_BYTES:
            return size, quality
    return os.path.getsize(out), QUALITIES[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", default=DEFAULT_LANG, choices=sorted(ACCEPT_LANG),
                    help="language to render the card in (default: %s)" % DEFAULT_LANG)
    ap.add_argument("--out", default=OUT, help="where to write it (default: %s)" % OUT)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(os.path.join(root, "index.html")):
        sys.exit("run me from the site folder — no index.html beside scripts/")

    chrome = find_chrome()
    httpd, port = serve(root)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, "card.png")
            shoot(chrome, "http://127.0.0.1:%d/index.html" % port,
                  args.lang, png, os.path.join(tmp, "profile"))
            out = os.path.join(root, args.out)
            size, quality = to_jpeg(png, out)
    finally:
        httpd.shutdown()

    print("  %-22s %dx%d, %.0f KB, quality %d, %s"
          % (args.out, WIDTH, HEIGHT, size / 1024.0, quality, args.lang))
    if size > MAX_BYTES:
        print("  warning: over %d KB — WhatsApp may skip the image"
              % (MAX_BYTES // 1024))


if __name__ == "__main__":
    main()
