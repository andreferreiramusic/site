# André Ferreira — site

Static site for classical guitarist & lutenist André Ferreira. Plain HTML/CSS/JS
(no build step), htmx for loading the concerts list, hosted for free on GitHub
Pages.

## Structure

```
index.html                    the whole one-page site
assets/css/style.css          all styles (black / cream-text / light-wood palette)
assets/js/main.js             language toggle (PT/EN/DE) + menu + htmx re-translate
assets/img/                   drop real photos here (see assets/img/README.md)
partials/concerts.html        the concert list — htmx loads this into the page
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

Edit `partials/concerts.html` directly — each concert is one `.crow` block
(date / title / venue / ticket link). Copy, edit or delete a block, commit,
push; the Action redeploys automatically. No build tooling needed.

**Later, from a Google Sheet:** the concerts list is deliberately its own
small file so it's easy to generate instead of hand-edit later — e.g. publish
your Sheet as CSV ("File → Share → Publish to web"), then add a small script
(Python or Node) that fetches that CSV and writes `partials/concerts.html` in
the same `.crow` format, run as an extra step in the GitHub Actions workflow
before deploy. Say the word when you're ready and I'll wire that up.

## Adding real photos

See `assets/img/README.md` for expected filenames and exactly which lines in
`index.html` / `style.css` to change (marked with HTML comments).

## Languages

Every translated string lives in the `i18n` dictionaries at the top of
`assets/js/main.js` (`pt` / `en` / `de` objects). Edit the wording there;
`data-i18n="key"` attributes in the HTML pick it up automatically, including
inside the htmx-loaded concerts partial.

## Custom domain later

Not wired up yet (site currently targets the free `github.io` URL). When
you're ready to point `andreferreiramusic.com` at it: add a `CNAME` file at
the repo root containing just the domain, and add a `CNAME` DNS record at
your registrar pointing `www` (or an `ALIAS`/`ANAME`/`A` record for the apex
domain per GitHub's current Pages docs) at `<your-username>.github.io`. Ask
and I'll do this step when you're ready.
