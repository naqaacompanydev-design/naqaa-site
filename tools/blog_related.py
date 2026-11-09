"""Add (or refresh) the "related articles" image cards at the end of blog articles.

Usage: python3 tools/blog_related.py            # every article in articles.json
       python3 tools/blog_related.py blog/<slug>/index.html ...

Picks 3 articles: the hand-picked links already in the page's "مقالات ذات صلة"
list first, then the newest articles from the same section. The old text-only
list at the end of the article is replaced by the cards (sidebar lists stay).
Idempotent: re-running replaces the cards in place.
"""
import html as H
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from blog_article_layout import ICON_CLOCK, minutes_label  # noqa: E402
from blog_index_layout import reading_minutes  # noqa: E402
from blog_sections import SECTION_NAMES  # noqa: E402
from blog_io import write_keep_eol  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 3


def load_articles():
    return json.load(open(os.path.join(ROOT, 'articles.json'), encoding='utf-8'))


def matching_div_end(t, start):
    """Index just after the </div> that closes the <div ...> opening at `start`."""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', t[start:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return start + m.end()
    raise ValueError('unbalanced div')


def pick(url, page_html, articles, by_url):
    chosen = []
    # cards from an earlier run keep their picks (the hand-picked list is gone by then)
    prev = re.search(r'<section class="art-related".*?</section>', page_html, re.S)
    if prev:
        for u in re.findall(r'<a class="art-rel" href="([^"]+)"', prev.group(0)):
            if u in by_url and u != url and u not in chosen:
                chosen.append(u)
    end = page_html.find('class="end-links-grid"')
    scope = page_html[end:] if end >= 0 else page_html
    for href in re.findall(r'<div class="articles-mesh-grid">(.*?)</div>', scope, re.S)[:1]:
        for u in re.findall(r'href="([^"]+)"', href):
            if u in by_url and u != url and u not in chosen:
                chosen.append(u)
    sec = by_url[url].get('section') if url in by_url else None
    for a in articles:  # articles.json is newest first
        if len(chosen) >= N:
            break
        if a['url'] != url and a['url'] not in chosen and a.get('section') == sec:
            chosen.append(a['url'])
    for a in articles:
        if len(chosen) >= N:
            break
        if a['url'] != url and a['url'] not in chosen:
            chosen.append(a['url'])
    return chosen[:N]


def cards_html(urls, by_url):
    out = ['<section class="art-related" aria-labelledby="art-rel-h">'
           '<h2 class="art-related-h" id="art-rel-h">مقالات ممكن تهمك</h2><div class="art-rel-grid">']
    for u in urls:
        a = by_url[u]
        mins = reading_minutes(u)
        sec = SECTION_NAMES.get(a.get('section'), '')
        out.append(f'<a class="art-rel" href="{u}"><img src="{a["img"]}" alt="{H.escape(a["alt"])}" loading="lazy" decoding="async">'
                   f'<div class="art-rel-b">' + (f'<span class="art-rel-cat">{sec}</span>' if sec else '')
                   + f'<h3>{a["title"]}</h3>'
                   + (f'<span class="art-rel-m">{ICON_CLOCK}{minutes_label(mins)}</span>' if mins else '')
                   + '</div></a>')
    out.append('</div></section>\n')
    return ''.join(out)


def drop_old_list(t):
    """Remove the text-only related list inside .end-links-grid (and the grid if left empty)."""
    g = t.find('<div class="end-links-grid">')
    if g < 0:
        return t
    g_end = matching_div_end(t, g)
    grid = t[g:g_end]
    m = re.search(r'<div class="sidebar-card[^"]*"[^>]*>\s*<div class="sidebar-card-head"><h4>[^<]*مقالات ذات صلة[^<]*</h4>', grid)
    if not m:
        return t
    s = g + m.start()
    e = matching_div_end(t, s)
    t = t[:s] + t[e:]
    g_end = matching_div_end(t, g)
    if not re.sub(r'\s+', '', t[g + len('<div class="end-links-grid">'):g_end - len('</div>')]):
        line_start = t.rfind('\n', 0, g) + 1
        comment = t.rfind('<!-- RELATED ARTICLES SECTION -->', 0, g)
        if comment >= 0 and t[comment:g].strip().startswith('<!--') and t[comment:g].count('\n') <= 1:
            line_start = comment
        t = t[:line_start] + t[g_end:].lstrip('\n')
    return t


def convert(path, articles, by_url):
    raw = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    url = '/' + rel[:-len('index.html')]
    if url not in by_url:
        return 'skip (not in articles.json)'
    urls = pick(url, t, articles, by_url)
    t = re.sub(r'<section class="art-related".*?</section>\n?', '', t, flags=re.S)
    t = drop_old_list(t)
    main_end = t.find('</main>')
    if main_end < 0:
        return 'FAIL: no </main>'
    t = t[:main_end] + cards_html(urls, by_url) + t[main_end:]
    write_keep_eol(path, t, nl)
    return 'ok: ' + ', '.join(u.split('/')[2] for u in urls)


if __name__ == '__main__':
    arts = load_articles()
    by = {a['url']: a for a in arts}
    paths = sys.argv[1:] or [os.path.join(ROOT, a['url'].strip('/'), 'index.html') for a in arts]
    for p in paths:
        print(os.path.relpath(p, ROOT), '->', convert(p, arts, by))
