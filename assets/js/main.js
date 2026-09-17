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
      'hero.eyebrow':'Guitarra Clássica & Alaúde · Viena','hero.cta':'Próximos concertos →',
      'home.more':'Ver mais →',
      'home.about':'André Ferreira é um guitarrista e alaudista português radicado em Viena, atuando por toda a Europa como solista, músico de câmara e instrumentista de orquestra.',
      'home.guitar':'Repertório, instrumentos e projetos em torno da guitarra clássica.',
      'home.lute':'Alaúde, teorba e instrumentos históricos de corda dedilhada.',
      'home.contact':'Reservas, masterclasses e pedidos de imprensa.',
      'home.dates.h':'Próximos Concertos','home.dates.all':'Todas as datas →',
      'bio.body':
        '<p>André Ferreira é um guitarrista e alaudista português radicado em Viena. Músico versátil, com uma sólida formação tanto na performance histórica como na moderna, o seu tocar reflete um envolvimento profundo com as possibilidades expressivas das cordas dedilhadas.</p>' +
        '<p>Atua regularmente como solista, músico de câmara e instrumentista de orquestra, colaborando com agrupamentos como o Concentus Musicus Wien e o Bach Consort Wien. As suas atuações levaram-no a importantes salas e festivais por toda a Europa, incluindo o Wiener Musikverein, o Wiener Konzerthaus, o Palau de la Música Catalana, o Auditorio Nacional de Madrid, a Kölner Philharmonie e o Brucknerhaus Linz.</p>' +
        '<p>A formação musical de André abrange as tradições europeias da guitarra e dos instrumentos antigos de corda dedilhada. Estudou com Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén e David Bergmüller, tendo concluído mestrados em Guitarra e em Alaúde, bem como uma licenciatura em Pedagogia Musical.</p>' +
        '<p>Desde 2023, integra o corpo docente da Universidade de Música e Artes Cénicas de Viena, onde leciona ambos os instrumentos.</p>',
      'about.teaching.h':'Ensino',
      'teaching.body':'André leciona instrumentos históricos de alaúde no Departamento de Música Antiga da mdw — Universidade de Música e Artes Cénicas de Viena, e dá masterclasses por toda a Europa.',
      'guitar.body':'<p><em>[Por preencher]</em> Esta página vai reunir o trabalho de André com a guitarra clássica: repertório, instrumentos, gravações e projetos de câmara.</p>',
      'lute.body':'<p><em>[Por preencher]</em> Esta página vai reunir o trabalho de André com o alaúde, a teorba e outros instrumentos históricos de corda dedilhada.</p>',
      'dates.upcoming':'Próximos Concertos','dates.past':'Arquivo',
      'dates.past.none':'Ainda sem atuações em arquivo.',
      'concerts.tickets':'Bilhetes →','concerts.none':'Sem concertos anunciados de momento.',
      'contact.body':'<p>Para reservas de concertos, masterclasses e pedidos de imprensa, escreva por email — as mensagens são respondidas em português, inglês ou alemão.</p>',
      'contact.email':'Email','contact.youtube':'YouTube','contact.based':'Base','contact.city':'Viena, Áustria',
      'video.play':'Reproduzir vídeo','video.link':'Ver no YouTube →',
      'foot.text':'Reservas e contacto'
    },
    en: {
      'nav.home':'Home','nav.about':'About','nav.guitar':'Guitar','nav.lute':'Lute',
      'nav.dates':'Dates','nav.contact':'Contact','nav.video':'Video',
      'hero.eyebrow':'Classical Guitar & Lute · Vienna','hero.cta':'Upcoming concerts →',
      'home.more':'Read more →',
      'home.about':'André Ferreira is a Portuguese guitarist and lutenist based in Vienna, performing across Europe as a soloist, chamber musician and orchestral player.',
      'home.guitar':'Repertoire, instruments and projects on the classical guitar.',
      'home.lute':'Lute, theorbo and historical plucked string instruments.',
      'home.contact':'Booking, masterclasses and press enquiries.',
      'home.dates.h':'Upcoming Concerts','home.dates.all':'All dates →',
      'bio.body':
        '<p>André Ferreira is a Portuguese guitarist and lutenist based in Vienna. A versatile musician with a strong foundation in both historical and modern performance, his playing reflects a deep engagement with the expressive possibilities of plucked strings.</p>' +
        '<p>He appears regularly as a soloist, chamber musician, and orchestral player, collaborating with ensembles such as Concentus Musicus Wien and Bach Consort Wien. His performances have taken him to major venues and festivals across Europe, including the Wiener Musikverein, Wiener Konzerthaus, Palau de la Música Catalana, Auditorio Nacional de Madrid, Kölner Philharmonie, and Brucknerhaus Linz.</p>' +
        '<p>André’s musical formation spans the European traditions of both the guitar and early plucked instruments. He studied with Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén, and David Bergmüller, earning master’s degrees in Guitar and Lute Performance, as well as a bachelor’s degree in Music Pedagogy.</p>' +
        '<p>Since 2023, he has been a member of the faculty at the University of Music and Performing Arts Vienna, where he teaches both instruments.</p>',
      'about.teaching.h':'Teaching',
      'teaching.body':'André teaches historical lute instruments at the Early Music Department of mdw — University of Music and Performing Arts Vienna, and gives masterclasses across Europe.',
      'guitar.body':'<p><em>[To be written]</em> This page will gather André’s work on the classical guitar: repertoire, instruments, recordings and chamber projects.</p>',
      'lute.body':'<p><em>[To be written]</em> This page will gather André’s work on the lute, theorbo and other historical plucked string instruments.</p>',
      'dates.upcoming':'Upcoming Concerts','dates.past':'Archive',
      'dates.past.none':'No past performances listed yet.',
      'concerts.tickets':'Tickets →','concerts.none':'No concerts announced at the moment.',
      'contact.body':'<p>For concert bookings, masterclasses and press enquiries, please write by email — messages are answered in Portuguese, English or German.</p>',
      'contact.email':'Email','contact.youtube':'YouTube','contact.based':'Based in','contact.city':'Vienna, Austria',
      'video.play':'Play video','video.link':'Watch on YouTube →',
      'foot.text':'Booking & contact'
    },
    de: {
      'nav.home':'Start','nav.about':'Über','nav.guitar':'Gitarre','nav.lute':'Laute',
      'nav.dates':'Termine','nav.contact':'Kontakt','nav.video':'Video',
      'hero.eyebrow':'Klassische Gitarre & Laute · Wien','hero.cta':'Kommende Konzerte →',
      'home.more':'Mehr lesen →',
      'home.about':'André Ferreira ist ein portugiesischer Gitarrist und Lautenist mit Sitz in Wien und tritt in ganz Europa als Solist, Kammermusiker und Orchestermusiker auf.',
      'home.guitar':'Repertoire, Instrumente und Projekte rund um die klassische Gitarre.',
      'home.lute':'Laute, Theorbe und historische Zupfinstrumente.',
      'home.contact':'Buchung, Meisterkurse und Presseanfragen.',
      'home.dates.h':'Kommende Konzerte','home.dates.all':'Alle Termine →',
      'bio.body':
        '<p>André Ferreira ist ein portugiesischer Gitarrist und Lautenist mit Sitz in Wien. Als vielseitiger Musiker mit einem soliden Fundament in historischer wie moderner Aufführungspraxis zeugt sein Spiel von einer tiefen Auseinandersetzung mit den Ausdrucksmöglichkeiten der Zupfinstrumente.</p>' +
        '<p>Er tritt regelmäßig als Solist, Kammermusiker und Orchestermusiker auf und arbeitet mit Ensembles wie dem Concentus Musicus Wien und dem Bach Consort Wien zusammen. Seine Auftritte führten ihn in bedeutende Säle und zu Festivals in ganz Europa, darunter der Wiener Musikverein, das Wiener Konzerthaus, der Palau de la Música Catalana, das Auditorio Nacional de Madrid, die Kölner Philharmonie und das Brucknerhaus Linz.</p>' +
        '<p>Andrés musikalische Ausbildung umspannt die europäischen Traditionen sowohl der Gitarre als auch der historischen Zupfinstrumente. Er studierte bei Margarita Escarpa, Tilman Hoppstock, Paolo Pegoraro, Ricardo Gallén und David Bergmüller und schloss Masterstudien in Gitarre und Laute sowie ein Bachelorstudium in Musikpädagogik ab.</p>' +
        '<p>Seit 2023 gehört er dem Lehrkörper der Universität für Musik und darstellende Kunst Wien an, wo er beide Instrumente unterrichtet.</p>',
      'about.teaching.h':'Lehre',
      'teaching.body':'André unterrichtet historische Lauteninstrumente am Institut für Alte Musik der mdw — Universität für Musik und darstellende Kunst Wien, und gibt Meisterkurse in ganz Europa.',
      'guitar.body':'<p><em>[Noch zu schreiben]</em> Diese Seite wird Andrés Arbeit an der klassischen Gitarre versammeln: Repertoire, Instrumente, Aufnahmen und Kammermusikprojekte.</p>',
      'lute.body':'<p><em>[Noch zu schreiben]</em> Diese Seite wird Andrés Arbeit an Laute, Theorbe und weiteren historischen Zupfinstrumenten versammeln.</p>',
      'dates.upcoming':'Kommende Konzerte','dates.past':'Archiv',
      'dates.past.none':'Noch keine vergangenen Auftritte gelistet.',
      'concerts.tickets':'Tickets →','concerts.none':'Zurzeit keine Konzerte angekündigt.',
      'contact.body':'<p>Für Konzertbuchungen, Meisterkurse und Presseanfragen bitte per E-Mail schreiben — Nachrichten werden auf Portugiesisch, Englisch oder Deutsch beantwortet.</p>',
      'contact.email':'E-Mail','contact.youtube':'YouTube','contact.based':'Basis','contact.city':'Wien, Österreich',
      'video.play':'Video abspielen','video.link':'Auf YouTube ansehen →',
      'foot.text':'Buchung & Kontakt'
    }
  };

  // The site is six pages now, so the choice has to outlive a page load or
  // every nav click would snap back to Portuguese. Wrapped because storage
  // throws outright in some privacy modes.
  var STORE = 'af-lang';
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
    burger.addEventListener('click', function(){
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true':'false');
    });
    // Widening past the breakpoint flattens the menu into the bar via CSS, but
    // .open would linger and leave it unexpectedly open on the way back down.
    var wide = window.matchMedia('(min-width:900px)');
    var reset = function(e){
      if(e.matches){
        menu.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      }
    };
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

  var stored = readStored();
  setLang(stored && i18n[stored] ? stored : 'pt', false);
})();
