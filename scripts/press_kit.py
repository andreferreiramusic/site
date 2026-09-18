#!/usr/bin/env python3
"""Builds the press kit: a PDF of the three bios plus a zip with the photos.

    python3 scripts/press_kit.py        (scripts/build.py runs it too)

Sources, both hand-edited:

    press_kit/bios.md     key: value front matter, then one `# pt|en|de`
                          section per language: an optional `> tagline` line
                          and the bio's paragraphs
    press_kit/*.jpg       the photos, dropped straight into the folder; a
                          press_kit/photos/ subfolder is read as well

Outputs, both generated (git-ignored) and rebuilt on every deploy:

    press_kit/<slug>-press-kit.pdf
    press_kit/<slug>-press-kit.zip    the PDF, bios.md and the photos

The PDF is written byte by byte rather than with a library because the deploy
runs bare `python3` with nothing installed — adding a pip step to CI for one
three-page document is not a trade worth making. That is also why the type is
Helvetica: one of the 14 faces every PDF reader carries, so nothing has to be
embedded. It does mean line breaking has to measure the glyphs itself, which
is what the width tables below are for.

Text is written in WinAnsiEncoding, which is CP1252 — every accent in
Portuguese, German and English fits. Anything outside it (a Polish ł in a
venue name, say) is stripped to its base letter rather than dropped.
"""

import html
import io
import os
import re
import sys
import unicodedata
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events  # noqa: E402  — for warn()

PRESS_DIR = "press_kit"          # override with the PRESS_DIR env var
BIOS_MD = "bios.md"
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")
JPEG_EXT = (".jpg", ".jpeg")

# Native name of the biography, per language section in bios.md. A section
# whose code is not listed still builds — it just gets its code as a heading.
LABELS = {"pt": "Biografia", "en": "Biography", "de": "Biographie"}
# The photo list is one block for every reader, so its heading carries all
# three languages rather than picking one.
PHOTOS_HEADING = "Fotografias · Photographs · Fotos"
PHOTOS_NOTE = {
    "pt": "Incluídas neste dossier, em alta resolução, para uso em programas e imprensa.",
    "en": "Included in this kit at full resolution, free to use for programmes and press.",
    "de": "In dieser Mappe in voller Auflösung enthalten, zur Verwendung in Programmheften und Presse.",
}


# ---------------------------------------------------------------- metrics --
#
# Adobe's published Helvetica widths for codes 32-126, in 1/1000 em.
# Helvetica-Oblique is metrically identical to Helvetica, so two tables cover
# all three faces used here.
HELV = (
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
)
HELV_BOLD = (
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584,
)
# Punctuation above code 127 that has no ASCII letter to borrow from. An
# accented letter is the width of its base in both faces, which is how the
# rest of the upper range is resolved (see char_width).
EXTRA = {
    "‘": 222, "’": 222, "“": 333, "”": 333, "‚": 222,
    "„": 333, "–": 556, "—": 1000, "•": 350, "…": 1000,
    "·": 278, "«": 556, "»": 556, "°": 400, "§": 556,
    "©": 737, "®": 737, "™": 1000, "€": 556, "ß": 556,
    "ª": 370, "º": 365, "¡": 333, "¿": 611, "†": 556,
}
EXTRA_BOLD = dict(EXTRA, **{
    "‘": 278, "’": 278, "“": 500, "”": 500, "‚": 278,
    "„": 500, "ß": 611, "¡": 333, "¿": 611,
})
FONT = {"": b"F1", "b": b"F2", "i": b"F3"}


def char_width(ch, style):
    bold = style == "b"
    table = HELV_BOLD if bold else HELV
    code = ord(ch)
    if 32 <= code <= 126:
        return table[code - 32]
    extra = EXTRA_BOLD if bold else EXTRA
    if ch in extra:
        return extra[ch]
    # é is exactly as wide as e in both faces, so decompose and measure that.
    base = unicodedata.normalize("NFD", ch)[:1]
    if base and 32 <= ord(base) <= 126:
        return table[ord(base) - 32]
    return table[ord("n") - 32]


def text_width(text, size, style="", tracking=0.0):
    w = sum(char_width(c, style) for c in text) / 1000.0 * size
    return w + tracking * len(text)


# ------------------------------------------------------------ pdf plumbing --

def winansi(text):
    """Encode to WinAnsi (CP1252), stripping accents from anything outside it
    rather than losing the letter altogether."""
    out = bytearray()
    for ch in text:
        try:
            out += ch.encode("cp1252")
            continue
        except UnicodeEncodeError:
            pass
        base = "".join(c for c in unicodedata.normalize("NFD", ch)
                       if not unicodedata.combining(c))
        try:
            out += base.encode("cp1252")
        except UnicodeEncodeError:
            out += b"?"
    return bytes(out)


def pdf_string(text):
    out = bytearray(b"(")
    for b in winansi(text):
        if b in (0x28, 0x29, 0x5C):       # ( ) \
            out += b"\\" + bytes([b])
        elif 32 <= b <= 126:
            out.append(b)
        else:
            out += (b"\\%03o" % b)
    out += b")"
    return bytes(out)


def pdf_text_string(text):
    """For the document information dictionary, which a reader decodes as
    PDFDocEncoding — where WinAnsi's em dash is a different glyph entirely.
    UTF-16BE with a byte-order mark is read correctly everywhere."""
    return b"<FEFF" + text.encode("utf-16-be").hex().upper().encode("ascii") + b">"


def num(value):
    """Two decimals is finer than any printer resolves, and trailing .00 is
    just noise in the content stream."""
    s = b"%.2f" % value
    return s[:-3] if s.endswith(b".00") else s


def rgb(color, stroke=False):
    op = b"RG" if stroke else b"rg"
    return b"%s %s %s %s" % (num(color[0]), num(color[1]), num(color[2]), op)


class Pdf(object):
    """Numbered objects and a cross-reference table. No dates anywhere, so
    two runs over the same sources produce byte-identical files."""

    def __init__(self):
        self.objs = [None]

    def reserve(self):
        self.objs.append(None)
        return len(self.objs) - 1

    def add(self, body, num_=None):
        if num_ is None:
            num_ = self.reserve()
        self.objs[num_] = body
        return num_

    def stream(self, extra, data, compress=True):
        if compress:
            data = zlib.compress(data, 9)
            extra += b" /Filter /FlateDecode"
        return (b"<< " + extra + b" /Length %d >>\nstream\n" % len(data)
                + data + b"\nendstream")

    def out(self, root, info=None):
        head = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        body, offsets, pos = [], [0] * len(self.objs), len(head)
        for i in range(1, len(self.objs)):
            offsets[i] = pos
            chunk = b"%d 0 obj\n" % i + self.objs[i] + b"\nendobj\n"
            body.append(chunk)
            pos += len(chunk)
        n = len(self.objs)
        xref = [b"xref\n0 %d\n" % n, b"0000000000 65535 f \n"]
        xref += [b"%010d 00000 n \n" % offsets[i] for i in range(1, n)]
        trailer = b"trailer\n<< /Size %d /Root %d 0 R" % (n, root)
        if info:
            trailer += b" /Info %d 0 R" % info
        trailer += b" >>\nstartxref\n%d\n%%%%EOF\n" % pos
        return b"".join([head] + body + xref + [trailer])


# ------------------------------------------------------------------ images --

def jpeg_info(data):
    """(width, height, components, progressive) from the frame header, or None
    if this isn't a JPEG we can hand straight to the reader."""
    if not data.startswith(b"\xff\xd8"):
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = int.from_bytes(data[i + 2:i + 4], "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h, data[i + 9], marker in (0xC2, 0xC6, 0xCA, 0xCE)
        i += 2 + seg
    return None


def jpeg_orientation(data):
    """EXIF orientation, or 1. A portrait shot straight off a camera is often
    stored landscape with a rotation flag, and a sideways face on a press kit
    is not a detail worth getting wrong."""
    i = 2
    while i + 4 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xDA:                      # start of scan; EXIF is behind us
            break
        seg = int.from_bytes(data[i + 2:i + 4], "big")
        if marker == 0xE1 and data[i + 4:i + 10] == b"Exif\x00\x00":
            tiff = data[i + 10:i + 2 + seg]
            try:
                return exif_orientation(tiff)
            except (IndexError, ValueError):
                return 1
        i += 2 + seg
    return 1


def exif_orientation(tiff):
    order = "big" if tiff[:2] == b"MM" else "little"

    def u16(o):
        return int.from_bytes(tiff[o:o + 2], order)

    def u32(o):
        return int.from_bytes(tiff[o:o + 4], order)

    ifd = u32(4)
    for k in range(u16(ifd)):
        entry = ifd + 2 + k * 12
        if u16(entry) == 0x0112:
            value = u16(entry + 8)
            return value if 1 <= value <= 8 else 1
    return 1


def cover_matrix(box, iw, ih, orientation):
    """Place an image to fill `box` and crop the overflow — object-fit: cover,
    written as a PDF matrix. Rotated originals are turned back upright here,
    which is why width and height swap for the quarter turns."""
    bx, by, bw, bh = box
    if orientation in (5, 6, 7, 8):
        iw, ih = ih, iw
    scale = max(bw / float(iw), bh / float(ih))
    dw, dh = iw * scale, ih * scale
    ox, oy = bx + (bw - dw) / 2.0, by + (bh - dh) / 2.0
    if orientation in (3, 4):                   # upside down
        return (-dw, 0, 0, -dh, ox + dw, oy + dh)
    if orientation in (5, 6):                   # a quarter turn clockwise
        return (0, -dh, dw, 0, ox, oy + dh)
    if orientation in (7, 8):                   # a quarter turn anticlockwise
        return (0, dh, -dw, 0, ox + dw, oy)
    return (dw, 0, 0, dh, ox, oy)


# ------------------------------------------------------------- the markdown --

MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
MD_RUN = re.compile(r"\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)")


def runs(text):
    """Split **bold** and *italic* into (text, style) runs. A [label](url) keeps
    its label — paper has nothing to click."""
    text = MD_LINK.sub(r"\1", text)
    out, pos = [], 0
    for m in MD_RUN.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], ""))
        out.append((m.group(1), "b") if m.group(1) else (m.group(2), "i"))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], ""))
    return out or [("", "")]


def parse_bios(text):
    """(meta, [(code, tagline, [paragraph, ...]), ...]) from press_kit/bios.md."""
    meta, body = {}, text
    fm = re.match(r"\s*---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
        body = text[fm.end():]

    langs, code, tagline, paras = [], None, "", []

    def close():
        if code:
            langs.append((code, tagline, [p for p in paras if p]))

    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            head, _, rest = block.partition("\n")
            close()
            code, tagline, paras = head[2:].strip().lower(), "", []
            block = rest.strip()
            if not block:
                continue
        if block.startswith(">"):
            first, _, rest = block.partition("\n")
            tagline = first.lstrip("> ").strip()
            block = rest.strip()
            if not block:
                continue
        paras.append(" ".join(block.split()))
    close()
    return meta, langs


# ---------------------------------------------------------------- the page --

PAGE_W, PAGE_H = 595.28, 841.89      # A4: this kit goes to European programmers
MARGIN = 62.0
COL_W = PAGE_W - 2 * MARGIN
BANNER_H = 188.0

# The site is cream on black; paper is the other way about. The accent is the
# same light wood, darkened until it still reads when printed on white.
INK = (0.10, 0.09, 0.08)
SUB = (0.44, 0.40, 0.35)
ACCENT = (0.51, 0.39, 0.21)
RULE = (0.80, 0.78, 0.72)


class Doc(object):
    """Text goes in from the top and pages break themselves."""

    def __init__(self):
        self.pdf = Pdf()
        self.pages = []
        self.images = []
        self.placed = {}      # path -> XObject name, so the cover photo is
        self.skipped = set()  # embedded once even though it also appears on
                              # the contact sheet
        self.ops = []
        self.y = 0.0
        self.new_page()

    def new_page(self):
        self.ops = []
        self.pages.append(self.ops)
        self.y = PAGE_H - MARGIN

    def room(self, height):
        """Start a new page unless `height` still fits — used to keep a heading
        with the first lines of what it heads."""
        if self.y - height < MARGIN:
            self.new_page()

    def draw(self, line, size, y, color, style_default="", tracking=0.0, x=MARGIN):
        if not line:
            return
        ops, cur = self.ops, None
        ops.append(b"BT " + rgb(color))
        if tracking:
            ops.append(b"%s Tc" % num(tracking))
        space = text_width(" ", size, style_default, tracking)
        for word, style in line:
            style = style or style_default
            if style != cur:
                ops.append(b"/%s %s Tf" % (FONT[style], num(size)))
                cur = style
            ops.append(b"1 0 0 1 %s %s Tm %s Tj" % (num(x), num(y), pdf_string(word)))
            x += text_width(word, size, style, tracking) + space
        if tracking:
            ops.append(b"0 Tc")
        ops.append(b"ET")

    def line(self, words, size, leading, color, style, tracking):
        if self.y - leading < MARGIN:
            self.new_page()
        self.y -= leading
        self.draw(words, size, self.y, color, style, tracking)

    def para(self, text, size=10.4, style="", color=INK, leading=None,
             before=0.0, after=0.0, tracking=0.0, width=COL_W):
        leading = leading or size * 1.5
        self.y -= before
        words = []
        for chunk, chunk_style in runs(text):
            words += [(w, chunk_style) for w in chunk.split()]
        line, used = [], 0.0
        space = text_width(" ", size, style, tracking)
        for word, word_style in words:
            w = text_width(word, size, word_style or style, tracking)
            if line and used + space + w > width:
                self.line(line, size, leading, color, style, tracking)
                line, used = [], 0.0
            if line:
                used += space
            line.append((word, word_style))
            used += w
        if line:
            self.line(line, size, leading, color, style, tracking)
        self.y -= after

    def rule(self, before=0.0, after=0.0, color=RULE):
        self.y -= before
        self.ops.append(b"%s 0.6 w %s %s m %s %s l S"
                        % (rgb(color, stroke=True), num(MARGIN), num(self.y),
                           num(MARGIN + COL_W), num(self.y)))
        self.y -= after

    def banner(self, path, height=BANNER_H):
        """A photo across the top of the first page, cropped to fill."""
        if not self.place_image(path, (MARGIN, self.y - height, COL_W, height)):
            return False
        self.y -= height
        return True

    def place_image(self, path, box):
        """Draw a JPEG into `box`, cropped to fill it. False if this file is
        one a PDF reader can't be handed directly — the caller decides what to
        put there instead, and the photo travels in the zip either way."""
        if path in self.skipped:
            return False
        data, name = None, self.placed.get(path)
        if name is None:
            data = io.open(path, "rb").read() \
                if path.lower().endswith(JPEG_EXT) else b""
            name = self.image_object(path, data)
            if name is None:
                return False
        if data is None:
            data = io.open(path, "rb").read()
        iw, ih = jpeg_info(data)[:2]
        m = cover_matrix(box, iw, ih, jpeg_orientation(data))
        self.ops.append(b"q %s %s %s %s re W n %s cm /%s Do Q"
                        % (num(box[0]), num(box[1]), num(box[2]), num(box[3]),
                           b" ".join(num(v) for v in m), name))
        return True

    def image_object(self, path, data):
        """The JPEG goes into the file exactly as it is: DCTDecode is the
        reader's own decoder, so nothing here has to understand the pixels.
        None for a file that can't go in — the reason is warned about once."""
        info = jpeg_info(data) if data else None
        if not info:
            reason = "is not a JPEG" if not data else "is not readable as a JPEG"
        elif info[3]:
            reason = ("is a progressive JPEG, which many PDF readers show "
                      "blank — save it as baseline")
        elif info[2] not in (1, 3):
            reason = "is neither greyscale nor RGB"
        else:
            reason = None
        if reason:
            # Only worth saying for a photo somebody expected to see; every
            # one of them is in the zip regardless.
            if data or path.lower().endswith(JPEG_EXT):
                events.warn("%s %s; it is in the zip but not in the PDF"
                            % (path, reason))
            self.skipped.add(path)
            return None
        iw, ih, comps, _progressive = info
        name = b"Im%d" % len(self.images)
        self.images.append((name, self.pdf.add(self.pdf.stream(
            b"/Type /XObject /Subtype /Image /Width %d /Height %d "
            b"/ColorSpace %s /BitsPerComponent 8 /Filter /DCTDecode"
            % (iw, ih, b"/DeviceRGB" if comps == 3 else b"/DeviceGray"),
            data, compress=False))))
        self.placed[path] = name
        return name

    def frame(self, box):
        """Stands in for a photo the reader can't display — a PNG, or a
        progressive JPEG."""
        self.ops.append(b"%s 0.6 w %s %s %s %s re S"
                        % (rgb(RULE, stroke=True), num(box[0]), num(box[1]),
                           num(box[2]), num(box[3])))

    def contact_sheet(self, paths, cols=3, gap=14.0):
        """Thumbnails with their filenames, so a programmer can pick the shot
        they want by name without unpacking the zip first."""
        cell = (COL_W - gap * (cols - 1)) / cols
        for start in range(0, len(paths), cols):
            row = paths[start:start + cols]
            self.room(cell + 34)
            top = self.y
            for i, path in enumerate(row):
                x = MARGIN + i * (cell + gap)
                box = (x, top - cell, cell, cell)
                if not self.place_image(path, box):
                    self.frame(box)
                for j, text in enumerate(photo_caption(path)):
                    self.draw([(ellipsize(text, 8.2, cell), "")], 8.2,
                              top - cell - 11 - j * 10, SUB, x=x)
            self.y = top - cell - 21 - 18

    def footer(self, text):
        """Written once the flow is done, so it lands on every page including
        ones the text broke onto by itself."""
        for i, ops in enumerate(self.pages):
            self.ops = ops
            self.draw([(text, "")], 7.6, MARGIN - 26, SUB)
            n = "%d / %d" % (i + 1, len(self.pages))
            x = MARGIN + COL_W - text_width(n, 7.6)
            self.draw([(n, "")], 7.6, MARGIN - 26, SUB, x=x)

    def save(self, path, title, author):
        pdf = self.pdf
        catalog, pages_obj = pdf.reserve(), pdf.reserve()
        fonts = []
        for key, base in ((b"F1", b"Helvetica"), (b"F2", b"Helvetica-Bold"),
                          (b"F3", b"Helvetica-Oblique")):
            fonts.append((key, pdf.add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /%s "
                b"/Encoding /WinAnsiEncoding >>" % base)))
        res = b"<< /Font << %s >>" % b" ".join(
            b"/%s %d 0 R" % (k, n) for k, n in fonts)
        if self.images:
            res += b" /XObject << %s >>" % b" ".join(
                b"/%s %d 0 R" % (k, n) for k, n in self.images)
        res += b" >>"
        kids = []
        for ops in self.pages:
            content = pdf.add(pdf.stream(b"", b"\n".join(ops)))
            kids.append(pdf.add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] "
                b"/Resources %s /Contents %d 0 R >>"
                % (pages_obj, num(PAGE_W), num(PAGE_H), res, content)))
        pdf.add(b"<< /Type /Pages /Count %d /Kids [%s] >>"
                % (len(kids), b" ".join(b"%d 0 R" % k for k in kids)), pages_obj)
        pdf.add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj, catalog)
        info = pdf.add(b"<< /Title %s /Author %s /Creator %s >>"
                       % (pdf_text_string(title), pdf_text_string(author),
                          pdf_text_string("scripts/press_kit.py")))
        io.open(path, "wb").write(pdf.out(catalog, info))


# --------------------------------------------------------------- the build --

def slug(text):
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def photos(root):
    """Every image in press_kit/, and in press_kit/photos/ for anyone who
    would rather keep the folder tidy. Sorted, so the kit is stable."""
    found = []
    for folder in (root, os.path.join(root, "photos")):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.startswith(".") or not name.lower().endswith(PHOTO_EXT):
                continue
            found.append(os.path.join(folder, name))
    return found


def cover_photo(pics, wanted):
    """The named photo if it is there, else the first JPEG — PNG and TIFF can
    be handed to a programmer but not embedded without a decoder."""
    jpegs = [p for p in pics if p.lower().endswith(JPEG_EXT)]
    if wanted:
        for p in jpegs:
            if os.path.basename(p).lower() == wanted.lower():
                return p
        events.warn("press kit: photo %r is not a JPEG in %s; using the first one"
                    % (wanted, PRESS_DIR))
    return jpegs[0] if jpegs else None


def ellipsize(text, size, width):
    if text_width(text, size) <= width:
        return text
    while text and text_width(text + "\u2026", size) > width:
        text = text[:-1]
    return text + "\u2026"


def photo_caption(path):
    """Filename, then the pixel size — the two things someone choosing a shot
    for a printed programme actually needs."""
    lines = [os.path.basename(path)]
    if path.lower().endswith(JPEG_EXT):
        data = io.open(path, "rb").read()
        info = jpeg_info(data)
        if info:
            w, h = info[0], info[1]
            if jpeg_orientation(data) in (5, 6, 7, 8):
                w, h = h, w
            lines.append("%d × %d px" % (w, h))
    return lines


def render(meta, langs, pics, pdf_path):
    name = meta.get("name") or "Press kit"
    doc = Doc()

    cover = cover_photo(pics, meta.get("photo"))
    if cover and doc.banner(cover):
        doc.y -= 34
    else:
        doc.y -= 6

    doc.para(name.upper(), size=27, style="b", tracking=1.4, after=4)
    contact = [meta.get(k) for k in ("email", "website", "youtube")]
    contact = " · ".join(c for c in contact if c)
    if contact:
        doc.para(contact, size=9.4, color=SUB, after=10)
    doc.rule(after=4)

    for code, tagline, paras in langs:
        # Keep the language heading with the first lines of its bio.
        doc.room(140)
        doc.para(code.upper(), size=8, style="b", color=ACCENT, tracking=1.0,
                 before=22, after=1)
        doc.para(LABELS.get(code, code.upper()), size=16.5, style="b", after=2)
        if tagline:
            doc.para(tagline, size=10.2, style="i", color=SUB, after=6)
        for para in paras:
            doc.para(para, size=10.4, leading=15.6, after=8)

    if pics:
        # Heading, note and the first row of thumbnails belong together.
        doc.room(300)
        doc.rule(before=26, after=4)
        doc.para(PHOTOS_HEADING, size=13, style="b", before=16, after=4)
        for code, _tagline, _paras in langs:
            if code in PHOTOS_NOTE:
                doc.para(PHOTOS_NOTE[code], size=9.2, style="i", color=SUB,
                         leading=12.6, after=0)
        doc.y -= 16
        doc.contact_sheet(pics)
        if meta.get("credit"):
            doc.para(meta["credit"], size=9.2, style="i", color=SUB, before=4)

    doc.footer("%s — press kit" % name)
    doc.save(pdf_path, "%s — press kit" % name, name)
    return len(doc.pages)


def write_zip(path, pdf_path, md_path, pics, folder):
    """One folder inside the archive, so it doesn't scatter over a desktop."""
    with zipfile.ZipFile(path, "w") as z:
        def put(src, arc, compress):
            info = zipfile.ZipInfo(folder + "/" + arc,
                                   date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = compress
            info.external_attr = 0o644 << 16
            z.writestr(info, io.open(src, "rb").read())

        put(pdf_path, os.path.basename(pdf_path), zipfile.ZIP_DEFLATED)
        # The bios in plain text as well: a programmer pasting a bio into a
        # programme booklet should not have to pull it back out of a PDF.
        put(md_path, "bios.md", zipfile.ZIP_DEFLATED)
        for p in pics:
            # Photos are compressed already; deflating them again buys nothing.
            put(p, "photos/" + os.path.basename(p), zipfile.ZIP_STORED)


# Singular / plural of "photograph", for the line under the download link.
KIT_META = {
    "pt": ("fotografia", "fotografias"),
    "en": ("photograph", "photographs"),
    "de": ("Foto", "Fotos"),
}


def render_link(zip_path, size, count, indent="      "):
    """The download link for the contact page, generated rather than typed:
    the size and the photo count are read off the kit that was just built, and
    a build that produced no kit leaves nothing to click.

    {{base}} is filled in per page by build.py, the same as the shared parts.
    The size line carries its own wording per language (data-pt/en/de) rather
    than a dictionary key, because the numbers in it are only known here."""
    lines = []
    for lang, (one, many) in KIT_META.items():
        if count:
            text = "ZIP · %s · %d %s + PDF (PT/EN/DE)" % (
                human(size), count, one if count == 1 else many)
        else:
            text = "ZIP · %s · PDF (PT/EN/DE)" % human(size)
        lines.append((lang, text))
    attrs = " ".join('data-%s="%s"' % (lang, html.escape(text, quote=True))
                     for lang, text in lines)
    href = "{{base}}" + zip_path.replace(os.sep, "/")
    return "\n".join([
        '%s<a class="cta" href="%s" download data-i18n="press.cta">'
        'Descarregar press kit ↓</a>' % (indent, html.escape(href, quote=True)),
        '%s<p class="pk-meta" %s>%s</p>' % (indent, attrs,
                                            html.escape(lines[0][1])),
    ])


def build():
    """Returns (zip path, bytes, page count, photo count) or None if there is
    nothing to build. Never raises: a broken press kit must not fail a deploy."""
    root = os.environ.get("PRESS_DIR", "").strip() or PRESS_DIR
    md_path = os.path.join(root, BIOS_MD)
    if not os.path.exists(md_path):
        events.warn("no %s; press kit not built" % md_path)
        return None
    meta, langs = parse_bios(io.open(md_path, encoding="utf-8").read())
    if not langs:
        events.warn("%s has no `# pt|en|de` sections; press kit not built" % md_path)
        return None

    pics = photos(root)
    if not pics:
        events.warn("no photos in %s — the kit is built with the PDF alone" % root)

    stem = slug(meta.get("name", ""))
    stem = stem + "-press-kit" if stem else "press-kit"
    pdf_path = os.path.join(root, stem + ".pdf")
    zip_path = os.path.join(root, stem + ".zip")
    pages = render(meta, langs, pics, pdf_path)
    write_zip(zip_path, pdf_path, md_path, pics, stem)
    return zip_path, os.path.getsize(zip_path), pages, len(pics)


def main():
    out = build()
    if not out:
        return 1
    zip_path, size, pages, count = out
    print("  %-22s %d page(s)" % (zip_path.replace(".zip", ".pdf"), pages))
    print("  %-22s %s, %d photo(s)" % (zip_path, human(size), count))
    return 0


def human(size):
    if size >= 1024 * 1024:
        return "%.1f MB" % (size / 1024.0 / 1024.0)
    return "%d KB" % max(1, size // 1024)


if __name__ == "__main__":
    sys.exit(main())
