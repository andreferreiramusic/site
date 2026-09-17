# André Ferreira — site

Static site for classical guitarist & lutenist André Ferreira. Plain HTML/CSS/JS,
concert dates generated from `data/events.csv` at deploy time, hosted for free
on GitHub Pages.

## Structure

```
index.html                    the whole one-page site
assets/css/style.css          all styles (black / cream-text / light-wood palette)
assets/js/main.js             language toggle (PT/EN/DE) + menu + video player
assets/img/                   photos (see assets/img/README.md)
data/events.csv               every concert, past and upcoming — the one file to edit
scripts/build_concerts.py     reads that CSV, writes the upcoming rows into index.html
.github/workflows/deploy.yml  GitHub Actions workflow that deploys to Pages
```

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

**The home page shows the next 4 upcoming events only**, chosen at build time by
comparing against the date of the build. Past events are never deleted — they
stay in the CSV as the archive, they just stop being rendered. The workflow also
runs once a day precisely so an event disappears from the site the day after
it's played, without anyone pushing anything.

To show more or fewer, change `LIMIT` at the top of `scripts/build_concerts.py`.

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

### If the CSV breaks

The build never fails the deploy over a bad CSV. If it's missing, unparseable,
or has no upcoming events, it logs a warning on the Actions run and ships the
concert rows currently committed in `index.html` instead. A malformed date is
skipped with a warning naming the offending row, and the rest still build.

## Adding real photos

See `assets/img/README.md` for expected filenames and exactly which lines in
`index.html` / `style.css` to change (marked with HTML comments).

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
