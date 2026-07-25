#!/usr/bin/env python3
import re
import os

ROOT = '/home/claude/fullsite/naqaa-site-main'

NAV_LI = '<li><a href="/pricing/" onclick="location.href=\'/pricing/\'" id="nav-pricing">الأسعار</a></li>'
MOBILE_A = '<a href="/pricing/" onclick="location.href=\'/pricing/\';toggleMenu()">الأسعار</a>'

FLOAT_BTN_TEMPLATE = (
    '<a href="/pricing/" class="phone-btn gold-pricing" title="احسب السعر" '
    'style="background:linear-gradient(135deg,#c9a84c,#e4bf6a)">'
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0a1628" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="4" y="3" width="16" height="18" rx="2"/><line x1="8" y1="7" x2="16" y2="7"/>'
    '<line x1="8" y1="11" x2="8" y2="11"/><line x1="12" y1="11" x2="12" y2="11"/>'
    '<line x1="16" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="8" y2="15"/>'
    '<line x1="12" y1="15" x2="12" y2="15"/><line x1="16" y1="15" x2="16" y2="15"/></svg></a>'
)

report = {'nav': [], 'nav_skip': [], 'mobile': [], 'mobile_skip': [], 'float': [], 'float_skip': []}

html_files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if fn == 'index.html' or fn.endswith('.html'):
            html_files.append(os.path.join(dirpath, fn))
        # skip the generator script itself, non-html files handled naturally

for fpath in sorted(html_files):
    rel = os.path.relpath(fpath, ROOT)
    with open(fpath, encoding='utf-8') as f:
        c = f.read()
    original = c
    changed = False

    # 1) Desktop + could-be-mobile nav-links <ul class="nav-links">...</ul>
    if 'id="nav-pricing"' in c:
        report['nav_skip'].append(rel + ' (موجودة بالفعل)')
    else:
        m = re.search(r'(<ul class="nav-links">)(.*?)(</ul>)', c, re.S)
        if m:
            new_inner = m.group(2) + '\n    ' + NAV_LI
            c = c[:m.start(2)] + new_inner + c[m.end(2):]
            changed = True
            report['nav'].append(rel)
        else:
            report['nav_skip'].append(rel + ' (مفيش nav-links)')

    # 2) Mobile menu link
    if 'الأسعار' in c and 'toggleMenu()">الأسعار' in c:
        report['mobile_skip'].append(rel + ' (موجودة بالفعل)')
    else:
        mm = re.search(r'(id="mobileMenu">)(.*?)(</div>)', c, re.S)
        if mm:
            new_inner = mm.group(2) + '\n  ' + MOBILE_A
            c = c[:mm.start(2)] + new_inner + c[mm.end(2):]
            changed = True
            report['mobile'].append(rel)
        else:
            report['mobile_skip'].append(rel + ' (مفيش mobileMenu شغالة)')

    # 3) Floating buttons - insert after the gold-btn (call) anchor, matching existing convention
    if 'gold-pricing' in c:
        report['float_skip'].append(rel + ' (موجودة بالفعل)')
    else:
        fm = re.search(r'(<a[^>]*class="phone-btn gold-btn"[^>]*>.*?</a>)', c, re.S)
        if fm:
            insertion = fm.group(1) + '\n  ' + FLOAT_BTN_TEMPLATE
            c = c[:fm.start(1)] + insertion + c[fm.end(1):]
            changed = True
            report['float'].append(rel)
        else:
            report['float_skip'].append(rel + ' (مفيش أزرار عائمة)')

    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(c)

print('=== تقرير التنفيذ ===')
print(f"رابط 'الأسعار' في الناف بار: أضيف في {len(report['nav'])} صفحة")
print(f"رابط في منيو الموبايل: أضيف في {len(report['mobile'])} صفحة")
print(f"الزرار العائم: أضيف في {len(report['float'])} صفحة")
print()
print('--- تفاصيل: الصفحات اللي اتضاف فيها الزرار العائم ---')
for r in report['float']:
    print(' ', r)
print()
print('--- تفاصيل: صفحات اتخطّاها الزرار العائم (مفيش أزرار عائمة أصلاً) ---')
for r in report['float_skip']:
    print(' ', r)
print()
print('--- صفحات اتخطّاها رابط منيو الموبايل (منيو مش شغالة) ---')
for r in report['mobile_skip']:
    print(' ', r)

import json
with open('/home/claude/sitewide_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
