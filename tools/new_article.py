"""Start a new blog article from blog_templates/article-template.html.

Usage (one line):
  python3 tools/new_article.py --slug water-tank-summer-riyadh \
      --title "تنظيف الخزان في الصيف: متى وليش؟" \
      --short-title "تنظيف الخزان في الصيف" \
      --description "وصف المقالة لجوجل (150 حرف تقريبًا)" \
      --excerpt "سطرين يظهروا تحت عنوان الكارت في المدونة" \
      --section water-tanks \
      --category "تنظيف الخزانات • نصائح الصيف" \
      --cover /path/to/cover.jpg --cover-alt "وصف الصورة"

What it does:
  - creates blog/<slug>/index.html from the template with the details filled in
  - copies the cover image into blog/<slug>/
  - adds the article at the top of articles.json (newest first)
Then write the article content in blog/<slug>/index.html (replace every TODO)
and run:  python3 build_blog.py
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))
from blog_sections import SECTION_NAMES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']


def main(argv=None):
    ap = argparse.ArgumentParser(description='Start a new Naqaa blog article')
    ap.add_argument('--slug', required=True, help='URL name in English, lowercase-with-dashes, e.g. water-tank-summer-riyadh')
    ap.add_argument('--title', required=True)
    ap.add_argument('--short-title', help='shorter title for the breadcrumb (default: the title)')
    ap.add_argument('--description', required=True, help='meta description for Google')
    ap.add_argument('--excerpt', required=True, help='short text under the card title on the blog page')
    ap.add_argument('--section', required=True, choices=list(SECTION_NAMES))
    ap.add_argument('--category', required=True, help='label on the card and article, e.g. "تنظيف الخزانات • نصائح"')
    ap.add_argument('--cover', required=True, help='cover image file (jpg/png/webp)')
    ap.add_argument('--cover-alt', required=True, help='describe the cover image')
    ap.add_argument('--date', help='YYYY-MM-DD (default: today)')
    a = ap.parse_args(argv)

    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', a.slug):
        sys.exit('slug: use lowercase English letters, digits and dashes only, e.g. water-tank-summer-riyadh')
    out_dir = os.path.join(ROOT, 'blog', a.slug)
    if os.path.exists(out_dir):
        sys.exit(f'blog/{a.slug}/ already exists')
    if not os.path.isfile(a.cover):
        sys.exit(f'cover image not found: {a.cover}')
    date = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
    short = a.short_title or a.title

    ext = os.path.splitext(a.cover)[1].lower()
    cover_name = a.slug.replace('-', '_') + '_1' + (ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg')
    tmpl = open(os.path.join(ROOT, 'blog_templates', 'article-template.html'), encoding='utf-8').read()
    tmpl = re.sub(r'<!--\n  قالب مقالة جديدة.*?-->\n', '', tmpl, count=1, flags=re.S)
    values = {
        'TITLE': a.title, 'SHORT_TITLE': short, 'SHORT_TITLE_URL': quote(short), 'DESCRIPTION': a.description,
        'SLUG': a.slug, 'COVER_JPG': cover_name, 'COVER_ALT': a.cover_alt, 'CATEGORY': a.category,
        'DATE': f'{MONTHS[date.month - 1]} {date.year}', 'DATE_ISO': date.isoformat(),
    }
    for k, v in values.items():
        safe = v.replace('"', '&quot;') if k not in ('SHORT_TITLE_URL',) else v
        tmpl = tmpl.replace('{{' + k + '}}', safe)
    left = re.findall(r'\{\{[A-Z_]+\}\}', tmpl)
    if left:
        sys.exit(f'template placeholders not filled: {sorted(set(left))}')

    os.makedirs(out_dir)
    shutil.copyfile(a.cover, os.path.join(out_dir, cover_name))
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(tmpl)

    path = os.path.join(ROOT, 'articles.json')
    raw = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    articles = json.loads(raw)
    articles.insert(0, {
        'url': f'/blog/{a.slug}/', 'img': f'/blog/{a.slug}/{cover_name}', 'alt': a.cover_alt,
        'cat': a.category, 'title': a.title, 'excerpt': a.excerpt,
        'date': f'📅 {MONTHS[date.month - 1]} {date.year}', 'section': a.section,
    })
    open(path, 'w', encoding='utf-8', newline='').write(
        json.dumps(articles, ensure_ascii=False, indent=2).replace('\n', nl) + (nl if raw.endswith('\n') else ''))

    print(f'created blog/{a.slug}/index.html and added it to articles.json')
    print('next: write the content (replace every TODO), then run:  python3 build_blog.py')


if __name__ == '__main__':
    main()
