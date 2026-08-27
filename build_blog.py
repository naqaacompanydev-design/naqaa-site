# -*- coding: utf-8 -*-
"""
build_blog.py
=============
سكريبت أوتوماتيك لبناء صفحات مدونة "نقاء" (blog/index.html و blog/page/N/index.html)
من ملف بيانات المقالات articles.json، مع ترقيم صفحات تلقائي (12 مقال في كل صفحة)
وتحديث sitemap.xml لوحده.

طريقة الاستخدام
----------------
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
       "date":    "📅 أغسطس 2026 • 15 دقيقة"   (النص زي ما هو هيظهر تحت الكارت)

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

# ============ إعدادات ============
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
ARTICLES_FILE = os.path.join(SITE_ROOT, "articles.json")
TEMPLATES_DIR = os.path.join(SITE_ROOT, "blog_templates")
BLOG_DIR = os.path.join(SITE_ROOT, "blog")
SITEMAP_FILE = os.path.join(SITE_ROOT, "sitemap.xml")

PER_PAGE = 12
BASE_URL = "https://www.naqaa-cleaning.com"

TITLE_P1 = "مدونة مؤسسة نقاء لخدمات للتنظيف | نصائح وإرشادات تنظيف احترافية"
DESC_P1 = ("مدونة مؤسسة نقاء للتنظيف دليلك الشامل لنصائح التنظيف الاحترافي بالسعودية "
           "استمتع بمعلومات قيمة من خبرائنا واستمتع بخصم 30% لفترة محدودة على كافة خدماتنا اتصل الآن:0545833481")
TITLE_PN = "مدونة مؤسسة نقاء للتنظيف | صفحة {n} من نصائح وإرشادات تنظيف احترافية"
DESC_PN = ("مدونة مؤسسة نقاء للتنظيف - صفحة {n} من دليلك الشامل لنصائح التنظيف الاحترافي "
           "في السعودية، مع خصم 40% لفترة محدودة على جميع خدماتنا.")

ARTICLE_CARD_TMPL = """<a href="{url}" class="blog-card-link"><article class="blog-card reveal">
<div class="blog-card-img"><img src="{img}" alt="{alt}" loading="lazy"></div>
<div class="blog-card-body">
<span class="blog-cat">{cat}</span>
<h2 class="blog-card-title">{title}</h2>
<p class="blog-card-excerpt">{excerpt}</p>
<div class="blog-date">{date}</div>
</div></article></a>"""


def page_url(n):
    return "/blog/" if n == 1 else f"/blog/page/{n}/"


def page_dir(n):
    return BLOG_DIR if n == 1 else os.path.join(BLOG_DIR, "page", str(n))


def build_pagination(current, total):
    parts = []
    if current > 1:
        parts.append(f'<a href="{page_url(current-1)}" title="الصفحة السابقة" class="pag-prev">‹ السابقة</a>')
    for p in range(1, total + 1):
        if p == current:
            parts.append(f'<span class="current">{p}</span>')
        else:
            parts.append(f'<a href="{page_url(p)}">{p}</a>')
    if current < total:
        parts.append(f'<a href="{page_url(current+1)}" title="الصفحة التالية" class="pag-next">التالية ›</a>')
    return "\n  ".join(parts)


def build_page_html(head_tmpl, middle, footer, page_num, total_pages, articles_slice, total_articles):
    title = TITLE_P1 if page_num == 1 else TITLE_PN.format(n=page_num)
    desc = DESC_P1 if page_num == 1 else DESC_PN.format(n=page_num)
    canonical = BASE_URL + page_url(page_num)

    head = (head_tmpl
            .replace("{{TITLE}}", title)
            .replace("{{DESC}}", desc)
            .replace("{{CANONICAL}}", canonical))

    cards = "\n".join(ARTICLE_CARD_TMPL.format(**a) for a in articles_slice)

    pagination = build_pagination(page_num, total_pages)
    page_info = f'<p class="blog-page-title">صفحة {page_num} من {total_pages} — {total_articles} مقال</p>'

    html = (head
            + middle
            + cards
            + "</div></div>\n"
            + f'<div class="pagination-wrap">\n  {pagination}\n</div>\n'
            + page_info + "\n"
            + footer)
    return html


def update_sitemap(total_pages):
    if not os.path.isfile(SITEMAP_FILE):
        print("⚠ ملف sitemap.xml مش موجود - اتخطى التحديث.")
        return
    xml = open(SITEMAP_FILE, encoding="utf-8").read()

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
                "    <lastmod>2026-08-12</lastmod>\n"
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

    open(SITEMAP_FILE, "w", encoding="utf-8").write(xml)
    print(f"✓ sitemap.xml اتحدّث ({total_pages - 1} صفحة ترقيم إضافية غير صفحة 1)")


def main():
    with open(ARTICLES_FILE, encoding="utf-8") as f:
        articles = json.load(f)
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
    print(f"\nتم. إجمالي {total_articles} مقال على {total_pages} صفحة/صفحات.")


if __name__ == "__main__":
    main()
