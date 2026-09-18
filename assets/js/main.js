// André Ferreira site — language toggle + menu + video player.
// Loaded by every page; each block guards for elements that page may not have.
//
// Two translation styles live side by side: data-i18n="key" pulls from the
// dictionaries below, while data-pt/en/de carry a row's own wording inline —
// used by the concert rows, which scripts/events.py generates from
// data/events.csv and so can't have dictionary keys known ahead of time.
(function(){
  var i18n = {
    pt: {
      'nav.home':'Início','nav.about':'Sobre','nav.guitar':'Guitarra','nav.lute':'Alaúde',
      'nav.dates':'Datas','nav.contact':'Contacto','nav.video':'Vídeo',
      'hero.eyebrow':'Guitarrista & Alaudista · Viena','hero.cta':'Próximos concertos ↓',
      'home.about.d':'Biografia, formação e as salas e festivais onde tem atuado.',
      'home.guitar.d':'Repertório, instrumentos e projetos em torno da guitarra clássica.',
      'home.lute.d':'Alaúde, teorba e outros instrumentos históricos de corda dedilhada.',
      'home.dates.h':'Próximos','home.dates.all':'Todas as datas →',
      'about.teaching.h':'Ensino',
      'teaching.link':'Perfil na mdw →',
      'dates.upcoming':'Próximos','dates.past':'Anteriores',
      'dates.past.none':'Ainda sem eventos anteriores.',
      'concerts.tickets':'Bilhetes →','concerts.none':'Sem concertos anunciados de momento.',
      'contact.email':'Email','contact.youtube':'YouTube','contact.based':'Base','contact.city':'Viena, Áustria',
      'video.play':'Reproduzir vídeo','video.link':'Ver no YouTube →'
    },
    en: {
      'nav.home':'Home','nav.about':'About','nav.guitar':'Guitar','nav.lute':'Lute',
      'nav.dates':'Dates','nav.contact':'Contact','nav.video':'Video',
      'hero.eyebrow':'Guitarist & Lutenist · Vienna','hero.cta':'Upcoming concerts ↓',
      'home.about.d':'Biography, training, and the halls and festivals he has played.',
      'home.guitar.d':'Repertoire, instruments and projects on the classical guitar.',
      'home.lute.d':'Lute, theorbo and other historical plucked string instruments.',
      'home.dates.h':'Upcoming','home.dates.all':'All dates →',
      'about.teaching.h':'Teaching',
      'teaching.link':'Faculty profile at mdw →',
      'dates.upcoming':'Upcoming','dates.past':'Past',
      'dates.past.none':'No past events listed yet.',
      'concerts.tickets':'Tickets →','concerts.none':'No concerts announced at the moment.',
      'contact.email':'Email','contact.youtube':'YouTube','contact.based':'Based in','contact.city':'Vienna, Austria',
      'video.play':'Play video','video.link':'Watch on YouTube →'
    },
    de: {
      'nav.home':'Start','nav.about':'Über','nav.guitar':'Gitarre','nav.lute':'Laute',
      'nav.dates':'Termine','nav.contact':'Kontakt','nav.video':'Video',
      'hero.eyebrow':'Gitarrist & Lautenist · Wien','hero.cta':'Kommende Konzerte ↓',
      'home.about.d':'Biografie, Ausbildung und die Säle und Festivals, in denen er gespielt hat.',
      'home.guitar.d':'Repertoire, Instrumente und Projekte rund um die klassische Gitarre.',
      'home.lute.d':'Laute, Theorbe und weitere historische Zupfinstrumente.',
      'home.dates.h':'Kommende','home.dates.all':'Alle Termine →',
      'about.teaching.h':'Lehre',
      'teaching.link':'Profil an der mdw →',
      'dates.upcoming':'Kommende','dates.past':'Vergangene',
      'dates.past.none':'Noch keine vergangenen Veranstaltungen gelistet.',
      'concerts.tickets':'Tickets →','concerts.none':'Zurzeit keine Konzerte angekündigt.',
      'contact.email':'E-Mail','contact.youtube':'YouTube','contact.based':'Basis','contact.city':'Wien, Österreich',
      'video.play':'Video abspielen','video.link':'Auf YouTube ansehen →'
    }
  };

  // Prose lives in content/<lang>/*.md and is compiled into content.js by
  // scripts/build.py; merge it over the UI strings above.
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
