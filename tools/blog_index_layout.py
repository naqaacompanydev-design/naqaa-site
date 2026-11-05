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
    open(path, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))
    return 'ok'


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, '->', convert(p))


ICON_CALC = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><rect x="4" y="2.5" width="16" height="19" rx="3"/>'
             '<path d="M8 7h8"/><path d="M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/></svg>')
HERO_BG = '/about/naqaa-cleaning-riyadh.webp'


def build_hero(articles, total, variant='1', page_num=1):
    """Blog listing hero. variant: 1 featured article, 2 team photo, 3 compact."""
    import html as H
    first = articles[0]
    mins = reading_minutes(first['url'])
    crumb = ('<nav class="page-breadcrumb"><a href="/">الرئيسية</a> <span aria-hidden="true">←</span> '
             + ('<a href="/blog/">المدونة</a> <span aria-hidden="true">←</span> <span>صفحة %d</span>' % page_num
                if page_num > 1 else '<span>المدونة</span>') + '</nav>')
    title = 'مدونة <span>نقاء</span> للتنظيف'
    sub = 'أدلة أسعار، ونصائح تنظيف عملية، وطرق اختيار الشركة الصح، من خبرة فريق نقاء في بيوت ومنشآت الرياض.'
    stats = (f'<ul class="bh-stats"><li><b>{total}</b> مقال</li><li>أدلة أسعار <b>2026</b></li>'
             '<li>نصائح من <b>فريق نقاء</b></li></ul>')
    ctas = (f'<div class="bh-ctas"><a class="c1" data-nq="price" href="/pricing/">{ICON_CALC}احسب سعرك</a>'
            '<a class="c2" href="#blog-list">تصفح المقالات ↓</a></div>')
    feat = (f'<a class="bh-feat" href="{first["url"]}"><img src="{first["img"]}" alt="{H.escape(first["alt"])}" '
            'fetchpriority="high" decoding="async"><div class="bh-feat-b"><span class="bh-feat-tag">أحدث مقال</span>'
            f'<h2>{first["title"]}</h2><div class="bh-feat-m">{minutes_label(mins) if mins else ""}</div></div></a>')
    collage = '<div class="bh-collage" aria-hidden="true">' + ''.join(
        f'<img src="{a["img"]}" alt="" loading="lazy" decoding="async">' for a in articles[1:4]) + '</div>'
    bg = f'<div class="bh-bg" aria-hidden="true"><img src="{HERO_BG}" alt="" decoding="async"></div>'
    parts = {'1': feat, '2': '', '3': collage}
    return (f'<header class="bh" data-hero="{variant}">' + (bg if variant in ('2', 'all') else '')
            + '<div class="bh-in"><div class="bh-txt">' + crumb + '<span class="bh-eyebrow">المدونة</span>'
            + f'<h1>{title}</h1><p class="bh-sub">{sub}</p>' + stats
            + (ctas if variant in ('2', 'all') else '') + '</div>'
            + (feat + collage if variant == 'all' else parts.get(variant, '')) + '</div></header>\n')
