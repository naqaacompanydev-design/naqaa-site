# -*- coding: utf-8 -*-
"""
build_blog.py
=============
سكريبت أوتوماتيك لبناء صفحات مدونة "نقاء" (blog/index.html و blog/page/N/index.html)
من ملف بيانات المقالات articles.json، مع ترقيم صفحات تلقائي (12 مقال في كل صفحة)
وتحديث sitemap.xml لوحده.

طريقة الاستخدام
----------------
الطريقة المختصرة لمقالة جديدة (التفاصيل في CLAUDE.md):
   python3 tools/new_article.py --slug ... --title ... --section ... --cover ...
   (اكتب المحتوى مكان كل TODO في blog/<slug>/index.html)
   python3 build_blog.py

1. لما تضيف مقال جديد للمدونة:
   - جهز صورة ومجلد المقال العادي زي ما بتعمل دايمًا (blog/اسم-المقال/index.html + الصور).
   - افتح articles.json وضيف عنصر جديد (Object) في *أول* القائمة (عشان يظهر
     المقال الجديد الأول في المدونة). كل عنصر لازم يحتوي على المفاتيح دي بالظبط:
       "url":     "/blog/اسم-المقال-الجديد/"
       "img":     "/blog/اسم-المقال-الجديد/اسم-الصورة.jpg"
       "alt":     "النص البديل للصورة"
       "cat":     "التصنيف • كلمة مختصرة تانية"
       "title":   "عنوان المقال اللي هيظهر في الكارت"
       "excerpt": "الوصف المختصر اللي هيظهر تحت العنوان"
       "date":    "📅 أغسطس 2026"   (للتوثيق بس: وقت القراءة في الكارت بيتحسب لوحده من المقال)
       "section": "homes"   (القسم: homes / facilities / water-tanks / prices /
                             choosing-a-company / pest-control — من tools/blog_sections.py)

2. شغّل الأمر ده من نفس المجلد اللي فيه المدونة (مجلد الموقع الرئيسي):
       python3 build_blog.py

3. السكريبت هيعمل لوحده:
   - يحسب عدد الصفحات المطلوبة (12 مقال في كل صفحة).
   - يعيد كتابة blog/index.html (صفحة 1).
   - يعيد كتابة/ينشئ blog/page/2/، blog/page/3/... حسب الحاجة الفعلية.
   - يمسح أي صفحة ترقيم قديمة بقت زيادة عن اللزوم (لو قللت المقالات).
   - يحدّث sitemap.xml بحيث يعكس عدد صفحات المدونة الصحيح.

المتطلبات: Python 3 بس (مفيش أي مكتبات خارجية).
"""

import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from blog_index_layout import date_line, pagination_html, reading_minutes  # noqa: E402

# ============ إعدادات ============
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
ARTICLES_FILE = os.path.join(SITE_ROOT, "articles.json")
TEMPLATES_DIR = os.path.join(SITE_ROOT, "blog_templates")
BLOG_DIR = os.path.join(SITE_ROOT, "blog")
SITEMAP_FILE = os.path.join(SITE_ROOT, "sitemap.xml")

PER_PAGE = 12
BASE_URL = "https://www.naqaa-cleaning.com"

TITLE_P1 = "مدونة مؤسسة نقاء لخدمات للتنظيف | نصائح وإرشادات تنظيف احترافية"
DESC_P1 = ("مدونة مؤسسة نقاء للتنظيف: نصائح وإرشادات التنظيف الاحترافي في الرياض من خبرائنا. "
           "اتصل 0545833481.")
TITLE_PN = "مدونة مؤسسة نقاء للتنظيف | صفحة {n} من النصائح"
DESC_PN = ("مدونة مؤسسة نقاء للتنظيف - صفحة {n} من دليلك الشامل لنصائح التنظيف الاحترافي "
           "في السعودية.")

ARTICLE_CARD_TMPL = """<a href="{url}" class="blog-card-link"><article class="blog-card reveal">
<div class="blog-card-img"><img src="{img}" alt="{alt}" loading="lazy"></div>
<div class="blog-card-body">
<span class="blog-cat">{cat}</span>
<h2 class="blog-card-title">{title}</h2>
<p class="blog-card-excerpt">{excerpt}</p>
{date_html}
</div></article></a>"""


def page_url(n):
    return "/blog/" if n == 1 else f"/blog/page/{n}/"


def page_dir(n):
    return BLOG_DIR if n == 1 else os.path.join(BLOG_DIR, "page", str(n))


def build_pagination(current, total):
    return pagination_html(current, total, page_url)


def build_page_html(head_tmpl, middle, footer, page_num, total_pages, articles_slice, total_articles):
    title = TITLE_P1 if page_num == 1 else TITLE_PN.format(n=page_num)
    desc = DESC_P1 if page_num == 1 else DESC_PN.format(n=page_num)
    canonical = BASE_URL + page_url(page_num)

    head = (head_tmpl
            .replace("{{TITLE}}", title)
            .replace("{{DESC}}", desc)
            .replace("{{CANONICAL}}", canonical))

    # the reading time on each card is measured from the article itself
    cards = "\n".join(ARTICLE_CARD_TMPL.format(**a, date_html=date_line(reading_minutes(a["url"])))
                      for a in articles_slice)

    pagination = build_pagination(page_num, total_pages)

    html = (head
            + middle
            + cards
            + "</div></div>\n"
            + pagination + "\n"
            + "</section>\n"
            + footer)
    return html


def update_sitemap(total_pages):
    if not os.path.isfile(SITEMAP_FILE):
        print("⚠ ملف sitemap.xml مش موجود - اتخطى التحديث.")
        return
    raw = open(SITEMAP_FILE, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw else "\n"   # keep the file's line endings
    xml = raw.replace("\r\n", "\n")
    import datetime
    today = datetime.date.today().isoformat()

    # امسح كل مدخلات /blog/page/N/ القديمة
    xml = re.sub(
        r'\s*<url>\s*<loc>https://www\.naqaa-cleaning\.com/blog/page/\d+/</loc>.*?</url>',
        '', xml, flags=re.S)

    if total_pages > 1:
        entries = []
        for n in range(2, total_pages + 1):
            entries.append(
                "  <url>\n"
                f"    <loc>{BASE_URL}/blog/page/{n}/</loc>\n"
                f"    <lastmod>{today}</lastmod>\n"
                "    <changefreq>weekly</changefreq>\n"
                "    <priority>0.5</priority>\n"
                "  </url>"
            )
        block = "\n" + "\n".join(entries)
        # حطهم قبل قسم صفحات الخدمات (لو موجود) وإلا قبل </urlset>
        marker = "  <!-- صفحات الخدمات -->"
        if marker in xml:
            xml = xml.replace(marker, block + "\n" + marker, 1)
        else:
            xml = xml.replace("</urlset>", block + "\n</urlset>")

    open(SITEMAP_FILE, "w", encoding="utf-8", newline="").write(xml.replace("\n", eol))
    print(f"✓ sitemap.xml اتحدّث ({total_pages - 1} صفحة ترقيم إضافية غير صفحة 1)")


def main():
    with open(ARTICLES_FILE, encoding="utf-8") as f:
        articles = json.load(f)

    # check every article and prepare new ones (WebP images, FAQ data, new layout)
    import blog_pipeline
    articles = blog_pipeline.prepare(articles)
    total_articles = len(articles)

    head_tmpl = open(os.path.join(TEMPLATES_DIR, "head.html"), encoding="utf-8").read()
    middle = open(os.path.join(TEMPLATES_DIR, "middle.html"), encoding="utf-8").read()
    footer = open(os.path.join(TEMPLATES_DIR, "footer.html"), encoding="utf-8").read()

    total_pages = max(1, (total_articles + PER_PAGE - 1) // PER_PAGE)

    # امسح صفحات ترقيم قديمة زيادة عن اللزوم (لو قل عدد المقالات)
    old_page_root = os.path.join(BLOG_DIR, "page")
    if os.path.isdir(old_page_root):
        for name in os.listdir(old_page_root):
            try:
                n = int(name)
            except ValueError:
                continue
            if n > total_pages:
                shutil.rmtree(os.path.join(old_page_root, name))
                print(f"🗑 اتشالت صفحة ترقيم زيادة: page/{n}")

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PER_PAGE
        chunk = articles[start:start + PER_PAGE]
        html = build_page_html(head_tmpl, middle, footer, page_num,
                                total_pages, chunk, total_articles)
        out_dir = page_dir(page_num)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓ اتبنت صفحة {page_num} ({len(chunk)} مقال) -> {os.path.join(out_dir, 'index.html')}")

    update_sitemap(total_pages)

    # section pages (/blog/category/<slug>/), section links bar, listing JSON-LD,
    # and the related-article cards at the end of every article
    import blog_categories
    import blog_related
    n, cats = blog_categories.build_all(articles)
    print(f"✓ صفحات الأقسام: {len(cats)} قسم")
    by_url = {a["url"]: a for a in articles}
    for a in articles:
        blog_related.convert(os.path.join(SITE_ROOT, a["url"].strip("/"), "index.html"), articles, by_url)
    print("✓ المقالات ذات الصلة اتحدثت في كل المقالات")
    # sitemap entries for new articles + final checks on every article
    blog_pipeline.finish(articles)
    print(f"\nتم. إجمالي {total_articles} مقال على {total_pages} صفحة/صفحات.")


if __name__ == "__main__":
    main()
