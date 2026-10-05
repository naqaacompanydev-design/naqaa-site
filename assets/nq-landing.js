/* Tank landing: animations + dynamic content */
(function(){
  var d = document, w = window;
  w.__tk = 1;
  var reduce = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s){ return d.querySelector(s); }
  function $$(s){ return Array.prototype.slice.call(d.querySelectorAll(s)); }

  /* 1) headline from the ad link: ?tank=ground | roof */
  var types = { ground:'أرضية', ard:'أرضية', roof:'علوية', top:'علوية' };
  var tp = null;
  try { tp = types[(new URLSearchParams(location.search).get('tank') || '').toLowerCase()] || null; } catch(e){}
  if (tp && $('#tk-h1-type')) $('#tk-h1-type').textContent = tp + ' ';

  /* 2) live status by Riyadh time (UTC+3) */
  var live = $('#tk-live');
  if (live) {
    var h = (new Date().getUTCHours() + 3) % 24;
    if (h >= 23 || h < 7) {
      live.classList.add('night');
      live.querySelector('span').textContent = 'ارسل طلبك الحين، ونأكد موعدك أول الصبح';
    } else {
      live.querySelector('span').textContent = (h < 12 ? 'صباح الخير ☀️ ' : 'مساء الخير 🌙 ') + 'فريقنا متاح الحين، ويوصلك غالبًا بنفس اليوم';
    }
  }

  /* 3) typed rotating word */
  var typed = $('#tk-typed');
  var words = ((typed && typed.getAttribute('data-words')) || '').split('|').filter(Boolean);
  if (tp && words.indexOf(tp) > 0) { words.splice(words.indexOf(tp), 1); words.unshift(tp); }
  if (!words.length) typed = null;
  if (typed) {
    if (reduce) typed.textContent = words.join(' • ');
    else (function(){
      var wi = 0, ci = 0, del = false;
      (function tick(){
        var word = words[wi];
        ci += del ? -1 : 1;
        typed.textContent = word.slice(0, ci);
        var t = del ? 45 : 95;
        if (!del && ci === word.length){ del = true; t = 1700; }
        else if (del && ci === 0){ del = false; wi = (wi + 1) % words.length; t = 300; }
        setTimeout(tick, t);
      })();
    })();
  }

  /* 4) ticker: duplicate for a seamless loop + live Riyadh temperature */
  var track = $('#tk-track'), base = track ? track.innerHTML : '';
  function render(extra){ if (track) track.innerHTML = extra + base + extra + base; }
  function addTemp(t){
    if (typeof t !== 'number' || isNaN(t)) return;
    var tail = (track && track.getAttribute('data-temp')) || '';
    render('<span>🌡️ الحرارة في الرياض الحين <b>' + Math.round(t) + '°</b>' + (tail ? '، ' + tail : '') + '</span>');
  }
  render('');
  var cached = null;
  try { cached = JSON.parse(sessionStorage.getItem('tkTemp') || 'null'); } catch(e){}
  if (cached && Date.now() - cached.at < 30 * 60 * 1000) addTemp(cached.t);
  else if (w.fetch) {
    var ctl = w.AbortController ? new AbortController() : null;
    var to = setTimeout(function(){ if (ctl) ctl.abort(); }, 3500);
    fetch('https://api.open-meteo.com/v1/forecast?latitude=24.71&longitude=46.68&current=temperature_2m', ctl ? { signal: ctl.signal } : {})
      .then(function(r){ return r.json(); })
      .then(function(j){
        var t = j && j.current && j.current.temperature_2m;
        addTemp(t);
        try { sessionStorage.setItem('tkTemp', JSON.stringify({ t: t, at: Date.now() })); } catch(e){}
      })
      .catch(function(){})
      .then(function(){ clearTimeout(to); });
  }

  /* 5) reveal on scroll + counters */
  function count(el){
    var end = parseFloat(el.getAttribute('data-count')), dec = +el.getAttribute('data-dec') || 0, t0 = null, dur = 1600;
    if (reduce) return;
    (function step(ts){
      if (!t0) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1), v = end * (1 - Math.pow(1 - p, 3));
      el.textContent = dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US');
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  }
  if ('IntersectionObserver' in w) {
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        $$('[data-count]').forEach(function(c){ if (!c._done && e.target.contains(c)) { c._done = 1; count(c); } });
        io.unobserve(e.target);
      });
    }, { threshold: .15, rootMargin: '0px 0px -40px 0px' });
    $$('.rv').forEach(function(el){ io.observe(el); });
    $$('.tk-stat').forEach(function(el){ io.observe(el); });
    /* pause hero animation when off screen */
    var hero = $('#tk-hero');
    if (hero) new IntersectionObserver(function(es){ hero.classList.toggle('tk-paused', !es[0].isIntersecting); }).observe(hero);
  } else $$('.rv').forEach(function(el){ el.classList.add('in'); });

  /* 6) tank follows the mouse */
  var box = $('#tk-tank-box'), tank = box && box.querySelector('.tk-tank');
  var heroEl = $('#tk-hero');
  if (tank && heroEl && !reduce && w.matchMedia('(hover:hover)').matches) {
    heroEl.addEventListener('pointermove', function(e){
      var r = box.getBoundingClientRect();
      tank.style.setProperty('--mx', Math.max(-1, Math.min(1, (e.clientX - r.left - r.width / 2) / r.width)).toFixed(3));
      tank.style.setProperty('--my', Math.max(-1, Math.min(1, (e.clientY - r.top - r.height / 2) / r.height)).toFixed(3));
    });
    heroEl.addEventListener('pointerleave', function(){ tank.style.setProperty('--mx', 0); tank.style.setProperty('--my', 0); });
  }

  /* 7) before / after slider */
  var ba = $('#tk-ba'), knob = $('#tk-knob'), touched = false;
  function setP(p){ p = Math.max(0, Math.min(100, p)); ba.style.setProperty('--p', p + '%'); knob.setAttribute('aria-valuenow', Math.round(p)); }
  if (ba && knob) {
    var drag = false;
    function at(e){ var r = ba.getBoundingClientRect(); setP((e.clientX - r.left) / r.width * 100); }
    ba.addEventListener('pointerdown', function(e){ drag = touched = true; at(e); try { ba.setPointerCapture(e.pointerId); } catch(_){} });
    ba.addEventListener('pointermove', function(e){ if (drag) at(e); });
    ba.addEventListener('pointerup', function(){ drag = false; });
    ba.addEventListener('pointercancel', function(){ drag = false; });
    knob.addEventListener('keydown', function(e){
      var v = +knob.getAttribute('aria-valuenow');
      if (e.key === 'ArrowLeft') { touched = true; setP(v - 5); e.preventDefault(); }
      if (e.key === 'ArrowRight') { touched = true; setP(v + 5); e.preventDefault(); }
    });
    /* demo sweep the first time it is seen */
    if (!reduce && 'IntersectionObserver' in w) {
      var bo = new IntersectionObserver(function(es){
        if (!es[0].isIntersecting) return;
        bo.disconnect();
        var keys = [[0,50],[900,18],[2000,82],[2900,50]], t0 = null;
        setTimeout(function(){
          (function anim(ts){
            if (touched) return;
            if (!t0) t0 = ts;
            var t = ts - t0, i = 0;
            while (i < keys.length - 1 && t > keys[i + 1][0]) i++;
            if (i >= keys.length - 1) { setP(50); return; }
            var a = keys[i], b = keys[i + 1], p = (t - a[0]) / (b[0] - a[0]), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
            setP(a[1] + (b[1] - a[1]) * e);
            requestAnimationFrame(anim);
          })(performance.now());
        }, 500);
      }, { threshold: .5 });
      bo.observe(ba);
    }
  }

  /* 8) 3D tilt cards */
  if (!reduce && w.matchMedia('(hover:hover)').matches) {
    $$('.tk-tilt').forEach(function(c){
      c.addEventListener('pointermove', function(e){
        var r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        c.style.setProperty('--ry', (x * 14).toFixed(2) + 'deg'); c.style.setProperty('--rx', (-y * 14).toFixed(2) + 'deg');
      });
      c.addEventListener('pointerleave', function(){ c.style.setProperty('--ry', '0deg'); c.style.setProperty('--rx', '0deg'); });
    });
  }

  /* 9) FAQ accordion */
  $$('.tk-q button').forEach(function(b){
    b.addEventListener('click', function(){
      var q = b.parentNode, open = !q.classList.contains('open');
      q.classList.toggle('open', open); b.setAttribute('aria-expanded', open);
    });
  });

  /* 10) insulation materials: water drop test + phone carousel */
  var matsBox = $('#tk-mats'), mats = $$('.tk-mat'), dots = $$('#tk-dots i'), matTouched = false;
  function play(m){ m.classList.remove('play'); void m.offsetWidth; m.classList.add('play'); }
  mats.forEach(function(m){ m.addEventListener('click', function(){ play(m); }); });
  if (matsBox && 'IntersectionObserver' in w) {
    var phone = function(){ return w.innerWidth <= 900; };
    var seen = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (!e.isIntersecting) return;
        var i = mats.indexOf(e.target);
        if (phone()) dots.forEach(function(d2, j){ d2.classList.toggle('on', j === i); });
        if (!e.target._played || phone()) { e.target._played = 1; play(e.target); }
      });
    }, { threshold: .6 });
    mats.forEach(function(m){ seen.observe(m); });
    ['pointerdown','touchstart','wheel'].forEach(function(ev){ matsBox.addEventListener(ev, function(){ matTouched = true; }, { passive: true }); });
    var secVisible = false;
    new IntersectionObserver(function(es){ secVisible = es[0].isIntersecting; }, { threshold: .4 }).observe(matsBox);
    if (!reduce) setInterval(function(){
      if (!phone() || matTouched || !secVisible) return;
      var cur = 0;
      dots.forEach(function(d2, j){ if (d2.classList.contains('on')) cur = j; });
      var next = mats[(cur + 1) % mats.length];
      var box = matsBox.getBoundingClientRect(), r = next.getBoundingClientRect();
      matsBox.scrollBy({ left: (r.left + r.width / 2) - (box.left + box.width / 2), behavior: 'smooth' });
    }, 3800);
  }

  /* 11) warranty: valid-until year */
  var wy = $('#tk-war-y');
  if (wy) wy.textContent = new Date().getFullYear() + 10;

  /* 13) cleaning: shared WhatsApp link builder */
  function waLink(msg){ return 'https://wa.me/966545833481?text=' + encodeURIComponent(msg); }
  function flash(el){ el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
  var TAIL = '\nالحي:\nنوع الخزان: أرضي / علوي';

  /* 14) "test your tank" quiz */
  var opts = $$('.tk-opt'), qres = $('#tk-qres'), qt = $('#tk-qtitle'), qd = $('#tk-qdesc'), qwa = $('#tk-qwa');
  function quiz(){
    var sel = opts.filter(function(o){ return o.dataset.k !== 'none' && o.getAttribute('aria-pressed') === 'true'; }).map(function(o){ return o.dataset.k; });
    var none = opts.some(function(o){ return o.dataset.k === 'none' && o.getAttribute('aria-pressed') === 'true'; });
    var lv = sel.length >= 2 ? '2' : sel.length === 1 ? '1' : none ? 'ok' : '0';
    var texts = {
      '0':  ['اختر العلامات اللي تلاحظها', 'كل ما اخترت علامة، يتغير لون المويه في الخزان.', '💬 اسألنا عن خزانك'],
      'ok': ['خزانك على ما يبدو تمام 👍', 'بس لا تنسى تنظفه وتعقمه كل 6 شهور.', '💬 احجز موعد التنظيف الجاي'],
      '1':  ['ننصحك تنظف خزانك قريب', 'فيه علامة تدل إن الخزان يحتاج تنظيف، والأفضل ما تأجله.', '💬 احجز تنظيف الخزان'],
      '2':  ['خزانك يحتاج تنظيف الحين', 'لاحظت أكثر من علامة، وهذا غالبًا معناه رواسب أو طحالب داخل الخزان.', '💬 احجز تنظيف الحين']
    };
    try { var custom = qres.getAttribute('data-texts'); if (custom) texts = JSON.parse(custom); } catch(e){}
    var t = texts[lv];
    qres.setAttribute('data-lv', lv);
    qt.textContent = t[0]; qd.textContent = t[1]; qwa.textContent = t[2];
    flash(qt.parentNode);
    var qtail = qres.getAttribute('data-tail'); if (qtail === null) qtail = TAIL;
    var qlabel = qres.getAttribute('data-label') || 'لاحظت';
    if (lv === 'ok') qwa.href = waLink((qres.getAttribute('data-msg-ok') || 'السلام عليكم، أبي أحجز موعد تنظيف خزان.') + qtail);
    else if (lv !== '0') qwa.href = waLink((qres.getAttribute('data-msg') || 'السلام عليكم، أبي تنظيف خزان.') + '\n' + qlabel + ': ' + sel.join('، ') + qtail);
  }
  opts.forEach(function(o){
    o.addEventListener('click', function(){
      var on = o.getAttribute('aria-pressed') !== 'true';
      o.setAttribute('aria-pressed', on);
      if (on) opts.forEach(function(x){ if ((o.dataset.k === 'none') !== (x.dataset.k === 'none')) x.setAttribute('aria-pressed', 'false'); });
      quiz();
    });
  });

  /* 15) what builds up inside the tank: hotspots */
  var hsVis = $('.tk-hs-vis'), hsEls = $$('.tk-hot').concat($$('.tk-hs-card'), $$('.tk-hs-tabs button')), hsI = 0, hsTouched = false, hsSeen = false;
  function hs(i){
    hsI = i; if (hsVis) hsVis.setAttribute('data-a', i);
    hsEls.forEach(function(el){ el.classList.toggle('on', +el.dataset.i === i); });
  }
  $$('.tk-hot, .tk-hs-tabs button').forEach(function(b){ b.addEventListener('click', function(){ hsTouched = true; hs(+b.dataset.i); }); });
  if (hsVis) {
    hs(0);
    if ('IntersectionObserver' in w) new IntersectionObserver(function(es){ hsSeen = es[0].isIntersecting; }, { threshold: .4 }).observe(hsVis);
    if (!reduce) setInterval(function(){ if (hsSeen && !hsTouched) hs((hsI + 1) % ($$('.tk-hs-card').length || 1)); }, 3200);
  }

  /* 18) Google review clicks */
  [['#tk-rev-btn', 'ضغطة_تقييم_جوجل'], ['#tk-rev-map', 'ضغطة_تقييمات_الخريطة']].forEach(function(p){
    var el = $(p[0]);
    if (el) el.addEventListener('click', function(){ if (w.naqaaTrack) w.naqaaTrack(p[1], { link_location: 'قسم التقييم' }); });
  });

  /* 19) compact links tabs */
  var tabsBox = $('.tk-tabs'), tabBtns = $$('.tk-tabs button');
  tabBtns.forEach(function(b, i){
    b.addEventListener('click', function(){
      tabBtns.forEach(function(x, j){ x.classList.toggle('on', i === j); x.setAttribute('aria-selected', i === j); var p = d.getElementById(x.getAttribute('aria-controls')); if (p) p.classList.toggle('on', i === j); });
      tabsBox.classList.toggle('s2', i === 1);
    });
  });

  /* 20) before/after: switch between several pairs */
  $$('.tk-ba-tabs button').forEach(function(b){
    b.addEventListener('click', function(){
      var box = $('#tk-ba'); if (!box) return;
      var imgs = box.querySelectorAll('img');
      if (b.getAttribute('data-bs')) imgs[0].srcset = b.getAttribute('data-bs'); else imgs[0].removeAttribute('srcset');
      if (!b.getAttribute('data-as')) imgs[1].removeAttribute('srcset');
      imgs[0].src = b.getAttribute('data-b'); imgs[0].alt = b.getAttribute('data-ba') || '';
      if (b.getAttribute('data-as')) imgs[1].srcset = b.getAttribute('data-as'); imgs[1].src = b.getAttribute('data-a'); imgs[1].alt = b.getAttribute('data-aa') || '';
      $$('.tk-ba-tabs button').forEach(function(x){ x.classList.toggle('on', x === b); });
      box.style.setProperty('--p', '50%');
    });
  });

  /* 21) price plans: pick the home condition */
  var plans = $$('.tk-plan:not(.link)'), planNum = $('#tk-plan-num'), planName = $('#tk-plan-name'), planWa = $('#tk-plan-wa'), planVal = 0;
  function animNum(el, from, to){
    if (reduce || !w.requestAnimationFrame) { el.textContent = to; return; }
    var t0 = null;
    (function step(ts){ if (!t0) t0 = ts; var p = Math.min((ts - t0) / 600, 1); el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); })(performance.now());
  }
  function pickPlan(pl){
    plans.forEach(function(x){ var on = x === pl; x.classList.toggle('on', on); x.setAttribute('aria-checked', on); });
    var v = +pl.getAttribute('data-price');
    if (planNum) { animNum(planNum, planVal, v); planVal = v; }
    if (planName) planName.textContent = pl.getAttribute('data-name');
    if (planWa) planWa.href = waLink('السلام عليكم، أبي ' + pl.getAttribute('data-msg') + '.' + (pl.getAttribute('data-tail') || TAIL));
  }
  plans.forEach(function(pl){ pl.addEventListener('click', function(){ pickPlan(pl); }); });
  if (plans.length) pickPlan($('.tk-plan.on') || plans[0]);

  /* 22) quote builder: choices become a ready WhatsApp message */
  var qb = $('#tk-qb');
  if (qb) {
    var qbOut = $('#tk-qb-out'), qbWa = $('#tk-qb-wa');
    var qbUpdate = function(){
      var parts = [], lines = [];
      $$('#tk-qb .tk-qb-row').forEach(function(row){
        var on = row.querySelector('button.on');
        if (on) { parts.push(on.textContent.trim()); lines.push(row.getAttribute('data-label') + ': ' + on.textContent.trim()); }
      });
      qbOut.textContent = parts.length ? parts.join(' • ') : qbOut.getAttribute('data-empty');
      qb.classList.toggle('ready', parts.length > 0);
      qbWa.href = waLink(qb.getAttribute('data-msg') + (lines.length ? '\n' + lines.join('\n') : '') + '\nالحي:');
    };
    $$('#tk-qb .tk-qb-row button').forEach(function(b){
      b.addEventListener('click', function(){
        b.parentNode.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on', x === b); });
        qbUpdate();
      });
    });
    qbUpdate();
  }

  /* 23) team: normal job vs big job */
  var team = $('#tk-team');
  if (team) {
    $$('#tk-team .tk-team-sw button').forEach(function(b){
      b.addEventListener('click', function(){
        $$('#tk-team .tk-team-sw button').forEach(function(x){ x.classList.toggle('on', x === b); });
        team.setAttribute('data-size', b.getAttribute('data-size'));
      });
    });
  }

  /* 24) hub: orbit highlight cycles through services and updates the caption */
  var hbIcos = $$('.hb-ico'), hbCap = $('#hb-cap'), hbI = 0, hbHold = false;
  function hbShow(i){
    hbI = i;
    hbIcos.forEach(function(a, j){ a.classList.toggle('on', j === i); });
    var a = hbIcos[i];
    if (hbCap && a) { hbCap.href = a.getAttribute('href'); hbCap.querySelector('.ic').textContent = a.getAttribute('data-ic'); hbCap.querySelector('.t').textContent = a.getAttribute('data-name'); hbCap.querySelector('.p').textContent = a.getAttribute('data-price'); flash(hbCap); }
  }
  if (hbIcos.length) {
    hbShow(0);
    hbIcos.forEach(function(a, j){ a.addEventListener('pointerenter', function(){ hbHold = true; hbShow(j); }); a.addEventListener('pointerleave', function(){ hbHold = false; }); });
    if (!reduce) setInterval(function(){ if (!hbHold && !d.hidden) hbShow((hbI + 1) % hbIcos.length); }, 2600);
  }

  /* 25) hub: service filter */
  var hbF = $$('.hb-filter button'), hbCards = $$('.hb-card');
  hbF.forEach(function(b){
    b.addEventListener('click', function(){
      var f = b.getAttribute('data-f');
      hbF.forEach(function(x){ x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); });
      var k = 0;
      hbCards.forEach(function(c){
        var show = f === 'all' || (' ' + c.getAttribute('data-c') + ' ').indexOf(' ' + f + ' ') > -1;
        c.classList.toggle('off', !show);
        if (show) { c.style.setProperty('--k', k++); c.classList.remove('pop'); void c.offsetWidth; c.classList.add('pop'); }
      });
    });
  });

  /* 25b) hub: a light runs around one service card at a time */
  var hbLit = -1;
  if (hbCards.length && !reduce) setInterval(function(){
    if (d.hidden) return;
    var vis = hbCards.filter(function(c){ return !c.classList.contains('off'); });
    hbCards.forEach(function(c){ c.classList.remove('lit'); });
    if (!vis.length) return;
    hbLit = (hbLit + 1) % vis.length; vis[hbLit].classList.add('lit');
  }, 2200);

  /* 26) hub: "not sure what you need?" helper */
  var wz = $('#hb-wz');
  if (wz) {
    var wzPlace = null, wzNeed = null, wzOut = $('#hb-wz-out');
    var MAP = JSON.parse(wz.getAttribute('data-map'));
    var wzStep = function(n){ wz.setAttribute('data-step', n); $$('#hb-wz .hb-dots i').forEach(function(x, j){ x.classList.toggle('on', j < n); }); };
    $$('#hb-wz [data-place]').forEach(function(b){
      b.addEventListener('click', function(){
        wzPlace = b.getAttribute('data-place');
        $$('#hb-wz [data-place]').forEach(function(x){ x.classList.toggle('on', x === b); });
        wzStep(2);
      });
    });
    $$('#hb-wz [data-need]').forEach(function(b){
      b.addEventListener('click', function(){
        wzNeed = b.getAttribute('data-need');
        $$('#hb-wz [data-need]').forEach(function(x){ x.classList.toggle('on', x === b); });
        var r = (MAP[wzNeed] && (MAP[wzNeed][wzPlace] || MAP[wzNeed]['*'])) || MAP['general']['*'];
        $('#hb-wz-ic').textContent = r[0]; $('#hb-wz-t').textContent = r[1]; $('#hb-wz-p').textContent = r[2];
        $('#hb-wz-go').href = r[3];
        $('#hb-wz-wa').href = waLink('السلام عليكم، أبي ' + r[1] + '.\nنوع المكان: ' + wzPlace + '\nالحي:');
        wzStep(3); flash(wzOut);
      });
    });
    var back = $('#hb-wz-back');
    if (back) back.addEventListener('click', function(){ wzPlace = wzNeed = null; $$('#hb-wz .on[data-place], #hb-wz .on[data-need]').forEach(function(x){ x.classList.remove('on'); }); wzStep(1); });
  }

  /* 27) hub: district finder with compass */
  var dz = $('#hb-dz');
  if (dz) {
    var tabs = $$('#hb-dz .hb-reg button'), lists = $$('#hb-dz .hb-dlist'), needle = $('#hb-needle'), dzTouched = false, dzI = 0;
    var DEG = { north: 0, east: 90, south: 180, west: 270, center: 0 };
    var region = function(r, i){
      dzI = i;
      tabs.forEach(function(t){ var on = t.getAttribute('data-r') === r; t.classList.toggle('on', on); t.setAttribute('aria-selected', on); });
      lists.forEach(function(l){ l.classList.toggle('on', l.getAttribute('data-r') === r); });
      if (needle) { needle.style.setProperty('--deg', DEG[r] + 'deg'); needle.classList.toggle('mid', r === 'center'); }
    };
    tabs.forEach(function(t, i){ t.addEventListener('click', function(){ dzTouched = true; region(t.getAttribute('data-r'), i); }); });
    region(tabs[0].getAttribute('data-r'), 0);
    if (!reduce) setInterval(function(){ if (!dzTouched && !d.hidden) { var n = (dzI + 1) % tabs.length; region(tabs[n].getAttribute('data-r'), n); } }, 3800);
    var inp = $('#hb-dz-in'), res = $('#hb-dz-res'), norm = function(s){ return s.replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي').trim().replace(/^حي\s+/, '').replace(/^ال/, ''); };
    var all = $$('#hb-dz .hb-dlist span').map(function(s){ return { n: s.textContent.trim(), r: s.parentNode.getAttribute('data-r'), label: s.parentNode.getAttribute('data-label') }; });
    var check = function(){
      var q = norm(inp.value || '');
      if (q.length < 2) { res.className = 'hb-dz-res'; res.innerHTML = ''; return; }
      var hit = all.filter(function(x){ return norm(x.n).indexOf(q) === 0 || norm(x.n) === q; })[0];
      dzTouched = true;
      var name = hit ? hit.n : inp.value.trim().replace(/^حي\s+/, '');
      if (hit) region(hit.r, tabs.map(function(t){ return t.getAttribute('data-r'); }).indexOf(hit.r));
      res.className = 'hb-dz-res show';
      res.innerHTML = '<b>✓ نخدم حي ' + name.replace(/[<>&"]/g, '') + (hit ? ' (' + hit.label + ')' : '') + '</b><span>ونوصلك غالبًا بنفس اليوم.</span><a class="tk-btn tk-btn-wa" target="_blank" rel="noopener" href="' + waLink('السلام عليكم، أبي أحجز تنظيف في حي ' + name + '.\nالخدمة:') + '">💬 احجز في حيّك</a>';
    };
    if (inp) { inp.addEventListener('input', check); inp.addEventListener('change', check); }
  }

  /* 28) lazy muted videos: load and play only while on screen */
  var vids = $$('video.mj-vid');
  if (vids.length && 'IntersectionObserver' in w) {
    var vio = new IntersectionObserver(function(es){
      es.forEach(function(e){
        var v = e.target;
        if (e.isIntersecting) {
          if (!v.src) { v.src = v.getAttribute('data-src'); }
          if (!reduce) { var p = v.play(); if (p && p.catch) p.catch(function(){}); }
        } else if (!v.paused) v.pause();
      });
    }, { threshold: .35 });
    vids.forEach(function(v){ vio.observe(v); v.addEventListener('click', function(){ if (v.paused) v.play(); else v.pause(); }); });
  }

  /* 29) reel dots follow the horizontal scroll */
  var reel = $('.mj-reel'), rdots = $('.mj-dots');
  if (reel && rdots) {
    var cards = $$('.mj-reel .mj-card');
    rdots.innerHTML = cards.map(function(){ return '<i></i>'; }).join('');
    var dl = $$('.mj-dots i');
    var upd = function(){
      var mid = reel.getBoundingClientRect().left + reel.clientWidth / 2, best = 0, bd = 1e9;
      cards.forEach(function(c, i){ var r = c.getBoundingClientRect(), dd = Math.abs(r.left + r.width / 2 - mid); if (dd < bd) { bd = dd; best = i; } });
      dl.forEach(function(x, i){ x.classList.toggle('on', i === best); });
    };
    reel.addEventListener('scroll', function(){ requestAnimationFrame(upd); }, { passive: true });
    upd();
  }

  /* 12) scroll: timeline fill + side tank meter */
  var tl = $('#tk-tl'), steps = $$('.tk-step'), meter = $('#tk-meter'), mv = $('#tk-meter-v'), ticking = false;
  function onScroll(){
    ticking = false;
    var vh = w.innerHeight;
    if (tl) {
      var r = tl.getBoundingClientRect(), p = Math.max(0, Math.min(1, (vh * .6 - r.top) / r.height));
      tl.style.setProperty('--tlp', (p * 100).toFixed(1) + '%');
      steps.forEach(function(s){ s.classList.toggle('on', s.getBoundingClientRect().top < vh * .6); });
    }
    if (meter) {
      var y = w.scrollY, max = d.documentElement.scrollHeight - vh, lv = max > 0 ? Math.round(y / max * 100) : 0;
      meter.classList.toggle('show', y > vh * .7);
      meter.style.setProperty('--lv', lv + '%');
      mv.textContent = lv >= 99 ? '✨ 100%' : lv + '%';
    }
  }
  w.addEventListener('scroll', function(){ if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  w.addEventListener('resize', onScroll);
  onScroll();
})();
