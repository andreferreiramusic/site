# Press kit

What a concert programmer downloads from the contact page: one PDF with the
biography in all three languages, and the photographs at full resolution.

Two things here are edited by hand — `bios.md` and the photos. Everything else
is generated:

```
bios.md                          the three bios (this is the only text source)
*.jpg                            the photos — drop them straight in here
andre-ferreira-press-kit.pdf     generated, git-ignored
andre-ferreira-press-kit.zip     generated, git-ignored
```

Rebuild with either of:

```
python3 scripts/press_kit.py     just the kit
python3 scripts/build.py         the whole site, the kit included
```

The deploy runs the build too, so committing a new photo or an edited bio is
enough — the PDF, the zip, and the file size printed under the download link
on the contact page all follow on their own.

## The photos

Any `.jpg`, `.png`, `.tif` or `.webp` in this folder goes into the zip, sorted
by filename, and is listed on the PDF's last page with its pixel size. A
`photos/` subfolder is read as well if you would rather keep this one tidy.

Name them so the order is the order you want them seen —
`andre-ferreira-01.jpg`, `-02`, `-03`.

Two details worth knowing:

- **Only JPEGs appear inside the PDF** (the cover photo and the thumbnails on
  the last page). A PNG or TIFF still travels in the zip; it just shows as an
  empty frame on the contact sheet. Baseline JPEG, not progressive — a
  progressive one is skipped with a warning, because many PDF readers show it
  blank.
- **Send the originals**, not the web-sized copies. A programme printed at
  300 dpi wants roughly 2500 px across for a half page; the files sitting here
  now are the site's own web images, put there so the download works today.
  Overwrite them with the photographer's files when you have them.

The first photo alphabetically goes across the top of the PDF. To choose a
different one, name it in the `photo:` line of `bios.md`.

## bios.md

Front matter first, between `---` lines: `name`, `email`, `website`, `youtube`
print in the PDF header (a blank one is simply left out), `photo` picks the
cover, `credit` adds a line under the photo list. `#` starts a comment.

Then one section per language:

```markdown
# pt

> Guitarrista & Alaudista · Viena

First paragraph…

Second paragraph…
```

`# pt`, `# en`, `# de` — the heading is the language code, and the PDF prints
the biography's name in that language. The `>` line is that language's
one-line description, and is optional. Blank line between paragraphs;
`**bold**`, `*italic*` and `[label](url)` work, the same as the site's own
Markdown.

The text is independent of `content/<lang>/about.md`, which is what the About
page shows. They start out as the same words — a press bio and a website bio
usually want to diverge, and this way they can.

Anything CP1252 covers is printed as typed, which is every accent in
Portuguese, German and English. A letter outside it (a Polish ł, say) loses
its diacritic rather than the letter.
