"""Apply the light listing layout to Naqaa blog listing pages.

Usage: python3 tools/blog_index_layout.py blog/index.html blog/page/2/index.html ...

- adds body class "nq-blogidx" plus /assets/nq-blog.css
- wraps the cards + pagination in <section class="blog-paper">
- uses the full-image card style (data-card="3")
- replaces each card's "date • 40 min" line with the article's real reading
  time and a "read the article" cue
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from blog_article_layout import ICON_CLOCK, WPM, minutes_label, text_of  # noqa: E402
from blog_io import write_keep_eol  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def reading_minutes(url):
    path = os.path.join(ROOT, url.strip('/'), 'index.html')
    if not os.path.isfile(path):
        return None
    t = open(path, encoding='utf-8').read()
    m = re.search(r'<main class="article-body">(.*?)</main>', t, re.S)
    if not m:
        return None
    body = m.group(1)
    cut = body.find('<div class="cta-section')
    body = body[:cut] if cut > 0 else body
    # don't count the generated table of contents / booking card
    body = re.sub(r'<details class="art-toc.*?</details>|<aside class="art-book.*?</aside>', ' ', body, flags=re.S)
    return max(1, round(len(text_of(body).split()) / WPM))


def date_line(minutes):
    t = minutes_label(minutes) if minutes else 'مقال'
    return (f'<div class="blog-date"><span>{ICON_CLOCK}{t}</span>'
            '<span class="bd-more">اقرأ المقال</span></div>')


def convert(path, card='3'):
    raw = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    if 'nq-blogidx' in t:
        return 'skip (already converted)'

    def fix_card(m):
        card_html = m.group(0)
        url = m.group(1)
        return re.sub(r'<div class="blog-date">.*?</div>', lambda _: date_line(reading_minutes(url)), card_html, count=1, flags=re.S)
    t = re.sub(r'<a href="([^"]+)" class="blog-card-link">.*?</a>', fix_card, t, flags=re.S)

    start = t.find('<div class="container"><div class="blog-grid">')
    end_m = re.search(r'<p class="blog-page-title">.*?</p>\n', t)
    if start < 0 or not end_m:
        return 'FAIL: grid/pagination not found'
    t = (t[:start] + '<section class="blog-paper">\n'
         + t[start:end_m.end()].replace('<div class="blog-grid">', f'<div class="blog-grid" data-card="{card}">', 1)
         + '</section>\n' + t[end_m.end():])
    t = t.replace('<body class="nq-inner">', '<body class="nq-inner nq-blogidx">', 1)
    t = t.replace('</head>', '<link rel="stylesheet" href="/assets/nq-blog.css">\n</head>', 1)
    write_keep_eol(path, t, nl)
    return 'ok'


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, '->', convert(p))



HERO_BG = '/about/naqaa-cleaning-riyadh.webp'
HERO_HTML = ('<header class="bh"><div class="bh-bg" aria-hidden="true">'
             f'<img src="{HERO_BG}" alt="" fetchpriority="high" decoding="async"></div>'
             '<div class="bh-in"><h1>مدونة خبراء <span>نقاء</span></h1></div></header>\n')


CHEV_RIGHT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>')
CHEV_LEFT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>')


def blog_page_url(n):
    return '/blog/' if n == 1 else f'/blog/page/{n}/'


def pagination_html(current, total, page_url=blog_page_url):
    """RTL pager: previous (arrow right) · 1 … n-1 n n+1 … last · next (arrow left).
    On phones the numbers collapse to "n من total" so it stays on one line."""
    if current > 1:
        prev = (f'<a class="pg-prev" href="{page_url(current - 1)}" rel="prev">{CHEV_RIGHT}'
                '<span>السابقة</span></a>')
    else:
        prev = f'<span class="pg-prev is-off" aria-hidden="true">{CHEV_RIGHT}<span>السابقة</span></span>'
    if current < total:
        nxt = (f'<a class="pg-next" href="{page_url(current + 1)}" rel="next"><span>التالية</span>'
               f'{CHEV_LEFT}</a>')
    else:
        nxt = f'<span class="pg-next is-off" aria-hidden="true"><span>التالية</span>{CHEV_LEFT}</span>'
    show = sorted({1, total, current - 1, current, current + 1} & set(range(1, total + 1)))
    items, last = [], 0
    for p in show:
        if p - last > 1:
            items.append('<li class="pg-gap" aria-hidden="true">…</li>')
        if p == current:
            items.append(f'<li><span aria-current="page">{p}</span></li>')
        else:
            items.append(f'<li><a href="{page_url(p)}" aria-label="صفحة {p}">{p}</a></li>')
        last = p
    return ('<div class="pager" role="navigation" aria-label="صفحات المدونة">' + prev
            + '<ol class="pg-nums">' + ''.join(items) + '</ol>'
            + f'<span class="pg-count">صفحة <b>{current}</b> من {total}</span>' + nxt + '</div>')
