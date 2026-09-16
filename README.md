# André Ferreira — site

Static site for classical guitarist & lutenist André Ferreira. Plain HTML/CSS/JS,
concert dates generated from a Google Sheet at deploy time, hosted for free on
GitHub Pages.

## Structure

```
index.html                    the whole one-page site
assets/css/style.css          all styles (black / cream-text / light-wood palette)
assets/js/main.js             language toggle (PT/EN/DE) + menu + video player
assets/img/                   drop real photos here (see assets/img/README.md)
scripts/build_concerts.py     fetches the Google Sheet, writes the concert rows
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

Dates come from a Google Sheet. Edit the sheet; the site catches up on the next
deploy — automatically once a day, or immediately via **Actions → Deploy to
GitHub Pages → Run workflow**.

### One-time setup

1. Make a sheet with this header row (only `date` is required; order doesn't
   matter, capitalisation doesn't either):

   | date | title | title_en | title_de | venue | tickets |
   |------|-------|----------|----------|-------|---------|
   | 2026-10-18 | Bach Consort Wien | | | Musikverein, Wien, AT | https://… |
   | 2027-01-22 | Recital a solo | Solo recital | Solorezital | Fundação Gulbenkian, Lisboa, PT | |

   - `date` must be ISO `yyyy-mm-dd`. **Past dates disappear from the site by
     themselves** — no need to delete old rows.
   - `title` is the Portuguese/default wording. Fill `title_en`/`title_de` only
     when it actually differs; "Bach Consort Wien" is the same in all three, but
     "Recital a solo" isn't. Blank means "use `title`".
   - `tickets` blank = no ticket link on that row.
   - The day/month label (`18 OUT` / `18 OCT` / `18 OKT`) is generated per
     language — don't put it in the sheet.

2. **File → Share → Publish to web**, choose the sheet, pick **Comma-separated
   values (.csv)**, Publish. Copy the URL.

3. Give the URL to the build, either:
   - **Settings → Secrets and variables → Actions → Variables → New variable**,
     named `SHEET_CSV_URL` (needs repo admin), or
   - paste it into `SHEET_CSV_URL` at the top of `scripts/build_concerts.py`
     and commit. The sheet is already public once published, so this is not a
     secret — it's just less convenient to change.

### If the sheet breaks

The build never fails the deploy over a bad sheet. If it's unreachable, empty
of upcoming dates, or malformed, it logs a warning on the Actions run and ships
the concert rows currently committed in `index.html` instead. So keep a
plausible set of rows there as the fallback.

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
