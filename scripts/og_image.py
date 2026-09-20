#!/usr/bin/env python3
"""Render the home page into assets/img/og.jpg — the link-preview card.

    python3 scripts/og_image.py            # Portuguese, the site's own language
    python3 scripts/og_image.py --lang en

This is the picture WhatsApp, Telegram, Signal, Messenger, Slack and iMessage
show when someone pastes the address. It is a real screenshot of the home page
rather than a picture made to look like one, so the card can never drift from
the site: change the hero photo or the name's size and the card follows on the
next run.

Not part of scripts/build.py, and deliberately: it needs a browser, and the
GitHub Actions runner that builds the site has none. Run it by hand when the
hero changes, and commit the JPEG. Give it a minute or two — it starts the
browser on a throwaway profile rather than yours, which is slow but means it
works while you have Chrome open.

1200x630 is the size every one of those apps reads as "big card"; under 300 KB
is what WhatsApp will actually fetch, so the JPEG quality is tuned down until
it fits rather than left at whatever the encoder felt like.
"""

import argparse
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

WIDTH, HEIGHT = 1200, 630
SCALE = 2               # render at 2x and downsample: kinder to the type
MAX_BYTES = 300 * 1024  # WhatsApp gives up above roughly this
QUALITIES = (86, 80, 72, 64, 55)
OUT = "assets/img/og.jpg"

# The site's own language. The card carries the same words as the <title> and
# og:description beside it, which are Portuguese, so the render is too.
DEFAULT_LANG = "pt"
ACCEPT_LANG = {"pt": "pt-PT,pt", "en": "en-GB,en", "de": "de-AT,de"}

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


def serve(root):
    """A throwaway server on a free port.

    Over file:// the language toggle can't read localStorage and some browsers
    refuse the generated content.js, so the card would render in whatever the
    fallback happens to be. http:// makes the page behave as it does live."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # one line per asset is noise, not news

    handler = functools.partial(Quiet, directory=root)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def shoot(chrome, url, lang, png, profile):
    """One screenshot of the first 1200x630 of the page.

    --accept-lang rather than the machine's own locale: on a first visit the
    site follows the browser's language preferences, so without this the card
    would come out in whatever language the person running the script reads."""
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        "--user-data-dir=" + profile,
        "--accept-lang=" + ACCEPT_LANG.get(lang, lang),
        "--window-size=%d,%d" % (WIDTH, HEIGHT),
        "--force-device-scale-factor=%d" % SCALE,
        # Long enough for the webfonts to arrive — the name is Cormorant, and
        # a card rendered in the Georgia fallback is the wrong picture.
        "--virtual-time-budget=10000",
        "--screenshot=" + png, url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(png):
        sys.exit("chrome wrote no screenshot:\n" + (proc.stderr or "").strip())


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
