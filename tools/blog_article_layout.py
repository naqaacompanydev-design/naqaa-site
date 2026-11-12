"""Convert a Naqaa blog article page to the light "paper" reading layout.

Usage: python3 tools/blog_article_layout.py blog/<slug>/index.html [...]

What it does to each page (idempotent, skips pages already converted):
- adds body class "nq-art" plus /assets/nq-article.css and /assets/nq-article.js
- replaces the dark image hero with a navy title band (breadcrumb, category,
  the page's single <h1>, meta with SVG icons) and a clear cover image
- removes the duplicate title/meta/first figure that repeated the hero
- computes the real reading time from the article text
- gives every section <h2> an id and adds a table of contents
  (collapsible box in the article on mobile, sticky box in the sidebar on desktop)
- adds a booking card (price calculator + WhatsApp) after the third section
- strips decorative emoji from sidebar headings
"""
import html as H
import os
import re
import sys

WPM = 200
WA = "966545833481"

ICON_CAL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4.5" width="18" height="17" rx="3"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/></svg>'
ICON_CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M12 7v5l3.5 2"/></svg>'
ICON_USER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>'
ICON_CALC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="2.5" width="16" height="19" rx="3"/><path d="M8 7h8"/><path d="M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/></svg>'
ICON_WA = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.26-.46-2.39-1.47-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.13-.14.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.03-.52-.07-.15-.67-1.61-.92-2.2-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.21 3.07c.15.2 2.1 3.2 5.08 4.49.71.3 1.26.49 1.7.63.71.22 1.36.19 1.87.12.57-.09 1.76-.72 2.01-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35zM12.05 21.78h-.01a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 0 1-1.51-5.26c0-5.45 4.44-9.88 9.89-9.88 2.64 0 5.12 1.03 6.99 2.9a9.83 9.83 0 0 1 2.89 6.99c0 5.45-4.44 9.88-9.88 9.88z"/></svg>'

EMOJI = re.compile(r'^[\s☀-➿\U0001F000-\U0001FAFF️‍]+')
COMMENT = re.compile(r'<!--.*?-->', re.S)
HIDDEN = re.compile(r'\x00(\d+)\x00')


def hide_comments(s):
    """Swap HTML comments for placeholders so tag scans never match markup inside a comment
    (the article template's instructions comment contains example tags such as <h2>)."""
    store = []

    def keep(m):
        store.append(m.group(0))
        return f'\x00{len(store) - 1}\x00'
    return COMMENT.sub(keep, s), store


def show_comments(s, store):
    return HIDDEN.sub(lambda m: store[int(m.group(1))], s)


def minutes_label(m):
    """Arabic: 3-10 take the plural (دقائق), everything else the singular (دقيقة)."""
    return f'{m} دقائق قراءة' if 3 <= m <= 10 else f'{m} دقيقة قراءة'


def text_of(fragment):
    t = HIDDEN.sub(' ', COMMENT.sub(' ', fragment))
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', t, flags=re.S)
    return H.unescape(re.sub(r'<[^>]+>', ' ', t))


def strip_emoji(s):
    return EMOJI.sub('', s).strip()


def convert(path):
    raw = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    if 'nq-art' in t:
        return 'skip (already converted)'

    # ---- hero ----
    if '<div class="art-layout">' in t and 'class="article-hero' not in t:
        return convert_legacy(path, raw, nl, t)
    hero = re.search(r'[ \t]*<div class="(?:nq-ended-wrap )?article-hero">\s*<img src="([^"]+)" alt="([^"]*)"[^>]*>'
                     r'(\s*<div class="nq-ended".*?</div>)?\s*'
                     r'<div class="hero-overlay">(.*?)</div>\s*</div>\n', t, re.S)
    if not hero:
        return 'FAIL: no article-hero'
    hero_src, hero_alt, stamp, overlay = hero.groups()
    stamp = (stamp or '').strip()
    cat_m = re.search(r'<span class="article-cat">(.*?)</span>', overlay, re.S)
    cat = cat_m.group(1).strip() if cat_m else ''

    # ---- breadcrumb / h1 / meta inside main ----
    bc = re.search(r'[ \t]*<nav class="breadcrumb"[^>]*>.*?</nav>\n', t, re.S)
    h1 = re.search(r'[ \t]*<h1>(.*?)</h1>\n', t, re.S)
    meta = re.search(r'[ \t]*<div class="article-meta">(.*?)</div>\n', t, re.S)
    if not (bc and h1 and meta):
        return 'FAIL: breadcrumb/h1/meta not found'
    spans = [strip_emoji(text_of(s)).strip() for s in re.findall(r'<span>(.*?)</span>', meta.group(1), re.S)]
    date = next((s for s in spans if re.search(r'20\d\d', s)), '')
    author = next((s for s in spans if 'بقلم' in s), '')

    main_m = re.search(r'<main class="article-body">(.*?)</main>', t, re.S)
    if not main_m:
        return 'FAIL: no main'
    main, comments = hide_comments(main_m.group(1))
    cta_at = main.find('<div class="cta-section')
    body_for_count = main[:cta_at] if cta_at > 0 else main
    words = len(text_of(body_for_count).split())
    minutes = max(1, round(words / WPM))

    # remove breadcrumb, h1, meta from main
    for m in (bc, h1, meta):
        main = main.replace(m.group(0), '', 1)
    # drop a leading figure that repeats the hero image
    fig = re.search(r'<figure[^>]*>\s*<img src="([^"]+)"[^>]*>.*?</figure>\n*', main, re.S)
    if fig and os.path.basename(fig.group(1)) == os.path.basename(hero_src) and main.find(fig.group(0)) < 400:
        main = main.replace(fig.group(0), '', 1)

    # ---- section ids + toc ----
    cta_at = main.find('<div class="cta-section')
    head_part, tail_part = (main[:cta_at], main[cta_at:]) if cta_at > 0 else (main, '')
    toc = []

    def add_id(m):
        n = len(toc) + 1
        label = strip_emoji(text_of(m.group(2))).strip()
        toc.append((f's{n}', label))
        return f'<h2{m.group(1)} id="s{n}">{m.group(2)}</h2>'
    head_part = re.sub(r'<h2((?:(?!\bid=)[^>])*)>(.*?)</h2>', add_id, head_part, flags=re.S)
    main = head_part + tail_part

    items = ''.join(f'<li><a href="#{i}">{H.escape(l)}</a></li>' for i, l in toc)
    toc_inline = (f'<details class="art-toc art-toc-inline"><summary>محتويات المقال <small>{len(toc)} قسم</small></summary>'
                  f'<ol>{items}</ol></details>\n')
    toc_side = (f'<details class="art-toc art-toc-side" open><summary>محتويات المقال <small>{len(toc)} قسم</small></summary>'
                f'<ol>{items}</ol></details>\n')

    wa_text = 'السلام عليكم، قريت مقال "' + text_of(h1.group(1)).strip() + '" وأبي أستفسر عن الخدمة'
    from urllib.parse import quote
    book = ('<aside class="art-book" aria-label="احجز">'
            '<div class="art-book-txt"><b>تبي تعرف السعر قبل ما تحجز؟</b>'
            '<span>اختار الخدمة واحسب سعرك في دقيقة، أو كلمنا على واتساب.</span></div>'
            f'<div class="art-book-btns"><a class="bk-p" data-nq="price" href="/pricing/">{ICON_CALC}احسب سعرك</a>'
            f'<a class="bk-w" href="https://wa.me/{WA}?text={quote(wa_text)}" target="_blank" rel="noopener">{ICON_WA}واتساب</a></div>'
            '</aside>\n')

    # toc after the intro box (or at the very top of the article)
    intro = re.search(r'<div class="intro-box[^"]*">.*?</div>\n', main, re.S)
    if intro:
        main = main.replace(intro.group(0), intro.group(0) + toc_inline, 1)
    else:
        main = toc_inline + main
    # booking card before the 3rd section heading (or after the toc)
    h2s = [m.start() for m in re.finditer(r'<h2 id="s\d+"|<h2[^>]* id="s\d+"', main)]
    pos = h2s[2] if len(h2s) > 2 else (h2s[-1] if h2s else len(main))
    main = main[:pos] + book + main[pos:]

    t = t.replace(main_m.group(1), show_comments(main, comments), 1)

    # ---- header band + cover ----
    cat_html = f'<span class="art-cat">{cat}</span>\n' if cat else ''
    meta_html = '<div class="art-meta">'
    if date:
        meta_html += f'<span>{ICON_CAL}{H.escape(date)}</span>'
    meta_html += f'<span>{ICON_CLOCK}{minutes_label(minutes)}</span>'
    if author:
        meta_html += f'<span>{ICON_USER}{H.escape(author.replace("بقلم:", "").strip())}</span>'
    meta_html += '</div>'
    band = ('<header class="art-head"><div class="art-head-in">\n' + bc.group(0).strip() + '\n' + cat_html
            + f'<h1>{h1.group(1)}</h1>\n' + meta_html + '\n</div></header>\n'
            + '<div class="art-paper">\n'
            + cover_html(hero_src, hero_alt, stamp))
    t = t.replace(hero.group(0), band, 1)
    # close .art-paper right before the site footer
    fpos = t.find('<footer', t.find('</aside>', t.find('<aside class="sidebar"')))
    if fpos < 0:
        return 'FAIL: footer not found'
    line_start = t.rfind('\n', 0, fpos) + 1
    t = t[:line_start] + '</div><!-- /art-paper -->\n' + t[line_start:]

    # ---- sidebar: toc on top, no emoji in headings ----
    t = t.replace('<div class="sidebar-inner">', '<div class="sidebar-inner">\n' + toc_side, 1)
    t = re.sub(r'(<div class="sidebar-card-head"><h4>)(.*?)(</h4>)',
               lambda m: m.group(1) + strip_emoji(m.group(2)) + m.group(3), t)
    t = re.sub(r'(<div class="offer-box[^"]*">\s*<h3>)(.*?)(</h3>)',
               lambda m: m.group(1) + strip_emoji(m.group(2)) + m.group(3), t)

    # ---- body class + assets ----
    t = t.replace('<body class="nq-inner">', '<body class="nq-inner nq-art">', 1)
    t = t.replace('</head>', '<link rel="stylesheet" href="/assets/nq-article.css">\n'
                  '<script src="/assets/nq-article.js" defer></script>\n</head>', 1)
    # schema: keep timeRequired in step with the shown reading time, if present
    t = re.sub(r'"timeRequired"\s*:\s*"PT\d+M"', f'"timeRequired": "PT{minutes}M"', t)

    open(path, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))
    return f'ok: {words} words, {minutes} min, {len(toc)} sections'


def cover_html(src, alt, stamp=''):
    cls = 'art-cover nq-ended-wrap' if stamp else 'art-cover'
    return (f'<figure class="{cls}"><img src="{src}" alt="{alt}" fetchpriority="high" decoding="async">'
            f'{stamp}</figure>\n')


def meta_block(date, minutes, author=''):
    h = '<div class="art-meta">'
    if date:
        h += f'<span>{ICON_CAL}{H.escape(date)}</span>'
    h += f'<span>{ICON_CLOCK}{minutes_label(minutes)}</span>'
    if author:
        h += f'<span>{ICON_USER}{H.escape(author.replace("بقلم:", "").strip())}</span>'
    return h + '</div>'


def booking_card(title):
    from urllib.parse import quote
    wa_text = 'السلام عليكم، قريت مقال "' + title + '" وأبي أستفسر عن الخدمة'
    return ('<aside class="art-book" aria-label="احجز">'
            '<div class="art-book-txt"><b>تبي تعرف السعر قبل ما تحجز؟</b>'
            '<span>اختار الخدمة واحسب سعرك في دقيقة، أو كلمنا على واتساب.</span></div>'
            f'<div class="art-book-btns"><a class="bk-p" data-nq="price" href="/pricing/">{ICON_CALC}احسب سعرك</a>'
            f'<a class="bk-w" href="https://wa.me/{WA}?text={quote(wa_text)}" target="_blank" rel="noopener">{ICON_WA}واتساب</a></div>'
            '</aside>\n')


def add_toc(main):
    """Give section h2s ids; return (main, toc_inline, toc_side)."""
    cta_at = main.find('<div class="cta-section')
    head_part, tail_part = (main[:cta_at], main[cta_at:]) if cta_at > 0 else (main, '')
    toc = []

    def add_id(m):
        n = len(toc) + 1
        toc.append((f's{n}', strip_emoji(text_of(m.group(2))).strip()))
        return f'<h2{m.group(1)} id="s{n}">{m.group(2)}</h2>'
    head_part = re.sub(r'<h2((?:(?!\bid=)[^>])*)>(.*?)</h2>', add_id, head_part, flags=re.S)
    items = ''.join(f'<li><a href="#{i}">{H.escape(l)}</a></li>' for i, l in toc)
    head = f'<summary>محتويات المقال <small>{len(toc)} قسم</small></summary><ol>{items}</ol></details>\n'
    return (head_part + tail_part,
            '<details class="art-toc art-toc-inline">' + head,
            '<details class="art-toc art-toc-side" open>' + head)


def insert_before_nth_h2(main, html, n=3):
    h2s = [m.start() for m in re.finditer(r'<h2[^>]* id="s\d+"', main)]
    pos = h2s[n - 1] if len(h2s) >= n else (h2s[-1] if h2s else len(main))
    return main[:pos] + html + main[pos:]


def finish(t, minutes):
    t = re.sub(r'<body class="([^"]*)">', lambda m: f'<body class="{m.group(1)} nq-art">', t, count=1)
    t = t.replace('</head>', '<link rel="stylesheet" href="/assets/nq-article.css">\n'
                  '<script src="/assets/nq-article.js" defer></script>\n</head>', 1)
    t = re.sub(r'"timeRequired"\s*:\s*"PT\d+M"', f'"timeRequired": "PT{minutes}M"', t)
    t = re.sub(r'(<div class="(?:sidebar-card-head|sb-card)[^"]*"[^>]*><h[34][^>]*>)(.*?)(</h[34]>)',
               lambda m: m.group(1) + strip_emoji(m.group(2)) + m.group(3), t)
    return t


def convert_legacy(path, raw, nl, t):
    """Older article template (art-hero / art-layout / art-card / art-sidebar)."""
    strip = re.search(r'<div style="background:rgba\(17,34,64,\.5\)[^"]*">\s*<div class="container"[^>]*>\s*'
                      r'<nav class="page-breadcrumb">(.*?)</nav>\s*</div>\s*</div>\n', t, re.S)
    hero = re.search(r'<div class="art-hero">\s*<div class="container">\s*<div class="section-tag">(.*?)</div>\s*'
                     r'<h1>(.*?)</h1>\s*<div class="art-hero-meta">(.*?)</div>\s*</div>\s*</div>\n', t, re.S)
    wrap = re.search(r'<div style="background:var\(--navy\);padding-bottom:80px">\s*<div class="art-layout">\s*<main>', t)
    cover = re.search(r'<div class="(?:nq-ended-wrap )?art-cover">(<img[^>]*>)(<div class="nq-ended".*?</div>)?</div>\n?', t, re.S)
    if not (strip and hero and wrap and cover):
        return 'FAIL: legacy layout not recognised'
    links = re.findall(r'<a href="([^"]+)">(.*?)</a>', strip.group(1))
    last = re.findall(r'<span style="color:var\(--white\)">(.*?)</span>', strip.group(1))
    bc = '<nav class="breadcrumb" aria-label="مسار التنقل">' + ''.join(
        f'<a href="{u}">{x}</a><span class="bc-sep">›</span>' for u, x in links) + (f'<span>{last[0]}</span>' if last else '') + '</nav>'
    cat = strip_emoji(text_of(hero.group(1)))
    title = hero.group(2)
    spans = [strip_emoji(text_of(s)).strip() for s in re.findall(r'<span>(.*?)</span>', hero.group(3), re.S)]
    date = next((s for s in spans if re.search(r'20\d\d', s)), '')

    img = re.sub(r'\sloading="[^"]*"', '', cover.group(1)).replace('<img ', '<img fetchpriority="high" decoding="async" ', 1)
    stamp = cover.group(2) or ''
    cls = 'art-cover nq-ended-wrap' if stamp else 'art-cover'
    t = t.replace(cover.group(0), '', 1)
    t = t.replace(wrap.group(0), f'<div class="art-paper">\n<figure class="{cls}">{img}{stamp}</figure>\n'
                  '<div class="art-layout page-wrapper">\n<main>', 1)

    main_m = re.search(r'<main>(.*?)</main>', t, re.S)
    main, comments = hide_comments(main_m.group(1))
    minutes = max(1, round(len(text_of(main).split()) / WPM))
    main, toc_inline, toc_side = add_toc(main)
    main = toc_inline + insert_before_nth_h2(main, booking_card(text_of(title).strip()))
    t = t.replace(main_m.group(0), '<main class="article-body">' + show_comments(main, comments) + '</main>', 1)

    band = ('<header class="art-head"><div class="art-head-in">\n' + bc + '\n'
            + (f'<span class="art-cat">{H.escape(cat)}</span>\n' if cat else '')
            + f'<h1>{title}</h1>\n' + meta_block(date, minutes) + '\n</div></header>\n')
    t = t.replace(strip.group(0), '', 1).replace(hero.group(0), band, 1)
    t = t.replace('<aside class="art-sidebar">', '<aside class="art-sidebar sidebar"><div class="sidebar-inner">\n' + toc_side, 1)
    a_end = t.find('</aside>', t.find('<aside class="art-sidebar sidebar">'))
    t = t[:a_end] + '</div>' + t[a_end:]
    t = finish(t, minutes)
    open(path, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))
    return f'ok (legacy): {minutes} min'


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, '->', convert(p))
