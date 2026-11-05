/* Naqaa blog listing: preview-only card style switcher (?card=1|2|3) */
(function () {
  var grid = document.querySelector('.blog-grid');
  if (!grid) return;
  var q = new URLSearchParams(location.search).get('card');
  if (!/^[123]$/.test(q || '')) return;
  grid.setAttribute('data-card', q);
  var names = { 1: '1 · كلاسيك', 2: '2 · أفقي', 3: '3 · صورة كاملة' };
  var bar = document.createElement('div');
  bar.className = 'nq-card-switch';
  bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'اختيار شكل الكارت');
  var inner = document.createElement('div');
  [1, 2, 3].forEach(function (n) {
    var a = document.createElement('a');
    a.href = '?card=' + n;
    a.textContent = names[n];
    if (String(n) === q) a.className = 'on';
    inner.appendChild(a);
  });
  bar.appendChild(inner);
  var paper = document.querySelector('.blog-paper');
  if (paper) paper.insertBefore(bar, paper.firstChild);
})();
