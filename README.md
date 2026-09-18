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
content/<text>/<lang>.md      the page texts, one folder per block of prose
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

## Editing the page texts

Every block of prose lives in a Markdown file, one per language:

```
content/home-intro/     the short bio on the home page
content/about/          the biography on the About page
content/teaching/       the Teaching paragraph on About
content/guitar/         the Guitar page text
content/lute/           the Lute page text
content/contact/        the intro on the Contact page
```

Each of those folders holds one file per language — `pt.md`, `en.md`, `de.md`:

```
content/about/pt.md
content/about/en.md
content/about/de.md
```

Grouping by text rather than by language keeps a paragraph and its
translations side by side, which is how they are actually edited: change the
wording and you want the other two open. A translation nobody has written yet
shows up as a gap in the folder you are already in, and the build says so.

The languages come from the filenames, so nothing lists them — a fourth means
dropping `fr.md` into each folder, and adding the UI strings to
`assets/js/main.js` plus a button in `templates/parts.html`.

Edit the file, run `python3 scripts/build.py`, commit. The build does two things
with them: it writes the Portuguese copy into the HTML (so the page reads
correctly before any JavaScript runs, and for search engines), and it compiles
all three languages into `assets/js/content.js`, which the language toggle uses.

Both of those are generated — never edit `assets/js/content.js` or the text
inside a page's `<!-- text:…:start -->` markers by hand.

### What the Markdown supports

Blank line between paragraphs, plus:

| Markdown | Result |
|---|---|
| `**bold**` | **bold** |
| `*italic*` | *italic* |
| `[label](https://example.com)` | a link — external ones get `target="_blank"` automatically |

That is the whole list. It is a small converter inside `build.py` rather than a
library, so the build keeps working with nothing installed beyond Python.
Anything else (headings, lists, images) is ignored, and raw HTML in a `.md` file
is escaped rather than passed through.

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

## Languages

Every translated string lives in the `i18n` dictionaries at the top of
`assets/js/main.js` (`pt` / `en` / `de` objects). Edit the wording there;
`data-i18n="key"` attributes in the HTML pick it up automatically.

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
