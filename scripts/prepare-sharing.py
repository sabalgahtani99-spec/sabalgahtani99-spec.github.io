from pathlib import Path
from html import escape, unescape
import json
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
ORIGIN = 'https://sabalgahtani99-spec.github.io'
PORTAL = 'بوابة أسماء القحطاني للتقارير'
VERSION = '20261108'

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

order = [
    'thursday', 'thursday-brief', 'wednesday', 'wednesday-brief',
    'interventions-wednesday', 'tuesday', 'tuesday-brief',
    'interventions-tuesday', 'monday', 'monday-brief',
    'interventions-monday', 'sunday',
]

def report_list():
    rows = []
    for slug in order:
        relative = Path('madrasati') / slug / 'index.html'
        file = ROOT / relative
        if not file.is_file():
            continue
        title = caption(relative, file.read_text())
        url = f'/madrasati/{slug}/'
        rows.append(
            '<article class="portal-report"><a href="' + url + '"><h3>' + escape(title) + '</h3></a>'
            '<button type="button" class="portal-copy" data-report-title="' + escape(title, quote=True) + '" '
            'data-report-url="' + url + '">نسخ رابط التقرير</button></article>'
        )
    return '<section id="portal-report-list" class="portal-report-library"><h2>تقارير المتابعة</h2><div class="portal-report-grid">' + ''.join(rows) + '</div></section>'

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
        text = text.replace('<h1>التقارير والبرامج التعليمية</h1>', '<h1>بوابة أسماء القحطاني<br><span class="portal-subtitle">التقارير والبرامج التعليمية</span></h1>')
        text = re.sub(r'<section\b[^>]*id="portal-report-list".*?</section>', '', text, flags=re.S)
        text = re.sub(r'<h2 class="portal-sites-title">.*?</h2>', '', text, flags=re.S)
        text = text.replace('<section class="works">', archive_markup + '<h2 class="portal-sites-title">المواقع والبرامج</h2><section class="works">', 1)
    text = re.sub(r'<title\b[^>]*>.*?</title>', '<title>' + escape(title) + '</title>', text, count=1, flags=re.I | re.S)
    text = re.sub(r'<meta\b(?=[^>]*(?:property|name)\s*=\s*["\'](?:og:[^"\']+|twitter:[^"\']+)["\'])[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<link\b(?=[^>]*rel\s*=\s*["\']canonical["\'])[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<script\b[^>]*id="portal-sharing-meta"[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    text = re.sub(r'<link\b[^>]*href="/portal-sharing-[^"]+\.css"[^>]*>', '', text, flags=re.I)
    text = re.sub(r'<script\b[^>]*src="/portal-sharing-[^"]+\.js"[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    meta = json.dumps({'title': title, 'url': url, 'portal': relative == Path('index.html')}, ensure_ascii=False).replace('</', '<\\/')
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
