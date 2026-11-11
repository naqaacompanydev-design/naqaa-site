#!/usr/bin/env python3
"""Build the English legal pages (/en/terms/, /en/privacy/, /en/refund/, /en/accessibility/).

Layout and styles come from the Arabic page (terms.html, ...); header, footer and contact bar
come from the English site (en/services/index.html); the English text lives in PAGES below.
After changing an Arabic legal page, update the matching English text here and run:

    python3 tools/build_legal_en.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.naqaa-cleaning.com'
WA = ('https://wa.me/966545833481?text=' +
      'Hello%2C%20I%20have%20a%20question%20about%20your%20policies')

PAGES = {
    'terms': {
        'src': 'terms.html', 'ar_url': '/terms', 'tag': '📋 Terms & Conditions', 'h1': 'Terms of Use',
        'title': 'Terms & Conditions | Naqaa Cleaning',
        'desc': 'Terms and conditions of Naqaa Cleaning in Riyadh: how we handle service requests, pricing, '
                'payment, liability and changes to these terms.',
        'lead': 'Please read these terms carefully before using our services or dealing with us.',
        'updated': 'November 2026',
        'sections': [
            ('Acceptance of the terms',
             '<p>By using the Naqaa Cleaning website or requesting any of our services, you confirm that you have '
             'read these terms and agree to them in full. If you do not agree with any part of them, please do not '
             'use the website.</p>'),
            ('Scope of services',
             '<p>Naqaa Cleaning provides professional cleaning for homes, villas, companies, mosques and majlis '
             'rooms, including:</p>'
             '<ul><li>Home, villa and palace cleaning</li><li>Water tank cleaning and insulation</li>'
             '<li>AC and curtain cleaning</li><li>Pest and rodent control</li>'
             '<li>Steam cleaning for majlis seating and sofas</li>'
             '<li>Nano protection for majlis seating (VIP service)</li></ul>'),
            ('Accuracy of information',
             '<p>The customer undertakes to give correct and accurate details when requesting a service or '
             'contacting us. The customer is fully responsible for any incorrect information, and the '
             'establishment may decline the service if false details are found.</p>'),
            ('Pricing and payment',
             '<p>Prices are set according to the type of service, the size of the place and the details of the '
             'request. We offer:</p>'
             '<ul><li>Offers and discounts for monthly and annual contracts (20% off annual contracts)</li>'
             '<li>Cash payment after the service is done</li>'
             '<li>Bank transfer in advance for contracts</li></ul>'),
            ('Limits of liability',
             '<p>The establishment works to the highest standards of quality and safety. However, it:</p>'
             '<ul><li>Is not responsible for damage caused by incorrect information from the customer</li>'
             '<li>Is not responsible for damage that exceeds the value of the service provided</li>'
             '<li>Commits to redoing the service free of charge if you are not satisfied with the quality</li></ul>'),
            ('Intellectual property',
             '<p>All content on this website, including text, images, design and the logo, is fully owned by '
             'Naqaa Cleaning. It may not be copied, republished or used in any form without prior written '
             'permission.</p>'),
            ('Changes to the terms',
             '<p>The establishment may change these terms at any time without prior notice. Continuing to use the '
             'website after the changes are published means you accept the updated terms.</p>'),
        ],
    },
    'privacy': {
        'src': 'privacy.html', 'ar_url': '/privacy', 'tag': '🔒 Privacy', 'h1': 'Privacy Policy',
        'title': 'Privacy Policy | Naqaa Cleaning',
        'desc': 'Privacy policy of Naqaa Cleaning in Riyadh: what information we collect, how we use it, cookies '
                'and analytics, data protection and your rights.',
        'lead': 'We respect your privacy and are committed to protecting your personal data.',
        'updated': 'September 2026',
        'sections': [
            ('Information we collect',
             '<p>When you contact us or request a service, we may collect the following:</p>'
             '<ul><li>Full name</li><li>Phone number</li><li>Email address (if provided)</li>'
             '<li>Address of the service location, or the city</li>'
             '<li>The type of service requested and its details</li>'
             '<li>Device and browser data (performance analytics)</li></ul>'),
            ('How we use the information',
             '<p>We use your data only for the following purposes:</p>'
             '<ul><li>Contacting you and confirming your booking</li>'
             '<li>Scheduling the visit and carrying out the service</li>'
             '<li>Sending offers and updates, with your consent</li>'
             '<li>Improving our services and the user experience</li>'
             '<li>Complying with legal requirements in the Kingdom of Saudi Arabia</li></ul>'),
            ('Sharing data with third parties',
             '<p>We do not sell your data or share it with any outside party, except where necessary:</p>'
             '<ul><li>Technical service providers, such as website hosting and Google analytics and advertising '
             'services, under confidentiality agreements</li>'
             '<li>Government and legal authorities when the law requires it</li></ul>'),
            ('Cookies',
             '<p>The website uses cookies (small text files saved in your browser) to understand how the site is '
             'used and to improve it. They include:</p>'
             '<ul><li><strong>Google Analytics:</strong> to know the number of visitors, the most visited pages, '
             'where visits come from, the device type and the approximate city. This data is statistical and does '
             'not include your name or phone number.</li>'
             '<li><strong>Google Ads and Google Tag Manager:</strong> to measure how our Google ads perform and '
             'whether a visit came from an ad.</li>'
             '<li><strong>Microsoft Clarity:</strong> to understand how visitors browse the site (such as where '
             'they click and scroll) through heatmaps and anonymous session recordings, so we can make the site '
             'easier to use. Clarity automatically hides anything you type into forms, such as your name and '
             'phone number.</li></ul>'
             '<p>This data is processed by Google under '
             '<a href="https://policies.google.com/technologies/partner-sites?hl=en" target="_blank" '
             'rel="noopener">Google\'s policy on data use on partner sites</a>, and by Microsoft under the '
             '<a href="https://privacy.microsoft.com/en-us/privacystatement" target="_blank" rel="noopener">'
             'Microsoft Privacy Statement</a>.</p>'
             '<p>You can control cookies in any of these ways:</p>'
             '<ul><li>Delete or block them in your browser settings</li>'
             '<li>Install the <a href="https://tools.google.com/dlpage/gaoptout?hl=en" target="_blank" '
             'rel="noopener">Google Analytics opt-out add-on</a> in your browser</li>'
             '<li>Control personalised ads in <a href="https://adssettings.google.com/" target="_blank" '
             'rel="noopener">Google Ads Settings</a></li></ul>'
             '<p>Turning cookies off does not stop you from browsing the site, contacting us or requesting a '
             'service.</p>'),
            ('Data protection and security',
             '<p>We take suitable technical and organisational measures to protect your data from unauthorised '
             'access, loss or misuse, including encryption and HTTPS.</p>'),
            ('Your rights',
             '<p>At any time, you may:</p>'
             '<ul><li>Ask to see the data we hold about you</li><li>Ask us to correct any inaccurate data</li>'
             '<li>Ask us to delete your data permanently</li>'
             '<li>Withdraw your consent to receive marketing messages</li></ul>'),
            ('Contact about privacy',
             '<p>For any question or request about your privacy, please contact us directly on WhatsApp or by '
             'phone using the number on the website, and we will reply within 24 hours.</p>'),
        ],
    },
    'refund': {
        'src': 'refund.html', 'ar_url': '/refund', 'tag': '↩️ Cancellation & Refunds',
        'h1': 'Cancellation & Refund Policy',
        'title': 'Cancellation & Refund Policy | Naqaa Cleaning',
        'desc': 'Cancellation and refund policy of Naqaa Cleaning in Riyadh: free cancellation before the team '
                'arrives, rescheduling, the redo guarantee and contracts.',
        'lead': 'We give you full flexibility in managing your bookings, and your right to quality is guaranteed.',
        'updated': 'November 2026',
        'sections': [
            ('Cancelling before the team arrives',
             '<p>You can cancel a booked service at any time before the team arrives, with no fees or penalties, '
             'by phone or WhatsApp. We appreciate being told as early as possible so we can offer the slot to '
             'another customer.</p>'),
            ('Changing the appointment',
             '<p>You may reschedule the appointment once, free of charge. Further changes may need the team\'s '
             'approval, depending on availability.</p>'),
            ('Cancelling after the team arrives',
             '<p>We confirm the price before we start. If the size or condition of the place is different from '
             'the booking, the supervisor tells you the updated price before work begins, and you are free to '
             'accept it or cancel.</p>'
             '<ul><li>Cancelling after the team arrives and before work begins costs a fee of 30 SAR only</li>'
             '<li>If work has started and you ask us to stop, the part actually completed is charged, by '
             'agreement between the customer and the establishment</li>'
             '<li>Amounts paid in advance for the completed part cannot be refunded</li></ul>'),
            ('Quality guarantee and redoing the service',
             '<p>Customer satisfaction is our top priority. If you are not satisfied with the quality of the '
             'service:</p>'
             '<ul><li>We redo the service free of charge within 48 hours of the complaint</li>'
             '<li>A specialised team is sent to deal with any issue</li>'
             '<li>Pest and rodent control comes with a 6-month warranty</li></ul>'),
            ('Monthly and annual contracts',
             '<p>For recurring service contracts:</p>'
             '<ul><li>The contract can be cancelled with 30 days\' written notice</li>'
             '<li>Amounts paid in advance are refunded after deducting the services actually provided</li>'
             '<li>There are no extra fees for cancelling within the notice period</li></ul>'),
            ('Complaints',
             '<p>To make a complaint or ask for a refund, please contact us on WhatsApp or by phone, and tell '
             'us:</p>'
             '<ul><li>The customer\'s name and the date of the service</li>'
             '<li>A description of the problem or the reason for the request</li>'
             '<li>Any supporting photos or documents</li></ul>'),
        ],
    },
    'accessibility': {
        'src': 'accessibility.html', 'ar_url': '/accessibility', 'tag': '♿ Accessibility',
        'h1': 'Accessibility Policy',
        'title': 'Accessibility Policy | Naqaa Cleaning',
        'desc': 'Accessibility policy of Naqaa Cleaning: our commitment to a website that is easy to use for '
                'every visitor, in line with the WCAG 2.1 guidelines.',
        'lead': 'We are committed to making our website easy to use for every visitor, in line with WCAG 2.1.',
        'updated': 'January 2026',
        'sections': [
            ('Our commitment to accessibility',
             '<p>Naqaa Cleaning is committed to an inclusive, easy-to-use digital experience for all visitors, '
             'including people with disabilities, in line with the international WCAG 2.1 guidelines.</p>'),
            ('Accessible design standards',
             '<p>Our website is designed to provide:</p>'
             '<ul><li>High colour contrast for easy reading (a contrast ratio above 4.5:1)</li>'
             '<li>Flexible font sizes that can be enlarged</li><li>Full keyboard navigation</li>'
             '<li>Alternative text (alt text) for all meaningful images</li>'
             '<li>A clear, logical heading structure (H1 to H6)</li></ul>'),
            ('Device and browser support',
             '<p>The website works with:</p>'
             '<ul><li>All devices (phone, computer and tablet)</li>'
             '<li>The latest versions of the main browsers (Chrome, Safari, Firefox and Edge)</li>'
             '<li>Common screen readers</li></ul>'),
            ('Arabic and English support',
             '<p>The website is built to support both Arabic and English, including:</p>'
             '<ul><li>Right-to-left layout on Arabic pages and left-to-right layout on English pages</li>'
             '<li>Fonts chosen for comfortable reading (Cairo)</li>'
             '<li>Numbers and formatting that work in both languages</li></ul>'),
            ('Feedback and help',
             '<p>If you have any difficulty reaching any part of our website or digital services, please contact '
             'us right away. We commit to replying and dealing with any technical issue within 48 working '
             'hours.</p>'),
            ('Continuous improvement',
             '<p>We review our accessibility standards regularly and keep working to improve the experience for '
             'all users. Last full accessibility review: January 2026.</p>'),
        ],
    },
}


def read(rel):
    raw = open(os.path.join(ROOT, rel), encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def region(t, start, end, include_end=True):
    a = t.index(start)
    b = t.index(end, a) + (len(end) if include_end else 0)
    return a, b


def alternates(ar_url, en_url):
    return (f'<link rel="alternate" hreflang="ar" href="{BASE}{ar_url}">\n'
            f'<link rel="alternate" hreflang="en" href="{BASE}{en_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{BASE}{ar_url}">\n')


def body_html(pg):
    out = ['<!-- LEGAL HERO -->', '<div class="legal-hero">', '  <div class="container">',
           f'    <div class="legal-hero-tag">{pg["tag"]}</div>', f'    <h1>{pg["h1"]}</h1>',
           f'    <p>{pg["lead"]}</p>', '  </div>', '</div>', '',
           '<!-- LEGAL BODY -->', '<div class="legal-body">', '  <div class="legal-container">',
           '    <div class="legal-card">', '']
    for i, (title, html) in enumerate(pg['sections'], 1):
        out += ['      <div class="legal-section">',
                f'        <h2><span class="sec-num">{i}</span>{title}</h2>',
                '        ' + html, '      </div>']
    out += ['', '      <div class="legal-contact-strip">',
            '        <p>Have a question? Our team is available around the clock to answer you.</p>',
            f'        <a href="{WA}" class="btn-gold" target="_blank" rel="noopener">💬 Contact us</a>',
            '      </div>', '',
            '      <div class="legal-last-updated">',
            f'        Last updated: <span>{pg["updated"]}</span>. All rights reserved to <span>Naqaa Cleaning</span>',
            '      </div>', '    </div>', '  </div>', '</div>', '', '']
    return '\n'.join(out)


def build_one(slug, pg, ref):
    en_url = f'/en/{slug}/'
    t, _ = read(pg['src'])
    title, desc = pg['title'], pg['desc']

    # ---------------- head ----------------
    t = re.sub(r'<html lang="ar" dir="rtl">', '<html lang="en" dir="ltr">', t, count=1)
    t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, count=1, flags=re.S)
    for name, val in [('description', desc), ('author', 'Naqaa Cleaning Establishment'),
                      ('twitter:title', title), ('twitter:description', desc)]:
        t = re.sub(rf'(<meta name="{name}" content=")[^"]*', lambda m, v=val: m.group(1) + v, t, count=1)
    for prop, val in [('og:title', title), ('og:description', desc), ('og:site_name', 'Naqaa Cleaning Establishment'),
                      ('og:url', BASE + en_url), ('og:locale', 'en_US')]:
        t = re.sub(rf'(<meta property="{prop}" content=")[^"]*', lambda m, v=val: m.group(1) + v, t, count=1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + BASE + en_url, t, count=1)
    t = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', '', t)
    t = re.sub(r'[ \t]*<meta name="keywords" content="[^"]*">\n?', '', t)
    t = re.sub(r'[ \t]*(<!-- JSON-LD[^>]*-->\s*)?<script type="application/ld\+json">.*?</script>\n?', '', t, flags=re.S)
    ld = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': pg['h1'], 'description': desc,
          'url': BASE + en_url, 'inLanguage': 'en',
          'isPartOf': {'@type': 'WebSite', 'name': 'Naqaa Cleaning', 'url': BASE + '/en/'}}
    ltr_css = ('<style id="legal-ltr">/* English page: left-to-right layout */body{direction:ltr}'
               '.legal-section ul li{padding-right:0;padding-left:20px}.legal-section ul li::before{right:auto;left:0}'
               '@media(min-width:1000px) and (max-width:1399px){html[dir=ltr] body .nq-nav{gap:14px}html[dir=ltr] body .nq-nav a{font-size:14px}}'
               '@media(min-width:1000px) and (max-width:1149px){html[dir=ltr] body .nq-nav{gap:10px}html[dir=ltr] body .nq-nav a{font-size:13px}html[dir=ltr] body .nq-call{padding-inline:14px}}'
               '</style>\n')
    t = t.replace('</head>', alternates(pg['ar_url'], en_url) +
                  '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=1) +
                  '\n</script>\n' + ltr_css + '</head>', 1)

    # ---------------- header / menu (from the English site) ----------------
    a, _b = region(t, '<header id="nq-hdr">', '\n', include_end=False)
    b = t.index('<!-- LEGAL HERO -->', a)
    ra, _rb = region(ref, '<header id="nq-hdr">', '\n', include_end=False)
    rb = ref.index('\n', ref.index('</nav><div id="navbar"', ra)) + 1
    t = t[:a] + ref[ra:rb] + '\n' + t[b:]

    # ---------------- content ----------------
    a = t.index('<!-- LEGAL HERO -->')
    b = t.index('<footer id="nq-footer">')
    t = t[:a] + body_html(pg) + t[b:]

    # ---------------- footer + contact bar (from the English site) ----------------
    for start, end in [('<footer id="nq-footer">', '</footer>'), ('<div id="nq-fbar"', '</div>')]:
        a, b = region(t, start, end)
        ra, rb = region(ref, start, end)
        t = t[:a] + ref[ra:rb] + t[b:]
    # "Arabic version" links copied from the reference page -> this page's Arabic version
    t = re.sub(r'href="/services/"((?: class="[^"]*")? hreflang="ar")', rf'href="{pg["ar_url"]}"\1', t)

    body = t[t.index('<body'):]
    body = re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S)
    left = sorted({m.group(0) for m in re.finditer(r'[؀-ۿ][؀-ۿ ]{3,}', re.sub(r'lang="ar">[^<]*<', '', body))})
    if left:
        print(f'  note: Arabic text left in /en/{slug}/:', left[:5])

    out = os.path.join(ROOT, 'en', slug, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(t)
    print('wrote', os.path.relpath(out, ROOT))


def link_arabic_page(pg, slug):
    """Make sure the Arabic page declares its English pair (hreflang)."""
    path = os.path.join(ROOT, pg['src'])
    raw = open(path, encoding='utf-8', newline='').read()
    if 'hreflang="en"' in raw[:raw.find('</head>')]:
        return
    nl = '\r\n' if '\r\n' in raw else '\n'
    block = alternates(pg['ar_url'], f'/en/{slug}/').replace('\n', nl)
    raw = re.sub(r'(<link rel="canonical" href="[^"]*">\r?\n)', lambda m: m.group(1) + block, raw, count=1)
    open(path, 'w', encoding='utf-8', newline='').write(raw)
    print('linked', pg['src'], '-> English version')


def build():
    ref, _ = read('en/services/index.html')
    for slug, pg in PAGES.items():
        build_one(slug, pg, ref)
        link_arabic_page(pg, slug)


if __name__ == '__main__':
    build()
