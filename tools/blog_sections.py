"""Blog sections (categories). Each article in articles.json has a "section" key
that must be one of the slugs below. Pages are built at /blog/category/<slug>/."""

SECTIONS = [
    # slug, name, one-line description shown on the section page
    ('homes', 'تنظيف المنازل والفلل',
     'نصائح وأدلة لتنظيف البيوت والشقق والفلل والمجالس في الرياض، من التنظيف اليومي للتنظيف العميق.'),
    ('facilities', 'تنظيف المنشآت والشركات',
     'كيف تنظف المكاتب والمطاعم والمساجد والمدارس والمحلات، وجداول التنظيف وعقود المنشآت.'),
    ('water-tanks', 'تنظيف وعزل الخزانات',
     'علامات تلوث الخزان، وخطوات التنظيف والتعقيم، ومواد العزل ومتى تحتاج تعيد العزل.'),
    ('prices', 'أسعار التنظيف',
     'كيف تتحدد أسعار تنظيف الشقق والبيوت بالرياض، وإيش اللي يرفع أو ينزل السعر.'),
    ('choosing-a-company', 'دليل اختيار شركة التنظيف',
     'إيش تسأل قبل ما تحجز، وكيف تتأكد من الترخيص والضمان والتقييمات، وتختار الشركة الصح.'),
    ('pest-control', 'مكافحة الحشرات',
     'علامات الحشرات والنمل الأبيض في البيت، وليش ترجع بعد الرش، وكيف تمنعها.'),
]
SECTION_NAMES = {s: n for s, n, _ in SECTIONS}


def section_url(slug):
    return f'/blog/category/{slug}/'
