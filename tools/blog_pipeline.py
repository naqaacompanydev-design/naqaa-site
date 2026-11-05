"""Checks and preparation steps that build_blog.py runs around the listing build.

prepare(articles)  -> before building the blog pages
  - every article in articles.json has a page, a valid "section", and no
    unfilled template placeholders ({{...}}) or TODO markers
  - new articles (not yet in the new layout): images -> WebP, FAQ structured
    data generated from the FAQ section, then the new article layout
finish(articles)   -> after building
  - every article URL is in sitemap.xml
  - every article page: one <h1>, new layout, related cards, images that exist
Both stop the build with a clear message when something is wrong.
"""
import datetime
import html as H
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import blog_article_layout  # noqa: E402
from blog_sections import SECTION_NAMES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.naqaa-cleaning.com'


def page_path(url):
    return os.path.join(ROOT, url.strip('/'), 'index.html')


def read(p):
    raw = open(p, encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def write(p, t, nl):
    open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl))


def fail(title, problems):
    print(f'\n✗ {title}:')
    for p in problems:
        print('   -', p)
    sys.exit(1)


# ---------------------------------------------------------------- images
def to_webp(src_file):
    """Create <name>.webp next to a jpg/png (max 1200px wide). Returns the webp path, or None."""
    try:
        from PIL import Image
    except ImportError:
        print('   ! Pillow is not installed (pip install pillow): images left as they are')
        return None
    out = os.path.splitext(src_file)[0] + '.webp'
    if os.path.exists(out):
        return out
    im = Image.open(src_file)
    im.load()
    if im.width > 1200:
        im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
    im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
    im.save(out, 'WEBP', quality=82, method=6)
    return out


def resolve(page, src):
    if src.startswith(('http:', 'https:', 'data:', '//')):
        return None
    from urllib.parse import unquote
    p = unquote(src.split('?')[0])
    return os.path.normpath(os.path.join(ROOT, p.lstrip('/')) if p.startswith('/') else os.path.join(os.path.dirname(page), p))


def webp_page_images(page, t):
    def swap(m):
        src = m.group(2)
        f = resolve(page, src)
        if not f or not re.search(r'\.(jpe?g|png)$', f, re.I) or not os.path.isfile(f):
            return m.group(0)
        if to_webp(f):
            return m.group(1) + re.sub(r'\.(jpe?g|png)$', '.webp', src, flags=re.I) + m.group(3)
        return m.group(0)
    return re.sub(r'(<img\b[^>]*?\ssrc=")([^"]+)(")', swap, t)


# ---------------------------------------------------------------- FAQ structured data
def faq_jsonld(t):
    qa = re.findall(r'<div class="faq-q">(.*?)</div>\s*<div class="faq-a">(.*?)</div>', t, re.S)
    t = re.sub(r'[ \t]*<script type="application/ld\+json">\s*\{"@context": ?"https://schema.org", ?"@type": ?"FAQPage".*?</script>\n?', '', t, flags=re.S)
    if not qa:
        return t
    clean = lambda s: H.unescape(re.sub(r'<[^>]+>', '', s)).strip()  # noqa: E731
    data = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': clean(q), 'acceptedAnswer': {'@type': 'Answer', 'text': clean(a)}} for q, a in qa]}
    block = '  <script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>\n'
    last = [m.end() for m in re.finditer(r'<script type="application/ld\+json">.*?</script>\n', t, re.S)]
    pos = last[-1] if last else t.index('</head>')
    return t[:pos] + block + t[pos:]


# ---------------------------------------------------------------- analytics
def analytics_snippets():
    """GTM + GA4 + Clarity + lead-click tracking, taken from the blog head template (single source)."""
    head, _ = read(os.path.join(ROOT, 'blog_templates', 'head.html'))
    a = head.index('<!-- Google Tag Manager -->')
    b = head.index('</script>', head.index('/* Lead tracking')) + len('</script>\n')
    noscript = re.search(r'<!-- Google Tag Manager \(noscript\) -->.*?\n', head).group(0)
    return head[a:b], noscript


def ensure_analytics(t):
    """Add the site's analytics to a page that is missing it (some blog pages lost it in an old upload)."""
    if 'G-VQ0QH8WEB9' in t:
        return t, False
    block, noscript = analytics_snippets()
    t = t.replace('<head>\n', '<head>\n' + block, 1)
    t = re.sub(r'(<body[^>]*>\n?)', lambda m: m.group(1) + noscript, t, count=1)
    return t, True


# ---------------------------------------------------------------- steps
def prepare(articles):
    problems = []
    for a in articles:
        url = a.get('url', '')
        p = page_path(url)
        if not re.fullmatch(r'/blog/[^/]+/', url):
            problems.append(f'{url!r}: url must look like /blog/<slug>/')
            continue
        if not os.path.isfile(p):
            problems.append(f'{url}: page blog{url[5:]}index.html is missing')
            continue
        if a.get('section') not in SECTION_NAMES:
            problems.append(f'{url}: "section" must be one of {list(SECTION_NAMES)} (got {a.get("section")!r})')
        for key in ('img', 'alt', 'cat', 'title', 'excerpt'):
            if not a.get(key):
                problems.append(f'{url}: "{key}" is empty in articles.json')
        t, _ = read(p)
        if '{{' in t:
            problems.append(f'{url}: template placeholders left: {sorted(set(re.findall(r"{{[A-Z_]+}}", t)))}')
        main = re.search(r'<main class="article-body">(.*?)</main>', t, re.S)
        if main and 'TODO' in re.sub(r'<!--.*?-->', '', main.group(1), flags=re.S):  # ignore the template's instructions comment
            problems.append(f'{url}: the article still has TODO text, write the content first')
    if problems:
        fail('articles.json / article pages need fixing', problems)

    converted, changed_json, tracked = [], False, []
    for a in articles:
        p = page_path(a['url'])
        t, nl = read(p)
        t, added = ensure_analytics(t)
        if added:
            write(p, t, nl)
            tracked.append(a['url'])
        if 'nq-art' in t:
            continue
        t = webp_page_images(p, t)
        t = faq_jsonld(t)
        write(p, t, nl)
        res = blog_article_layout.convert(p)
        if not res.startswith('ok'):
            fail('could not apply the article layout', [f'{a["url"]}: {res}'])
        converted.append(f'{a["url"]} ({res})')
        img = resolve(p, a['img'])
        if img and re.search(r'\.(jpe?g|png)$', img, re.I) and os.path.isfile(img) and to_webp(img):
            a['img'] = re.sub(r'\.(jpe?g|png)$', '.webp', a['img'], flags=re.I)
            changed_json = True
    if changed_json:
        path = os.path.join(ROOT, 'articles.json')
        raw = open(path, encoding='utf-8', newline='').read()
        nl = '\r\n' if '\r\n' in raw else '\n'
        open(path, 'w', encoding='utf-8', newline='').write(
            json.dumps(articles, ensure_ascii=False, indent=2).replace('\n', nl) + (nl if raw.endswith('\n') else ''))
    if tracked:
        print(f'✓ كود Google Analytics اتضاف لـ {len(tracked)} مقالة كانت ناقصاه')
    for c in converted:
        print('✓ مقالة جديدة اتجهزت:', c)
    return articles


def finish(articles, today=None):
    today = today or datetime.date.today().isoformat()
    # sitemap: add any article that is missing
    sp = os.path.join(ROOT, 'sitemap.xml')
    t, nl = read(sp)
    added = []
    for a in articles:
        loc = BASE + a['url']
        enc = BASE + '/'.join(__import__('urllib.parse', fromlist=['quote']).quote(s) for s in a['url'].split('/'))
        if f'<loc>{loc}</loc>' in t or f'<loc>{enc}</loc>' in t:
            continue
        t = t.replace('\n  <!-- blog sections -->', f'\n  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n'
                      '    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n  <!-- blog sections -->', 1)
        added.append(a['url'])
    if added:
        write(sp, t, nl)
        print('✓ اتضافت للـ sitemap:', ', '.join(added))

    problems = []
    for a in articles:
        p = page_path(a['url'])
        t, _ = read(p)
        if len(re.findall(r'<h1[\s>]', t)) != 1:
            problems.append(f'{a["url"]}: needs exactly one <h1>')
        if 'nq-art' not in t:
            problems.append(f'{a["url"]}: not in the new article layout')
        if 'G-VQ0QH8WEB9' not in t:
            problems.append(f'{a["url"]}: Google Analytics code missing')
        if 'class="art-related"' not in t:
            problems.append(f'{a["url"]}: related-article cards missing')
        for src in re.findall(r'<img\b[^>]*?\ssrc="([^"]+)"', t):
            f = resolve(p, src)
            if f and not os.path.isfile(f):
                problems.append(f'{a["url"]}: image not found: {src}')
        f = resolve(p, a['img'])
        if f and not os.path.isfile(f):
            problems.append(f'{a["url"]}: articles.json "img" not found: {a["img"]}')
    if problems:
        fail('final checks found problems', problems)
    print(f'✓ الفحص النهائي: {len(articles)} مقالة سليمة')
