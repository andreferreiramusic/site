// André Ferreira site — language toggle + menu.
// Runs again after htmx swaps in partials/concerts.html so the newly loaded
// rows pick up the current language too.
(function(){
  var i18n = {
    pt: { 'nav.bio':'Biografia','nav.concerts':'Concertos','nav.video':'Vídeo','nav.teaching':'Ensino','nav.contact':'Contacto',
      'hero.eyebrow':'Guitarra Clássica & Alaúde · Viena','hero.cta':'Próximos concertos ↓',
      'bio.body':'André Ferreira é um guitarrista e alaudista português radicado em Viena. Natural de Leiria, iniciou os estudos de guitarra aos doze anos e formou-se com distinção no Conservatorio Superior de Música de Vigo, prosseguindo estudos avançados em Darmstadt, Graz, Weimar e Colónia. O seu percurso foi reconhecido com prémios nos concursos internacionais José Tomás, Ciutat d\'Elx e Leiria. Atua por toda a Europa como solista e com formações como o Bach Consort Wien e o Concentus Musicus Wien, tendo editado o álbum de estreia "Sonatas" em 2018.',
      'bio.link':'Sobre André →','concerts.h':'Próximos Concertos',
      'concerts.note':'Esta lista vem de partials/concerts.html — edita esse ficheiro para atualizar datas (ou liga-o a uma Google Sheet mais tarde).',
      'concerts.tickets':'Bilhetes →','concerts.solo1':'Recital a solo','concerts.solo2':'Recital a solo',
      'video.note':'Espaço reservado — ligar a uma atuação real no YouTube.',
      'video.title':'Título da atuação','video.link':'Ver no YouTube →',
      'teaching.body':'André leciona instrumentos históricos de alaúde no Departamento de Música Antiga da mdw — Universidade de Música e Artes Cénicas de Viena, e dá masterclasses por toda a Europa.',
      'foot.text':'Reservas e contacto' },
    en: { 'nav.bio':'Bio','nav.concerts':'Concerts','nav.video':'Video','nav.teaching':'Teaching','nav.contact':'Contact',
      'hero.eyebrow':'Classical Guitar & Lute · Vienna','hero.cta':'Upcoming concerts ↓',
      'bio.body':'André Ferreira is a Portuguese classical guitarist and lutenist based in Vienna. Born in Leiria, he began guitar studies at twelve and graduated with highest honours from the Conservatorio Superior de Música de Vigo, going on to advanced studies in Darmstadt, Graz, Weimar and Cologne. His playing has been recognised with prizes at the José Tomás, Ciutat d\'Elx and Leiria international competitions. He performs across Europe as a soloist and with ensembles including Bach Consort Wien and Concentus Musicus Wien, and released his debut album, "Sonatas," in 2018.',
      'bio.link':'About André →','concerts.h':'Upcoming Concerts',
      'concerts.note':'This list comes from partials/concerts.html — edit that file to update dates (or wire it to a Google Sheet later).',
      'concerts.tickets':'Tickets →','concerts.solo1':'Solo recital','concerts.solo2':'Solo recital',
      'video.note':'Placeholder — link to a real performance on YouTube.',
      'video.title':'Performance title','video.link':'Watch on YouTube →',
      'teaching.body':'André teaches historical lute instruments at the Early Music Department of mdw — University of Music and Performing Arts Vienna, and gives masterclasses across Europe.',
      'foot.text':'Booking & contact' },
    de: { 'nav.bio':'Biografie','nav.concerts':'Konzerte','nav.video':'Video','nav.teaching':'Lehre','nav.contact':'Kontakt',
      'hero.eyebrow':'Klassische Gitarre & Laute · Wien','hero.cta':'Kommende Konzerte ↓',
      'bio.body':'André Ferreira ist ein portugiesischer Gitarrist und Lautenist mit Sitz in Wien. Geboren in Leiria, begann er im Alter von zwölf Jahren mit dem Gitarrenspiel und schloss sein Studium mit Auszeichnung am Conservatorio Superior de Música de Vigo ab, gefolgt von weiterführenden Studien in Darmstadt, Graz, Weimar und Köln. Seine Arbeit wurde mit Preisen bei den internationalen Wettbewerben José Tomás, Ciutat d\'Elx und Leiria ausgezeichnet. Er tritt in ganz Europa als Solist sowie mit Ensembles wie dem Bach Consort Wien und dem Concentus Musicus Wien auf und veröffentlichte 2018 sein Debütalbum "Sonatas".',
      'bio.link':'Über André →','concerts.h':'Kommende Konzerte',
      'concerts.note':'Diese Liste stammt aus partials/concerts.html — bearbeite diese Datei, um Termine zu aktualisieren (oder verbinde sie später mit einer Google-Tabelle).',
      'concerts.tickets':'Tickets →','concerts.solo1':'Solorezital','concerts.solo2':'Solorezital',
      'video.note':'Platzhalter — mit einem echten Auftritt auf YouTube verlinken.',
      'video.title':'Titel des Auftritts','video.link':'Auf YouTube ansehen →',
      'teaching.body':'André unterrichtet historische Lauteninstrumente am Institut für Alte Musik der mdw — Universität für Musik und darstellende Kunst Wien, und gibt Meisterkurse in ganz Europa.',
      'foot.text':'Buchung & Kontakt' }
  };

  var currentLang = 'pt';

  function applyLang(lang, root){
    (root || document).querySelectorAll('[data-i18n]').forEach(function(el){
      var key = el.getAttribute('data-i18n');
      if(i18n[lang] && i18n[lang][key]) el.innerHTML = i18n[lang][key];
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

  // Re-translate content htmx just swapped in (e.g. the concerts partial).
  document.body.addEventListener('htmx:afterSwap', function(evt){
    applyLang(currentLang, evt.target);
  });

  setLang('pt');
})();
