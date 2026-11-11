"""Build /en/pricing/ (English booking calculator) from the Arabic /pricing/ page.

Usage: python3 tools/build_pricing_en.py

Prices and calculator logic live only in pricing/index.html. Re-run this after
changing that page so the English calculator keeps the same prices and features.
Texts come from tools/pricing_en_strings.py; the build stops if any visible
Arabic text in the calculator has no translation.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pricing_en_strings import JS, KEEP, MARKUP  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.naqaa-cleaning.com'
AR_URL, EN_URL = '/pricing/', '/en/pricing/'
AR = re.compile(r'[؀-ۿ]')

TITLE = 'Cleaning Prices in Riyadh: Price Calculator | Naqaa Cleaning'
DESC = ('Instant prices for home, villa, water tank, majlis, AC and pest control cleaning in Riyadh. '
        'Apartments from 200 SAR. Book in a minute.')


def read(rel):
    raw = open(os.path.join(ROOT, rel), encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def region(t, start, end, include_end=True):
    a = t.index(start)
    b = t.index(end, a) + (len(end) if include_end else 0)
    return a, b


def js_escape(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def translate_js(js, missing):
    def rep(m):
        s = m.group(1)
        if not AR.search(s) or s in KEEP:
            return m.group(0)
        if s in JS:
            return "'" + js_escape(JS[s]) + "'"
        missing.add(s)
        return m.group(0)
    return re.sub(r"'((?:[^'\\\n]|\\.)*)'", rep, js)


def translate_markup(html, missing):
    def text(m):
        s = m.group(1)
        if not AR.search(s):
            return m.group(0)
        if s in MARKUP:
            return '>' + MARKUP[s] + '<'
        missing.add(s)
        return m.group(0)

    def attr(m):
        s = m.group(2)
        if not AR.search(s):
            return m.group(0)
        if s in MARKUP:
            return f'{m.group(1)}="{MARKUP[s]}"'
        missing.add(s)
        return m.group(0)
    html = re.sub(r'>([^<]+)<', text, html)
    return re.sub(r'\b(placeholder|aria-label|title|alt|value)="([^"]*)"', attr, html)


def head_jsonld():
    blocks = [
        {'@context': 'https://schema.org', '@type': 'WebPage', '@id': BASE + EN_URL + '#page', 'url': BASE + EN_URL,
         'name': TITLE, 'description': DESC, 'inLanguage': 'en',
         'isPartOf': {'@type': 'WebSite', 'name': 'Naqaa Cleaning Establishment', 'url': BASE + '/en/'}},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE + '/en/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Price calculator', 'item': BASE + EN_URL}]},
    ]
    return ''.join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=1) + '\n</script>\n'
                   for b in blocks)


def build():
    t, nl = read('pricing/index.html')
    ref, _ = read('en/services/index.html')
    missing = set()

    # ---------------- head ----------------
    t = re.sub(r'<html lang="ar" dir="rtl">', '<html lang="en" dir="ltr">', t, count=1)
    t = re.sub(r'<title>.*?</title>', f'<title>{TITLE}</title>', t, count=1)
    for name, val in [('description', DESC), ('author', 'Naqaa Cleaning Establishment')]:
        t = re.sub(rf'(<meta name="{name}" content=")[^"]*', lambda m, v=val: m.group(1) + v, t, count=1)
    for prop, val in [('og:title', TITLE), ('og:description', DESC), ('og:site_name', 'Naqaa Cleaning Establishment'),
                      ('og:url', BASE + EN_URL), ('og:locale', 'en_US')]:
        t = re.sub(rf'(<meta property="{prop}" content=")[^"]*', lambda m, v=val: m.group(1) + v, t, count=1)
    for name, val in [('twitter:title', TITLE), ('twitter:description', DESC)]:
        t = re.sub(rf'(<meta name="{name}" content=")[^"]*', lambda m, v=val: m.group(1) + v, t, count=1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + BASE + EN_URL, t, count=1)
    t = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', '', t)
    t = re.sub(r'<meta name="keywords" content="[^"]*">\n?', '', t)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', t, flags=re.S)
    alternates = (f'<link rel="alternate" hreflang="ar" href="{BASE}{AR_URL}">\n'
                  f'<link rel="alternate" hreflang="en" href="{BASE}{EN_URL}">\n'
                  f'<link rel="alternate" hreflang="x-default" href="{BASE}{AR_URL}">\n')
    ltr_css = ('<style id="bk-ltr">/* English page: left-to-right layout; steps slide in from the other side */body{direction:ltr}'
               '@keyframes bkIn{from{opacity:0;transform:translateX(36px)}to{opacity:1;transform:none}}'
               '@keyframes bkInBack{from{opacity:0;transform:translateX(-36px)}to{opacity:1;transform:none}}'
               # English menu labels are longer: tighten the header on mid-size screens (same as nq-ui.css)
               '@media(min-width:1000px) and (max-width:1399px){html[dir=ltr] body .nq-nav{gap:14px}html[dir=ltr] body .nq-nav a{font-size:14px}}'
               '@media(min-width:1000px) and (max-width:1149px){html[dir=ltr] body .nq-nav{gap:10px}html[dir=ltr] body .nq-nav a{font-size:13px}html[dir=ltr] body .nq-call{padding-inline:14px}}'
               '</style>\n')
    t = t.replace('</head>', alternates + head_jsonld() + ltr_css + '</head>', 1)

    # ---------------- header / menu (from the English site) ----------------
    a, b = region(t, '<header id="nq-hdr">', '\n', include_end=False)
    b = t.index('<main class="bk"', a)
    ra, rb = region(ref, '<header id="nq-hdr">', '\n', include_end=False)
    rb = ref.index('\n', ref.index('</nav><div id="navbar"', ra)) + 1
    en_header = ref[ra:rb]
    # every "Arabic version" link (header pill and mobile menu) must point at the Arabic calculator
    en_header = re.sub(r'href="/services/"((?: class="[^"]*")? hreflang="ar")', r'href="/pricing/"\1', en_header)
    # keep the hidden placeholder elements the page's older scripts expect
    old_header = t[a:b]
    for pid in re.findall(r'<div id="([^"]+)" hidden></div>', old_header):
        if f'id="{pid}"' not in en_header:
            en_header = en_header.rstrip('\n') + f'<div id="{pid}" hidden></div>\n'
    t = t[:a] + en_header + '\n' + t[b:]

    # ---------------- calculator markup ----------------
    a = t.index('<main class="bk"')
    b = t.index('</div>\n</div>', t.index('id="bk-done"')) + len('</div>\n</div>')
    mk = translate_markup(t[a:b], missing)
    mk = mk.replace('id="bk-back" aria-label="Back">→</button>', 'id="bk-back" aria-label="Back">←</button>')  # LTR back arrow
    t = t[:a] + mk + t[b:]

    # ---------------- footer + contact bar (from the English site) ----------------
    a, b = region(t, '<footer id="nq-footer">', '</footer>')
    ra, rb = region(ref, '<footer id="nq-footer">', '</footer>')
    t = t[:a] + ref[ra:rb] + t[b:]
    t = t.replace('<a href="/services/" hreflang="ar" lang="ar">', '<a href="/pricing/" hreflang="ar" lang="ar">')  # Arabic link in copied blocks -> Arabic calculator
    a, b = region(t, '<div id="nq-fbar"', '</div>')
    ra, rb = region(ref, '<div id="nq-fbar"', '</div>')
    t = t[:a] + ref[ra:rb] + t[b:]
    t = t.replace('<a href="/services/" hreflang="ar" lang="ar">', '<a href="/pricing/" hreflang="ar" lang="ar">')  # Arabic link in copied blocks -> Arabic calculator

    # ---------------- calculator script ----------------
    a = t.index('<script>window.NQ_BOOKING')
    b = t.index('</script>', a)
    js = translate_js(t[a:b], missing)
    js = js.replace("'←'", "'→'")  # 'go' arrows point forward in LTR
    t = t[:a] + js + t[b:]

    if missing:
        print('Untranslated strings (add them to tools/pricing_en_strings.py):')
        for s in sorted(missing):
            print('  ', repr(s))
        raise SystemExit(1)

    # anything Arabic left outside the allowed places?
    body = t[t.index('<body'):]
    allowed = [r'lang="ar">[^<]*<',                     # "العربية" language switch links
               r'/\[[,\u066B\u0660-\u0669\u06F0-\u06F9-]+\]/g']  # digit/decimal-normalising regexes
    allowed += ["'" + re.escape(k) + "'" for k in KEEP]  # analytics names, digit tables
    spans = [(m.start(), m.end()) for p in allowed for m in re.finditer(p, body)]
    leftovers = sorted({body[max(0, m.start() - 25):m.start() + 25].replace('\n', ' ')
                        for m in AR.finditer(body) if not any(s <= m.start() < e for s, e in spans)})
    if leftovers:
        print('Arabic left in the page body:')
        for c in leftovers[:20]:
            print('  ', c)
        raise SystemExit(1)

    out = os.path.join(ROOT, 'en', 'pricing', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))
    print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    build()
