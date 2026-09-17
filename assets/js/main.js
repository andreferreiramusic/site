// André Ferreira site — language toggle + menu + video player.
// Two translation styles live side by side: data-i18n="key" pulls from the
// dictionaries below, while data-pt/en/de carry a row's own wording inline —
// used by the concert rows, which scripts/build_concerts.py generates from the
// Google Sheet and so can't have dictionary keys known ahead of time.
(function(){
  var i18n = {
    pt: { 'nav.bio':'Biografia','nav.concerts':'Concertos','nav.video':'Vídeo','nav.teaching':'Ensino','nav.contact':'Contacto',
      'hero.eyebrow':'Guitarra Clássica & Alaúde · Viena','hero.cta':'Próximos concertos ↓',
      'bio.body':
        '<p>André Ferreira é um guitarrista e alaudista português radicado em Viena. Músico versátil, com uma sólida formação tanto na performance histórica como na moderna, o seu tocar reflete um envolvimento profundo com as possibilidades expressivas das cordas dedilhadas.</p>' +
        '<p>Atua regularmente como solista, músico de câmara e instrumentista de orquestra, colaborando com agrupamentos como o Concentus Musicus Wien e o Bach Consort Wien. As suas atuações levaram-no a importantes salas e festivais por toda a Europa, incluindo o Wiener Musikverein, o Wiener Konzerthaus, o Palau de la Música Catalana, o Auditorio Nacional de Madrid, a Kölner Philharmonie e o Brucknerhaus Linz.</p>' +
        '<p>A formação musical de André abrange as tradições europeias da guitarra e dos instrumentos antigos de corda dedilhada. Estudou com Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén e David Bergmüller, tendo concluído mestrados em Guitarra e em Alaúde, bem como uma licenciatura em Pedagogia Musical.</p>' +
        '<p>Desde 2023, integra o corpo docente da Universidade de Música e Artes Cénicas de Viena, onde leciona ambos os instrumentos.</p>',
      'bio.link':'Sobre André →','concerts.h':'Próximos Concertos',
      'concerts.tickets':'Bilhetes →','concerts.none':'Sem concertos anunciados de momento.',
      'video.play':'Reproduzir vídeo','video.link':'Ver no YouTube →',
      'teaching.body':'André leciona instrumentos históricos de alaúde no Departamento de Música Antiga da mdw — Universidade de Música e Artes Cénicas de Viena, e dá masterclasses por toda a Europa.',
      'foot.text':'Reservas e contacto' },
    en: { 'nav.bio':'Bio','nav.concerts':'Concerts','nav.video':'Video','nav.teaching':'Teaching','nav.contact':'Contact',
      'hero.eyebrow':'Classical Guitar & Lute · Vienna','hero.cta':'Upcoming concerts ↓',
      'bio.body':
        '<p>André Ferreira is a Portuguese guitarist and lutenist based in Vienna. A versatile musician with a strong foundation in both historical and modern performance, his playing reflects a deep engagement with the expressive possibilities of plucked strings.</p>' +
        '<p>He appears regularly as a soloist, chamber musician, and orchestral player, collaborating with ensembles such as Concentus Musicus Wien and Bach Consort Wien. His performances have taken him to major venues and festivals across Europe, including the Wiener Musikverein, Wiener Konzerthaus, Palau de la Música Catalana, Auditorio Nacional de Madrid, Kölner Philharmonie, and Brucknerhaus Linz.</p>' +
        '<p>André’s musical formation spans the European traditions of both the guitar and early plucked instruments. He studied with Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén, and David Bergmüller, earning master’s degrees in Guitar and Lute Performance, as well as a bachelor’s degree in Music Pedagogy.</p>' +
        '<p>Since 2023, he has been a member of the faculty at the University of Music and Performing Arts Vienna, where he teaches both instruments.</p>',
      'bio.link':'About André →','concerts.h':'Upcoming Concerts',
      'concerts.tickets':'Tickets →','concerts.none':'No concerts announced at the moment.',
      'video.play':'Play video','video.link':'Watch on YouTube →',
      'teaching.body':'André teaches historical lute instruments at the Early Music Department of mdw — University of Music and Performing Arts Vienna, and gives masterclasses across Europe.',
      'foot.text':'Booking & contact' },
    de: { 'nav.bio':'Biografie','nav.concerts':'Konzerte','nav.video':'Video','nav.teaching':'Lehre','nav.contact':'Kontakt',
      'hero.eyebrow':'Klassische Gitarre & Laute · Wien','hero.cta':'Kommende Konzerte ↓',
      'bio.body':
        '<p>André Ferreira ist ein portugiesischer Gitarrist und Lautenist mit Sitz in Wien. Als vielseitiger Musiker mit einem soliden Fundament in historischer wie moderner Aufführungspraxis zeugt sein Spiel von einer tiefen Auseinandersetzung mit den Ausdrucksmöglichkeiten der Zupfinstrumente.</p>' +
        '<p>Er tritt regelmäßig als Solist, Kammermusiker und Orchestermusiker auf und arbeitet mit Ensembles wie dem Concentus Musicus Wien und dem Bach Consort Wien zusammen. Seine Auftritte führten ihn in bedeutende Säle und zu Festivals in ganz Europa, darunter der Wiener Musikverein, das Wiener Konzerthaus, der Palau de la Música Catalana, das Auditorio Nacional de Madrid, die Kölner Philharmonie und das Brucknerhaus Linz.</p>' +
        '<p>Andrés musikalische Ausbildung umspannt die europäischen Traditionen sowohl der Gitarre als auch der historischen Zupfinstrumente. Er studierte bei Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén und David Bergmüller und schloss Masterstudien in Gitarre und Laute sowie ein Bachelorstudium in Musikpädagogik ab.</p>' +
        '<p>Seit 2023 gehört er dem Lehrkörper der Universität für Musik und darstellende Kunst Wien an, wo er beide Instrumente unterrichtet.</p>',
      'bio.link':'Über André →','concerts.h':'Kommende Konzerte',
      'concerts.tickets':'Tickets →','concerts.none':'Zurzeit keine Konzerte angekündigt.',
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
