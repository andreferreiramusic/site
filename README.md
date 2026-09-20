# André Ferreira — site

Static site for classical guitarist & lutenist André Ferreira. Plain HTML/CSS/JS,
concert dates generated from `data/events.csv` at deploy time, hosted for free
on GitHub Pages.

## Structure

```
index.html                    home page
pages/about.html              the other five pages — each one is a real,
pages/guitar.html             complete page you edit directly
pages/lute.html
pages/dates.html
pages/contact.html
templates/parts.html          shared head / header / footer, defined once
data/events.csv               every concert, past and upcoming
data/videos.csv               one video per page (page, video_id, caption)
content/<page>/<block>_<lang>.md   every translatable word, one file each
press_kit/bios.md             the three press bios; the photos sit beside it
scripts/build.py              writes the shared parts, concerts and videos into the pages
scripts/events.py             reads the CSV (library used by build.py)
scripts/press_kit.py          builds the press-kit PDF and zip (library too)
assets/css/style.css          all styles (black / cream-text / light-wood palette)
assets/js/main.js             language toggle (PT/EN/DE) + menu + video player
assets/img/                   photos (see assets/img/README.md)
.github/workflows/deploy.yml  GitHub Actions workflow that deploys to Pages
```

## Local preview

```
python3 -m http.server 8000
```

Then open <http://localhost:8000>. Use a server rather than double-clicking the
files: over `file://` some browsers refuse `localStorage`, which is where the
chosen language is remembered, so the PT/EN/DE toggle won't survive a page
change. Ctrl+C stops it.

## Editing a page

Open the page and edit it — `pages/about.html` is the real page, there is no
separate source file. Only the regions between marker comments are generated:

```html
<!-- nav:start -->
  …written by scripts/build.py, don't edit…
<!-- nav:end -->
```

Everything outside the markers is yours and is never touched, so text and
layout changes need no build step at all.

Run the build when you change either of the shared things:

```
python3 scripts/build.py
```

- `templates/parts.html` — the head, header/nav and footer, shared by all six
  pages. Edit once, build, and all six update.
- `data/events.csv` — the concert list (see below).

The build is idempotent: running it twice changes nothing. It also runs on
every deploy, which is what keeps "upcoming" honest — see below.

Adding a page means creating the file with the markers you want, then adding it
to the `NAV` list at the top of `scripts/build.py` so it appears in the menu.

## Publish it

1. Create an empty repo on GitHub (no README/license, so it doesn't conflict
   with what's here).
2. From this folder:
   ```
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Build and deployment → Source: "GitHub
   Actions"**. The included workflow will pick up automatically on this and
   future pushes to `main`, and your site will be live at
   `https://<your-username>.github.io/<repo-name>/` a minute or two later
   (check the Actions tab for progress).

## Updating concert dates

Everything lives in `data/events.csv` — past and upcoming together, one row per
engagement. Edit it, commit, push; the deploy regenerates the home page.

**The home page shows the next 4**; `pages/dates.html` shows every upcoming
event plus the full archive below it, newest first. Which events count as
upcoming is decided at build time against the current date, so past events are
never deleted — they just move from the upcoming list into the archive.

The workflow also runs once a day precisely so an event moves to the archive the
day after it's played, without anyone pushing anything.

To show more or fewer on the home page, change `HOME_LIMIT` at the top of
`scripts/build.py`. Archive rows deliberately carry no ticket links.

### Columns

Only `date` is required; every other column may be left blank.

| column | example | notes |
|---|---|---|
| `date` | `2026-12-21` | ISO `yyyy-mm-dd` only |
| `end_date` | `2026-11-03` | for a run of **consecutive** days |
| `title` | `Concerto de Natal` | Portuguese / default |
| `title_en`, `title_de` | `Christmas Concert` | optional; blank = use `title` |
| `performers` | `Bach Consort Wien` | shown in grey under the title |
| `venue` | `Wiener Musikverein` | |
| `city` | `Vienna` | |
| `country` | `AT` | venue/city/country are joined with commas |
| `tickets` | `https://…` | blank = no ticket link on that row |

Anything containing a comma must be wrapped in double quotes, as the existing
rows do: `"Concentus Musicus Wien, Stefan Gottfried & Michael Schade"`.

### Dates spanning more than one day

| Situation | How to write it | Shows as |
|---|---|---|
| Single evening | `date` = `2026-12-21` | `21 DEZ` |
| Consecutive run, 25 Oct–3 Nov | `date` = `2026-10-25`, `end_date` = `2026-11-03` | `25 OUT – 03 NOV` |
| Separate nights, 16th and 18th | `date` = `2026-10-16; 2026-10-18` | `16 & 18 OUT` |

Put non-consecutive dates in the **`date`** cell separated by `;`, as many as
you like — three become `03, 07 & 12 NOV`. `end_date` is only for an unbroken
run, and is ignored if `date` already lists several dates.

The two behave differently once under way, deliberately: a consecutive run stays
listed in full until its last day (it's one engagement), while separate nights
drop off one at a time as each is played.

**You never type the year label.** It's added only when the date isn't in the
current year, so the list stays uncluttered but nothing distant is ambiguous:

| | Rendered |
|---|---|
| This year | `07 NOV` |
| Next year | `22 JAN 2027` |
| Two years out | `04 JUN 2028` |
| All in one later year | `29 JAN & 02 FEV 2027` |
| Straddling new year | `28 DEZ – 02 JAN 2027` |

## Editing the texts

**Every word on the site that changes with the language is a Markdown file
under `content/`** — the biography and the word "Tickets" alike. Nothing is
written in JavaScript, and nothing is typed into a page twice.

One folder per page, one file per text, named `<block>_<lang>.md`:

```
content/home/     main_pt.md  main_en.md  main_de.md     the intro paragraph
                  hero-eyebrow_*.md    under the big name
                  hero-cta_*.md        the button down to the concerts
                  dates-heading_*.md   dates-all_*.md
                  link-about_*.md  link-guitar_*.md  link-lute_*.md
content/about/    main_*.md            the biography, teaching and mdw link included
content/guitar/   main_*.md
content/lute/     main_*.md
content/dates/    upcoming-heading_*.md  past-heading_*.md  past-none_*.md
content/contact/  main_*.md            the intro
                  email-label_*.md
                  press-heading_*.md  press-body_*.md  press-cta_*.md
content/site/     nav-home_*.md … nav-contact_*.md   the menu
                  tickets_*.md  concerts-none_*.md   the concert lists
                  video-play_*.md                    the player's aria-label
```

`main_` is the page's own prose; the rest are the labels around it. `site/`
holds what belongs to no single page — the menu, and the wording the concert
rows and video poster are generated with.

Grouping by page rather than by language puts a text and its translations in
one folder: change the wording and the other two are already open in front of
you, and a translation nobody has written yet is a visible gap.

Edit a file, run `python3 scripts/build.py`, commit. The build writes the
Portuguese into the HTML — so every page reads correctly before any JavaScript
runs, and for search engines — and compiles all three languages into
`assets/js/content.js`, which the language toggle uses. One edit, both places.

Both are generated: never edit `assets/js/content.js`, the text inside a page's
`<!-- text:…:start -->` markers, or the words inside an element carrying
`data-i18n` — the build overwrites all three.

Which languages exist is read off the filenames. A fourth is `fr.md` beside
each of the others plus a button in `templates/parts.html`; `scripts/build.py`
lists no languages anywhere.

### Adding a new text

Add the file, then one row to the `TEXTS` table at the top of
`scripts/build.py`:

```python
    ("contact", "phone-label",  "contact.phone",  LABEL),
```

…and reference it from the markup with `data-i18n="contact.phone"`. `PROSE`
wraps each paragraph in a `<p>` for a `.prose` block; `LABEL` goes in as it is,
for text inside a link, a heading or an `aria-label`.

### What the Markdown supports

Blank line between paragraphs, plus:

| Markdown | Result |
|---|---|
| `## Heading` | an `<h2>`; `###` an `<h3>`, and so on down to `######` |
| `**bold**` | **bold** |
| `*italic*` | *italic* |
| `[label](https://example.com)` | a link — external ones get `target="_blank"` automatically |

That is the whole list. It is a small converter inside `build.py` rather than a
library, so the build keeps working with nothing installed beyond Python.
Anything else (lists, images, tables, block quotes) is not markup here and
comes through as the literal characters you typed, and raw HTML in a `.md`
file is escaped rather than passed through.

A heading goes on its own line and needs no blank line after it. Keep to `##`
and below: each page already opens with its own `<h1>`, and the build warns if
a text adds a second one. Headings only apply to the prose files — a label is
one line by definition, so a `#` in one stays a `#`.

## Videos

`data/videos.csv` holds one row per page that should show a video:

| page | video_id | caption |
|---|---|---|
| `guitar` | `KjQrODARBj0` | J. K. Mertz — "An die Entfernte" |
| `lute` | `8HuC4jDdDU4` | J. S. Bach — Violin Sonata No. 3, BWV 1005: Largo |

- `page` is the page key — `home`, `about`, `guitar`, `lute`, `dates`, `contact`.
  The page must contain the `<!-- video:start -->` / `<!-- video:end -->`
  markers for the video to land anywhere; add them where you want it to appear.
- `video_id` takes either the bare id or a pasted YouTube URL (`youtu.be/…`,
  `watch?v=…`, `/embed/…`, `/shorts/…`) — the build extracts the id either way.
- `caption` shows under the player. Wrap it in double quotes if it contains a
  comma, as the Bach row does.

Remove a row and that page's video block builds empty; the markers stay, so you
can add it back later. Only the poster image loads on page view — the YouTube
player is fetched only when someone actually presses play.

### If the CSV breaks

The build never fails the deploy over a bad CSV. If it's missing, unparseable,
or has no upcoming events, it logs a warning on the Actions run and ships the
concert rows currently committed in `index.html` instead. A malformed date is
skipped with a warning naming the offending row, and the rest still build.

## Adding real photos

See `assets/img/README.md` for expected filenames and exactly which lines in
`index.html` / `style.css` to change (marked with HTML comments).

## The press kit

The contact page offers concert programmers a single download: a PDF with the
biography in all three languages and a contact sheet of the photographs, zipped
together with the photos themselves at full size.

```
press_kit/bios.md      the three bios — front matter, then `# pt`, `# en`, `# de`
press_kit/*.jpg        the photos; drop them in, name them in the order you want
```

Edit either, run `python3 scripts/build.py`, commit. The PDF, the zip, and the
size printed under the download link are all generated from what is in that
folder — nothing about the kit is typed into a page by hand, which is what
stops the link promising "3 photographs" once there are five. The deploy
rebuilds it too, so committing a photo is enough on its own.

`press_kit/README.md` has the details: what the front matter holds, why the
photos should be baseline JPEGs, and how to choose the one on the cover.

The PDF is written by `scripts/press_kit.py` directly, without a PDF library —
the deploy runs bare `python3` with nothing installed, and this keeps it that
way. It sets the bios in Helvetica, one of the 14 faces every reader carries,
so no font is embedded either.

## Link previews

Pasting the address into WhatsApp, Telegram, Signal, Messenger, Slack or
iMessage shows a card: a wide picture, the page's title, its description. The
tags that produce it are part of the shared head in `templates/parts.html`, so
every page gets them, and `scripts/build.py` fills in the per-page wording from
that page's own `<title>` and `<meta name="description">` — there is no second
copy of the words to keep in step.

A page that wants the card to read differently from its meta description adds
an optional `<meta name="share-description" content="…">` beside it, and the
card uses that instead. `index.html` carries one: the meta description is the
Portuguese a search engine indexes, while a pasted link travels, so the card
speaks English.

The picture is `assets/img/og.jpg`: a real screenshot of the hero — the photo
below the navbar, at its own full 3:2 height — taken by a headless browser,
which is why it can never drift from the site. The bar itself is hidden for the
shot, and the hero is pinned to 3:2, by a few lines of CSS the script injects
in memory; nothing card-shaped is shipped to visitors.

```
python3 scripts/og_image.py            # Portuguese, the site's own language
python3 scripts/og_image.py --lang en  # or en / de
```

Run it when the hero photo, the name or the eyebrow changes, then commit the
JPEG. It takes a few seconds. It is **not** part of `scripts/build.py` on
purpose: it needs Chrome, and the Actions runner that builds the site has none.
It looks for Chrome, Chromium, Brave or Edge in the usual places — set
`CHROME=/path/to/it` if yours is elsewhere.

It uses Chrome's own profile, with extensions and background networking turned
off so nothing of yours reaches the picture. If Chrome is busy and won't share,
it retries on a private profile — that one can take a minute or two the first
time, because a brand-new Chrome profile sets itself up before it will render
anything.

Two numbers matter and the script holds both: **1200x800**, wide enough that
every one of those apps draws a big card rather than a thumbnail beside the
text, and **under 300 KB**, which is what WhatsApp will actually fetch — the
script steps the JPEG quality down until it fits and warns if it cannot. The
size is declared in `og:image:width` / `og:image:height` too, so changing one
means changing the other in `templates/parts.html`.

WhatsApp, Telegram and Signal show a 3:2 card whole. Facebook and X prefer a
wider 1.91:1 and may trim the top and bottom of it; the name sits low in the
frame, so it survives that crop.

The URLs in those tags must be absolute, because the chat app fetches the page
from its own servers where a relative path resolves against nothing. That base
is `SITE_URL` at the top of `scripts/build.py`; it is also the one thing to
change when the custom domain lands (see below), or set it in the environment:

```
SITE_URL=https://andreferreiramusic.com python3 scripts/build.py
```

After a deploy, a cached old preview can linger. Facebook's
[sharing debugger](https://developers.facebook.com/tools/debug/) re-scrapes on
demand; WhatsApp caches per device, so the quickest check is a fresh chat.

## Languages

Every translated string lives in `content/` (see **Editing the texts**) and is
compiled into `assets/js/content.js`. `data-i18n="key"` attributes in the HTML
pick it up; the toggle swaps the whole page without reloading, and remembers
the choice in `localStorage`.

Concert rows are the exception: their wording comes from the sheet, so each row
carries its own `data-pt` / `data-en` / `data-de` attributes instead of a
dictionary key.

## Custom domain later

Not wired up yet (site currently targets the free `github.io` URL). When
you're ready to point `andreferreiramusic.com` at it: add a `CNAME` file at
the repo root containing just the domain, and add a `CNAME` DNS record at
your registrar pointing `www` (or an `ALIAS`/`ANAME`/`A` record for the apex
domain per GitHub's current Pages docs) at `<your-username>.github.io`. Ask
and I'll do this step when you're ready.

Also change `SITE_URL` at the top of `scripts/build.py` and rebuild, so the
link-preview and canonical tags point at the new address rather than the old
`github.io` one.
