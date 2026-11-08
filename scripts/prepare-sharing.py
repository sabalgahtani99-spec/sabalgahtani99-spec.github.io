from pathlib import Path
from html import escape, unescape
import json
from itertools import count as sequence
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
ORIGIN = 'https://sabalgahtani99-spec.github.io'
PORTAL = 'تقارير قسم الاشراف التربوي Asma'
VERSION = '20261108b'
COLLECTIONS = {
    'madrasati-reports': 'تقارير منصة مدرستي — الأيام الخمسة',
    'urgent-interventions': 'تقارير التدخلات العاجلة',
}

DATES = {
    'sunday': 'الأحد ١ نوفمبر ٢٠٢٦',
    'monday': 'الاثنين ٢ نوفمبر ٢٠٢٦',
    'tuesday': 'الثلاثاء ٣ نوفمبر ٢٠٢٦',
    'wednesday': 'الأربعاء ٤ نوفمبر ٢٠٢٦',
    'thursday': 'الخميس ٥ نوفمبر ٢٠٢٦',
}

def caption(path, text):
    if path == Path('index.html'):
        return PORTAL
    if len(path.parts) == 2 and path.parts[0] in COLLECTIONS:
        return COLLECTIONS[path.parts[0]]
    if len(path.parts) == 3 and path.parts[0] == 'madrasati':
        slug = path.parts[1]
        if slug.startswith('interventions-') and slug.split('-', 1)[1] in DATES:
            return 'تقرير متابعة مدارس التدخلات العاجلة — ' + DATES[slug.split('-', 1)[1]]
        day = slug.removesuffix('-brief')
        if day in DATES:
            return 'تقرير تفعيل منصة مدرستي — ' + DATES[day] + (' — مختصر' if slug.endswith('-brief') else '')
    match = re.search(r'<title\b[^>]*>(.*?)</title>', text, re.I | re.S)
    value = re.sub(r'<[^>]+>', '', match.group(1)) if match else 'التقرير'
    return ' '.join(unescape(value).split())

def report_row(slug, label):
    relative = Path('madrasati') / slug / 'index.html'
    file = ROOT / relative
    if not file.is_file():
        return ''
    title = caption(relative, file.read_text())
    url = f'/madrasati/{slug}/'
    return (
        '<article class="portal-report"><a href="' + url + '"><h3>' + escape(label) + '</h3></a>'
        '<button type="button" class="portal-copy" data-report-title="' + escape(title, quote=True) + '" '
        'data-report-url="' + url + '">نسخ رابط التقرير</button></article>'
    )

def collection_page(slug, title, subtitle, content, extra=''):
    brand = escape(PORTAL).replace(' Asma', ' <bdi dir="ltr">Asma</bdi>')
    page = (
        '<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(COLLECTIONS[slug]) + '</title>'
        '</head><body class="portal-hub"><header class="portal-hub-header"><a href="/">' + brand + '</a>'
        '<img src="/madrasati/assets/ministry.png" alt="وزارة التعليم"></header><main class="portal-hub-main">'
        '<a class="portal-back" href="/">العودة إلى الرئيسية</a><section class="portal-hub-hero"><h1>' + escape(title) + '</h1>'
        + ('<p>' + escape(subtitle) + '</p>' if subtitle else '') + '</section>' + content + extra + '</main>'
        '<footer class="portal-hub-footer">' + brand + '</footer></body></html>'
    )
    destination = ROOT / slug / 'index.html'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page)

def report_list():
    days = []
    for day, date in DATES.items():
        assert (ROOT / 'madrasati' / day / 'index.html').is_file(), 'Missing daily report: ' + day
        rows = report_row(day, 'التقرير الكامل') + report_row(day + '-brief', 'التقرير المختصر')
        days.append('<section class="portal-day" data-day="' + day + '"><h2>' + escape(date) + '</h2><div>' + rows + '</div></section>')
    extra = '<nav class="portal-related" aria-label="الإحصاءات والمقارنات">'
    for path, title in [('statistics', 'إحصائية منصة مدرستي'), ('comparison', 'مقارنة التقارير')]:
        if (ROOT / 'madrasati' / path / 'index.html').is_file():
            extra += '<a href="/madrasati/' + path + '/">' + title + '</a>'
    extra += '</nav>'
    collection_page('madrasati-reports', 'تقارير منصة مدرستي', 'الأحد ١ نوفمبر إلى الخميس ٥ نوفمبر ٢٠٢٦', '<div class="portal-day-grid">' + ''.join(days) + '</div>', extra)
    urgent = report_row('interventions', 'تقرير المتابعة الأساسي')
    for day in ['monday', 'tuesday', 'wednesday', 'thursday']:
        urgent += report_row('interventions-' + day, DATES[day])
    collection_page('urgent-interventions', 'تقارير التدخلات العاجلة', '', '<div class="portal-report-grid portal-urgent-grid">' + urgent + '</div>')
    cards = []
    for slug, title in COLLECTIONS.items():
        detail = 'الأحد إلى الخميس' if slug == 'madrasati-reports' else 'تقارير المتابعة لمدارس التدخلات العاجلة'
        cards.append('<article class="portal-report portal-collection-card"><a href="/' + slug + '/"><h3>' + escape(title) + '</h3><p>' + detail + '</p><b>فتح التقارير ←</b></a>'
                     '<button type="button" class="portal-copy" data-report-title="' + escape(title, quote=True) + '" data-report-url="/' + slug + '/">نسخ رابط المجموعة</button></article>')
    return '<section id="portal-report-list" class="portal-report-library"><h2>التقارير</h2><div class="portal-report-grid">' + ''.join(cards) + '</div></section>'

assert (ROOT / 'index.html').is_file()
archive_markup = report_list()
count = 0
for file in ROOT.rglob('*.html'):
    relative = file.relative_to(ROOT)
    text = file.read_text()
    title = caption(relative, text)
    route = '/' + str(relative.parent).strip('.') + '/' if relative.parent != Path('.') else '/'
    route = re.sub(r'/+', '/', route)
    url = ORIGIN + route
    if relative == Path('index.html'):
        brand = escape(PORTAL).replace(' Asma', ' <bdi dir="ltr">Asma</bdi>')
        text = re.sub(r'<h1>.*?</h1>', '<h1>' + brand + '</h1>', text, count=1, flags=re.S)
        text = re.sub(r'<footer\b[^>]*>.*?</footer>', '<footer>' + brand + '</footer>', text, count=1, flags=re.S)
        text = re.sub(r'<nav\b[^>]*class="quick"[^>]*>.*?</nav>', '', text, flags=re.S)
        text = re.sub(r'<a\b(?=[^>]*class="work")(?=[^>]*href="/madrasati/")[^>]*>.*?</a>', '', text, flags=re.S)
        numbers = sequence(1)
        text = re.sub(r'<a\b(?=[^>]*class="work")[^>]*>.*?</a>', lambda m: re.sub(r'<span>.*?</span>', '<span>' + str(next(numbers)).translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')) + '</span>', m.group(0), count=1, flags=re.S), text, flags=re.S)
        text = re.sub(r'<section\b[^>]*id="portal-report-list".*?</section>', '', text, flags=re.S)
        text = re.sub(r'<h2 class="portal-sites-title">.*?</h2>', '', text, flags=re.S)
        text = text.replace('<section class="works">', archive_markup + '<h2 class="portal-sites-title">المواقع والبرامج</h2><section class="works">', 1)
    text = re.sub(r'<title\b[^>]*>.*?</title>', '<title>' + escape(title) + '</title>', text, count=1, flags=re.I | re.S)
    text = re.sub(r'<meta\b(?=[^>]*(?:property|name)\s*=\s*["\'](?:og:[^"\']+|twitter:[^"\']+)["\'])[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<link\b(?=[^>]*rel\s*=\s*["\']canonical["\'])[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<script\b[^>]*id="portal-sharing-meta"[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    text = re.sub(r'<link\b[^>]*href="/portal-sharing-[^"]+\.css"[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<script\b[^>]*src="/portal-sharing-[^"]+\.js"[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    meta = json.dumps({'title': title, 'url': url, 'portal': relative == Path('index.html'), 'collection': relative.parent.name in COLLECTIONS}, ensure_ascii=False).replace('</', '<\\/')
    tags = (
        '<link rel="canonical" href="' + escape(url, quote=True) + '">'
        '<meta property="og:type" content="website">'
        '<meta property="og:title" content="' + escape(title, quote=True) + '">'
        '<meta property="og:site_name" content="' + escape(PORTAL, quote=True) + '">'
        '<meta property="og:url" content="' + escape(url, quote=True) + '">'
        '<meta name="twitter:card" content="summary">'
        '<meta name="twitter:title" content="' + escape(title, quote=True) + '">'
        '<script type="application/json" id="portal-sharing-meta">' + meta + '</script>'
        '<link rel="stylesheet" href="/portal-sharing-' + VERSION + '.css">'
        '<script src="/portal-sharing-' + VERSION + '.js" defer></script>'
    )
    if 'id="portal-sharing-meta"' not in text:
        if re.search(r'</head>', text, re.I):
            text = re.sub(r'</head>', lambda _: tags + '</head>', text, count=1, flags=re.I)
        else:
            text = re.sub(r'</title>', lambda _: '</title>' + tags, text, count=1, flags=re.I)
    file.write_text(text)
    count += 1
print(json.dumps({'sharing_pages': count, 'portal': ORIGIN, 'report_links': archive_markup.count('data-report-url=')}, ensure_ascii=False))
