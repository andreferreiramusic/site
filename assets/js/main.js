// André Ferreira site — language toggle + menu + video player.
// Two translation styles live side by side: data-i18n="key" pulls from the
// dictionaries below, while data-pt/en/de carry a row's own wording inline —
// used by the concert rows, which scripts/build_concerts.py generates from the
// Google Sheet and so can't have dictionary keys known ahead of time.
(function(){
  var i18n = {
    pt: { 'nav.bio':'Biografia','nav.concerts':'Concertos','nav.video':'Vídeo','nav.teaching':'Ensino','nav.contact':'Contacto',
      'hero.eyebrow':'Guitarra Clássica & Alaúde · Viena','hero.cta':'Próximos concertos ↓',
      'bio.body':'André Ferreira é um guitarrista e alaudista português radicado em Viena. Natural de Leiria, iniciou os estudos de guitarra aos doze anos e formou-se com distinção no Conservatorio Superior de Música de Vigo, prosseguindo estudos avançados em Darmstadt, Graz, Weimar e Colónia. O seu percurso foi reconhecido com prémios nos concursos internacionais José Tomás, Ciutat d\'Elx e Leiria. Atua por toda a Europa como solista e com formações como o Bach Consort Wien e o Concentus Musicus Wien, tendo editado o álbum de estreia "Sonatas" em 2018.',
      'bio.link':'Sobre André →','concerts.h':'Próximos Concertos',
      'concerts.tickets':'Bilhetes →',
      'video.play':'Reproduzir vídeo','video.link':'Ver no YouTube →',
      'teaching.body':'André leciona instrumentos históricos de alaúde no Departamento de Música Antiga da mdw — Universidade de Música e Artes Cénicas de Viena, e dá masterclasses por toda a Europa.',
      'foot.text':'Reservas e contacto' },
    en: { 'nav.bio':'Bio','nav.concerts':'Concerts','nav.video':'Video','nav.teaching':'Teaching','nav.contact':'Contact',
      'hero.eyebrow':'Classical Guitar & Lute · Vienna','hero.cta':'Upcoming concerts ↓',
      'bio.body':'André Ferreira is a Portuguese classical guitarist and lutenist based in Vienna. Born in Leiria, he began guitar studies at twelve and graduated with highest honours from the Conservatorio Superior de Música de Vigo, going on to advanced studies in Darmstadt, Graz, Weimar and Cologne. His playing has been recognised with prizes at the José Tomás, Ciutat d\'Elx and Leiria international competitions. He performs across Europe as a soloist and with ensembles including Bach Consort Wien and Concentus Musicus Wien, and released his debut album, "Sonatas," in 2018.',
      'bio.link':'About André →','concerts.h':'Upcoming Concerts',
      'concerts.tickets':'Tickets →',
      'video.play':'Play video','video.link':'Watch on YouTube →',
      'teaching.body':'André teaches historical lute instruments at the Early Music Department of mdw — University of Music and Performing Arts Vienna, and gives masterclasses across Europe.',
      'foot.text':'Booking & contact' },
    de: { 'nav.bio':'Biografie','nav.concerts':'Konzerte','nav.video':'Video','nav.teaching':'Lehre','nav.contact':'Kontakt',
      'hero.eyebrow':'Klassische Gitarre & Laute · Wien','hero.cta':'Kommende Konzerte ↓',
      'bio.body':'André Ferreira ist ein portugiesischer Gitarrist und Lautenist mit Sitz in Wien. Geboren in Leiria, begann er im Alter von zwölf Jahren mit dem Gitarrenspiel und schloss sein Studium mit Auszeichnung am Conservatorio Superior de Música de Vigo ab, gefolgt von weiterführenden Studien in Darmstadt, Graz, Weimar und Köln. Seine Arbeit wurde mit Preisen bei den internationalen Wettbewerben José Tomás, Ciutat d\'Elx und Leiria ausgezeichnet. Er tritt in ganz Europa als Solist sowie mit Ensembles wie dem Bach Consort Wien und dem Concentus Musicus Wien auf und veröffentlichte 2018 sein Debütalbum "Sonatas".',
      'bio.link':'Über André →','concerts.h':'Kommende Konzerte',
      'concerts.tickets':'Tickets →',
      'video.play':'Video abspielen','video.link':'Auf YouTube ansehen →',
      'teaching.body':'André unterrichtet historische Lauteninstrumente am Institut für Alte Musik der mdw — Universität für Musik und darstellende Kunst Wien, und gibt Meisterkurse in ganz Europa.',
      'foot.text':'Buchung & Kontakt' }
  };

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

  function setLang(lang){
    currentLang = lang;
    document.documentElement.setAttribute('lang', lang);
    applyLang(lang);
    document.querySelectorAll('.langs button').forEach(function(b){
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true':'false');
    });
  }

  document.querySelectorAll('.langs button').forEach(function(b){
    b.addEventListener('click', function(){ setLang(b.getAttribute('data-lang')); });
  });

  var burger = document.getElementById('burgerBtn'), menu = document.getElementById('menu');
  if(burger){
    burger.addEventListener('click', function(){
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true':'false');
    });
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

  setLang('pt');
})();
