/* Preview only: switch the blog hero style with ?hero=1|2|3 */
(function () {
  var hero = document.querySelector('.bh');
  if (!hero) return;
  var q = new URLSearchParams(location.search).get('hero');
  if (!/^[123]$/.test(q || '')) return;
  hero.setAttribute('data-hero', q);
  if (q === '2' && !hero.querySelector('.bh-bg')) {
    var bg = document.createElement('div'); bg.className = 'bh-bg';
    bg.innerHTML = '<img src="/about/naqaa-cleaning-riyadh.webp" alt="">';
    hero.insertBefore(bg, hero.firstChild);
  }
  var names = { 1: '1 · مقالة مميزة', 2: '2 · صورة خلفية', 3: '3 · مدمج' };
  var bar = document.createElement('div'); bar.className = 'nq-hero-switch';
  bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'اختيار شكل الهيرو');
  [1, 2, 3].forEach(function (n) {
    var a = document.createElement('a'); a.href = '?hero=' + n; a.textContent = names[n];
    if (String(n) === q) a.className = 'on'; bar.appendChild(a);
  });
  document.body.appendChild(bar);
})();
