/* Naqaa shared UI behaviour: header menu, active link, progress bar, floating bar, footer credit. */
(function(){
  var d = document, b = d.body;
  var burger = d.getElementById('nq-burger'), fbar = d.getElementById('nq-fbar'), prog = d.getElementById('nq-progress');

  function menu(open){
    b.classList.toggle('nq-open', open);
    if(burger) burger.setAttribute('aria-expanded', open);
  }
  if(burger){
    burger.addEventListener('click', function(e){ e.stopPropagation(); menu(!b.classList.contains('nq-open')); });
    d.addEventListener('click', function(e){
      if(b.classList.contains('nq-open') && !e.target.closest('#nq-menu') && !e.target.closest('#nq-burger')) menu(false);
    });
    d.addEventListener('keydown', function(e){ if(e.key === 'Escape') menu(false); });
  }

  /* highlight the section the visitor is in */
  var path = decodeURIComponent(location.pathname);
  Array.prototype.forEach.call(d.querySelectorAll('.nq-nav a, #nq-menu a'), function(a){
    var h = a.getAttribute('href') || '';
    if(h.length > 1 && h.charAt(0) === '/' && path.indexOf(decodeURIComponent(h)) === 0) a.classList.add('on');
  });

  var ticking = false;
  function onScroll(){
    var y = window.scrollY, h = d.documentElement.scrollHeight - window.innerHeight;
    if(prog) prog.style.transform = 'scaleX(' + (h > 0 ? y / h : 0) + ')';
    if(fbar) fbar.classList.toggle('show', y > 300);
    ticking = false;
  }
  window.addEventListener('scroll', function(){ if(!ticking){ ticking = true; requestAnimationFrame(onScroll); } }, {passive:true});
  onScroll();

  var yr = d.getElementById('nq-yr');
  if(yr) yr.textContent = new Date().getFullYear();

  var credit = d.getElementById('nq-credit'), pop = d.getElementById('nq-credit-pop');
  if(credit && pop){
    credit.addEventListener('click', function(e){ e.stopPropagation(); pop.classList.toggle('show'); });
    d.addEventListener('click', function(){ pop.classList.remove('show'); });
  }
})();
