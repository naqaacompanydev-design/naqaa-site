"""Blog section pages + the section links bar + correct structured data on listing pages.

Usage: python3 tools/blog_categories.py
  - writes /blog/category/<slug>/index.html for every section in blog_sections.py
    (look and head taken from the current /blog/ page, so they match it exactly)
  - adds the section links bar under the hero of /blog/, /blog/page/N/ and the section pages
  - rewrites the JSON-LD of the listing pages so each describes itself
  - adds the section URLs to sitemap.xml
Idempotent. build_blog.py calls build_all() after rebuilding the blog pages.
"""
import html as H
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from blog_index_layout import date_line, reading_minutes  # noqa: E402
from blog_sections import SECTIONS, SECTION_NAMES, section_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.naqaa-cleaning.com'
BLOG_NAME = 'مدونة نقاء للتنظيف'


def card_html(a):
    return (f'<a href="{a["url"]}" class="blog-card-link"><article class="blog-card reveal">\n'
            f'<div class="blog-card-img"><img src="{a["img"]}" alt="{a["alt"]}" loading="lazy"></div>\n'
            '<div class="blog-card-body">\n'
            f'<span class="blog-cat">{a["cat"]}</span>\n'
            f'<h2 class="blog-card-title">{a["title"]}</h2>\n'
            f'<p class="blog-card-excerpt">{a["excerpt"]}</p>\n'
            f'{date_line(reading_minutes(a["url"]))}\n'
            '</div></article></a>')


def sections_bar(active, articles):
    counts = {s: 0 for s, _, _ in SECTIONS}
    for a in articles:
        if a.get('section') in counts:
            counts[a['section']] += 1
    items = [('الكل', '/blog/', len(articles), active is None)]
    items += [(n, section_url(s), counts[s], active == s) for s, n, _ in SECTIONS]
    links = ''.join(
        (f'<a href="{u}" aria-current="page" class="on">' if on else f'<a href="{u}">')
        + f'{n} <small>{c}</small></a>' for n, u, c, on in items)
    return f'<div class="blog-sections" role="navigation" aria-label="أقسام المدونة">{links}</div>\n'


def jsonld(name, url, desc, crumbs, items):
    blocks = [
        {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': BASE + url + '#page',
         'name': name, 'url': BASE + url, 'description': desc, 'inLanguage': 'ar',
         'isPartOf': {'@type': 'Blog', 'name': BLOG_NAME, 'url': BASE + '/blog/'}},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + u} for i, (n, u) in enumerate(crumbs)]},
        {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'url': BASE + a['url'], 'name': a['title']} for i, a in enumerate(items)]},
    ]
    return ''.join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, separators=(',', ':'))
                   + '\n</script>\n' for b in blocks)


def set_jsonld(t, ld):
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', t, flags=re.S)
    return t.replace('</head>', ld + '</head>', 1)


def set_bar(t, bar):
    t = re.sub(r'<div class="blog-sections".*?</div>(?:<script>.*?</script>)?\n', '', t, flags=re.S)
    return re.sub(r'(<section class="blog-paper"[^>]*>\n)', lambda m: m.group(1) + bar, t, count=1)


def listing_items(t, by_url):
    grid = t[t.index('<div class="blog-grid"'):]
    grid = grid[:grid.index('</div></div>')]
    return [by_url[u] for u in re.findall(r'<a href="([^"]+)" class="blog-card-link">', grid) if u in by_url]


def read(p):
    raw = open(p, encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def write(p, t, nl):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))


def fix_listing_pages(articles):
    by_url = {a['url']: a for a in articles}
    pages = [os.path.join(ROOT, 'blog', 'index.html')]
    pdir = os.path.join(ROOT, 'blog', 'page')
    if os.path.isdir(pdir):
        pages += [os.path.join(pdir, d, 'index.html') for d in sorted(os.listdir(pdir), key=lambda x: int(x) if x.isdigit() else 0)
                  if os.path.isfile(os.path.join(pdir, d, 'index.html'))]
    for p in pages:
        t, nl = read(p)
        n = 1 if p.endswith(os.path.join('blog', 'index.html')) else int(os.path.basename(os.path.dirname(p)))
        url = '/blog/' if n == 1 else f'/blog/page/{n}/'
        name = BLOG_NAME if n == 1 else f'{BLOG_NAME} - صفحة {n}'
        desc = re.search(r'<meta name="description" content="([^"]*)"', t).group(1)
        crumbs = [('الرئيسية', '/'), ('المدونة', '/blog/')] + ([(f'صفحة {n}', url)] if n > 1 else [])
        t = set_jsonld(t, jsonld(name, url, desc, crumbs, listing_items(t, by_url)))
        t = set_bar(t, sections_bar(None, articles))
        write(p, t, nl)
    return len(pages)


def build_category_pages(articles):
    base, nl = read(os.path.join(ROOT, 'blog', 'index.html'))
    out = []
    for slug, name, desc in SECTIONS:
        items = [a for a in articles if a.get('section') == slug]
        url = section_url(slug)
        title = f'{name} | {BLOG_NAME}'
        t = base
        t = re.sub(r'<title>.*?</title>', f'<title>{H.escape(title)}</title>', t, count=1)
        t = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + H.escape(desc), t, count=1)
        t = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + BASE + url, t, count=1)
        t = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + BASE + url, t, count=1)
        t = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + H.escape(title), t, count=1)
        t = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + H.escape(desc), t, count=1)
        t = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + H.escape(title), t, count=1)
        t = re.sub(r'(<meta name="twitter:description" content=")[^"]*', lambda m: m.group(1) + H.escape(desc), t, count=1)
        t = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', '', t)  # no English twin for sections
        crumbs = [('الرئيسية', '/'), ('المدونة', '/blog/'), (name, url)]
        t = set_jsonld(t, jsonld(name, url, desc, crumbs, items))
        t = re.sub(r'(<div class="bh-in"><h1>).*?(</h1>)', lambda m: m.group(1) + H.escape(name) + m.group(2), t, count=1, flags=re.S)
        g0 = t.index('<div class="blog-grid"')
        g1 = t.index('>', g0) + 1
        g2 = t.index('</div></div>', g1)
        t = t[:g1] + '\n'.join(card_html(a) for a in items) + '\n' + t[g2:]
        t = re.sub(r'<div class="pager".*?</div>\n?', '', t, count=1, flags=re.S)
        t = set_bar(t, sections_bar(slug, articles) + f'<p class="blog-section-intro">{H.escape(desc)}</p>\n')
        p = os.path.join(ROOT, 'blog', 'category', slug, 'index.html')
        write(p, t, nl)
        out.append((url, len(items)))
    return out


def update_sitemap(today=None):
    import datetime
    today = today or datetime.date.today().isoformat()
    p = os.path.join(ROOT, 'sitemap.xml')
    t, nl = read(p)
    t = re.sub(r'\n\s*<!-- blog sections -->.*?<!-- /blog sections -->', '', t, flags=re.S)
    entries = ''.join(f'\n  <url>\n    <loc>{BASE}{section_url(s)}</loc>\n    <lastmod>{today}</lastmod>\n'
                      '    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>' for s, _, _ in SECTIONS)
    t = t.replace('</urlset>', f'\n  <!-- blog sections -->{entries}\n  <!-- /blog sections -->\n</urlset>', 1)
    write(p, t, nl)


def build_all(articles=None, today=None):
    articles = articles or json.load(open(os.path.join(ROOT, 'articles.json'), encoding='utf-8'))
    unknown = sorted({a.get('section') for a in articles} - set(SECTION_NAMES))
    if unknown:
        raise SystemExit(f'articles.json: unknown "section" value(s): {unknown}. Use one of {list(SECTION_NAMES)}')
    n = fix_listing_pages(articles)
    cats = build_category_pages(articles)
    update_sitemap(today)
    return n, cats


if __name__ == '__main__':
    n, cats = build_all()
    print(f'listing pages updated: {n}')
    for u, c in cats:
        print(f'{u} -> {c} articles')
