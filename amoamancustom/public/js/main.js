
// FAQ: accordéon simple, un seul ouvert par groupe
(function(){
  document.querySelectorAll('[data-faq]').forEach(function(container){
    var items = Array.from(container.querySelectorAll('.faq-item'));
    function openItem(it){ items.forEach(function(el){ el.classList.toggle('open', el === it); }); }
    items.forEach(function(it){
      var btn = it.querySelector('.faq-btn');
      if (!btn) return;
      btn.addEventListener('click', function(){
        it.classList.contains('open') ? it.classList.remove('open') : openItem(it);
      });
    });
  });
})();


(function () {
    const fill = document.querySelector('[data-ticks-fill]');
    const tags = Array.from(document.querySelectorAll('.time-tag'));
    const timeline = document.querySelector('.timeline');

    // Activer un tag et remplir la barre
    function activateTag(tag) {
        tags.forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        fill.style.width = '100%';
    }

    // Survol de la timeline entière
    timeline.addEventListener('mouseenter', () => {
        fill.style.width = '100%';
        tags.forEach(t => t.classList.add('active'));
    });

    timeline.addEventListener('mouseleave', () => {
        fill.style.width = '0%';
        tags.forEach(t => t.classList.remove('active'));
    });

    // Survol des tags (optionnel, si tu veux un effet individuel)
    tags.forEach(tag => {
        tag.addEventListener('mouseenter', () => {
            activateTag(tag);
        });
        tag.addEventListener('mouseleave', () => {
            fill.style.width = '0%';
            tag.classList.remove('active');
        });
    });
})();






// Smooth scroll pour les liens ancre du menu
(function(){
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click', function(e){
      var id = a.getAttribute('href');
      if (!id || id.length < 2) return;
      var el = document.querySelector(id);
      if (el) {
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();

// Intersection reveal (petite animation d’apparition)
(function(){
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(ent){
      if (ent.isIntersecting) {
        ent.target.classList.add('reveal');
        io.unobserve(ent.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.service-tile, .card-soft, .news-card, .step-card')
    .forEach(function(el){ io.observe(el); });
})();


