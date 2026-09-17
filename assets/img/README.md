Drop real photos here, then swap the placeholders in index.html:

- hero.jpeg — **in use.** Full portrait behind the big name on the homepage,
  set as a background image on `.hero` in assets/css/style.css with a dark
  gradient over it so the white name stays readable. To swap it, overwrite the
  file (keeping the name) or update the url() in that rule.
- bio.jpg — the smaller photo next to the biography text (e.g. 1200x1500,
  4:5). Replace the placeholder <span>/<svg> inside .bio-photo in index.html
  with `<img src="assets/img/bio.jpg" alt="André Ferreira">`.
- video-thumb.jpg — thumbnail for the video card (16:9). Replace the
  placeholder inside .video-thumb the same way.

Keep filenames as above, or update the paths in index.html / style.css to
match whatever you name them.
