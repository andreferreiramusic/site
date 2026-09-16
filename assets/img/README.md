Drop real photos here, then swap the placeholders in index.html:

- hero.jpg — full portrait used behind the big name on the homepage (portrait
  orientation works best, e.g. 1600x2000). Wire it in by setting a background
  image on `.hero` in assets/css/style.css, or restructure to an <img> — see
  the HTML comment above the hero section in index.html.
- bio.jpg — the smaller photo next to the biography text (e.g. 1200x1500,
  4:5). Replace the placeholder <span>/<svg> inside .bio-photo in index.html
  with `<img src="assets/img/bio.jpg" alt="André Ferreira">`.
- video-thumb.jpg — thumbnail for the video card (16:9). Replace the
  placeholder inside .video-thumb the same way.

Keep filenames as above, or update the paths in index.html / style.css to
match whatever you name them.
