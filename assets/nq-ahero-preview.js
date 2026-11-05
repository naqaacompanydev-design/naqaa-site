/* Preview only: switch the article hero style with ?ahero=1|2|3 */
(function () {
  var q = new URLSearchParams(location.search).get('ahero');
  if (!/^[123]$/.test(q || '')) return;
  document.body.setAttribute('data-ahero', q);
  var names = { 1: '1 · صورة خلفية', 2: '2 · بسيط في النص', 3: '3 · مقسوم' };
  var bar = document.createElement('div'); bar.className = 'nq-ahero-switch';
  bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'اختيار شكل هيرو المقال');
  [1, 2, 3].forEach(function (n) {
    var a = document.createElement('a'); a.href = '?ahero=' + n; a.textContent = names[n];
    if (String(n) === q) a.className = 'on'; bar.appendChild(a);
  });
  document.body.appendChild(bar);
})();
