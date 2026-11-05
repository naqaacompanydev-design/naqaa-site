/* Naqaa blog article: highlight the current section in the table of contents */
(function () {
  var links = document.querySelectorAll('.art-toc a[href^="#"]');
  if (!links.length || !('IntersectionObserver' in window)) return;
  var byId = {};
  links.forEach(function (a) {
    var id = decodeURIComponent(a.getAttribute('href').slice(1));
    (byId[id] = byId[id] || []).push(a);
    // close the mobile contents box after jumping to a section
    a.addEventListener('click', function () {
      var d = a.closest('details.art-toc-inline');
      if (d) d.open = false;
    });
  });
  var current = null;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      if (current) (byId[current] || []).forEach(function (a) { a.classList.remove('on'); });
      current = e.target.id;
      (byId[current] || []).forEach(function (a) {
        a.classList.add('on');
        var box = a.closest('ol');
        if (box && a.closest('.art-toc-side')) {
          var top = a.offsetTop - box.clientHeight / 2;
          box.scrollTo({ top: top, behavior: 'smooth' });
        }
      });
    });
  }, { rootMargin: '-90px 0px -70% 0px' });
  Object.keys(byId).forEach(function (id) {
    var h = document.getElementById(id);
    if (h) io.observe(h);
  });
})();
