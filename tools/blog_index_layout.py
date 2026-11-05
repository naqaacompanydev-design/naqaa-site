"""Apply the light listing layout to Naqaa blog listing pages.

Usage: python3 tools/blog_index_layout.py blog/index.html blog/page/2/index.html ...

- adds body class "nq-blogidx" plus /assets/nq-blog.css and /assets/nq-blog.js
- wraps the cards + pagination in <section class="blog-paper">
- sets the default card style (data-card="1")
- replaces each card's "date • 40 min" line with the article's real reading
  time and a "read the article" cue
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from blog_article_layout import ICON_CLOCK, WPM, text_of  # noqa: E402

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
    t = f'{minutes} دقيقة قراءة' if minutes else 'مقال'
    return (f'<div class="blog-date"><span>{ICON_CLOCK}{t}</span>'
            '<span class="bd-more">اقرأ المقال</span></div>')


def convert(path, card='1'):
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
    t = t.replace('</head>', '<link rel="stylesheet" href="/assets/nq-blog.css">\n'
                  '<script src="/assets/nq-blog.js" defer></script>\n</head>', 1)
    open(path, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))
    return 'ok'


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, '->', convert(p))
