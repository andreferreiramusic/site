// André Ferreira site — language toggle + menu + video player.
// Loaded by every page; each block guards for elements that page may not have.
//
// Two translation styles live side by side: data-i18n="key" pulls from the
// dictionary compiled out of content/, while data-pt/en/de carry a row's own
// wording inline — used by the concert rows, which scripts/events.py
// generates from data/events.csv and so can't have keys known ahead of time.
(function(){
  // Every translated word lives in content/<page>/<block>_<lang>.md and is
  // compiled into content.js by scripts/build.py, which loads first. Nothing
  // is spelled out in here: a text is edited in Markdown, the build is run,
  // and both the copy baked into the HTML and this dictionary follow.
  var i18n = {};

  // content.js is generated from content/ and holds every language the site
  // has; which languages exist is whatever it carries.
  if(window.__content){
    for(var lang in window.__content){
      if(!i18n[lang]) i18n[lang] = {};
      for(var key in window.__content[lang]) i18n[lang][key] = window.__content[lang][key];
    }
  }

  // The site is six pages now, so the choice has to outlive a page load or
  // every nav click would snap back to Portuguese. Wrapped because storage
  // throws outright in some privacy modes.
  var STORE = 'af-lang';
  // Shown to visitors whose browser asks for none of pt/en/de — French,
  // Spanish, Italian and so on. Change this one value to prefer Portuguese.
  var FALLBACK = 'en';
  function readStored(){
    try { return localStorage.getItem(STORE); } catch(e){ return null; }
  }
  function writeStored(lang){
    try { localStorage.setItem(STORE, lang); } catch(e){ /* nothing to do */ }
  }

  var currentLang = 'pt';

  function applyLang(lang, root){
    (root || document).querySelectorAll('[data-i18n]').forEach(function(el){
      var key = el.getAttribute('data-i18n');
      if(i18n[lang] && i18n[lang][key]) el.innerHTML = i18n[lang][key];
    });
    (root || document).querySelectorAll('[data-pt]').forEach(function(el){
      var v = el.getAttribute('data-' + lang);
      if(v) el.textContent = v;
    });
    (root || document).querySelectorAll('[data-i18n-aria]').forEach(function(el){
      var key = el.getAttribute('data-i18n-aria');
      if(i18n[lang] && i18n[lang][key]) el.setAttribute('aria-label', i18n[lang][key]);
    });
  }

  function setLang(lang, remember){
    currentLang = lang;
    document.documentElement.setAttribute('lang', lang);
    applyLang(lang);
    document.querySelectorAll('.langs button').forEach(function(b){
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true':'false');
    });
    if(remember) writeStored(lang);
  }

  document.querySelectorAll('.langs button').forEach(function(b){
    b.addEventListener('click', function(){ setLang(b.getAttribute('data-lang'), true); });
  });

  var burger = document.getElementById('burgerBtn'), menu = document.getElementById('menu');
  if(burger){
    function isOpen(){ return menu.classList.contains('open'); }
    function setOpen(open){
      menu.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open ? 'true':'false');
    }

    burger.addEventListener('click', function(){ setOpen(!isOpen()); });

    // Tapping the page dismisses the menu. Without this the only way out is to
    // find the burger again, which is awkward once the menu covers the corner.
    // The burger itself is excluded so its own click isn't undone here first.
    document.addEventListener('click', function(e){
      if(isOpen() && !menu.contains(e.target) && !burger.contains(e.target)) setOpen(false);
    });

    document.addEventListener('keydown', function(e){
      if(isOpen() && (e.key === 'Escape' || e.key === 'Esc')){
        setOpen(false);
        burger.focus();
      }
    });

    // Widening past the breakpoint flattens the menu into the bar via CSS, but
    // .open would linger and leave it unexpectedly open on the way back down.
    var wide = window.matchMedia('(min-width:768px)');
    var reset = function(e){ if(e.matches) setOpen(false); };
    if(wide.addEventListener) wide.addEventListener('change', reset);
    else if(wide.addListener) wide.addListener(reset);  // older Safari
  }

  // Press play: trade the poster for the real player. Loading the iframe up
  // front would pull ~1MB of YouTube script on every visit, play or not.
  var videoBtn = document.getElementById('videoBtn');
  if(videoBtn){
    var id = videoBtn.getAttribute('data-video-id');
    var poster = videoBtn.querySelector('img');
    // Not every upload has a maxres still; fall back to the size that always exists.
    poster.addEventListener('error', function(){
      poster.src = 'https://i.ytimg.com/vi/' + id + '/hqdefault.jpg';
    });
    videoBtn.addEventListener('click', function(){
      var frame = document.createElement('iframe');
      frame.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
      frame.title = document.querySelector('.video-caption .vt').textContent;
      frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      frame.allowFullscreen = true;
      var wrap = document.createElement('div');
      wrap.className = 'video-player';
      wrap.appendChild(frame);
      videoBtn.replaceWith(wrap);
    });
  }

  // On a first visit, follow the browser's own language preferences. That is
  // the language the visitor asked for, which is not the same as where they
  // are: a Portuguese speaker in Vienna should still get Portuguese. Deciding
  // by country would need a third-party IP lookup on every page load, and
  // would answer the wrong question anyway.
  function preferredLang(){
    var prefs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || ''];
    for(var i = 0; i < prefs.length; i++){
      // "de-AT" and "de" both count as German.
      var base = String(prefs[i]).toLowerCase().split('-')[0];
      if(i18n[base]) return base;
    }
    return FALLBACK;
  }

  // An explicit click always wins over detection, and forever after.
  var stored = readStored();
  setLang(stored && i18n[stored] ? stored : preferredLang(), false);
})();
