"""Build dependency-free, localized static pages. Run: python3 site/build.py."""
from pathlib import Path
import html
import hashlib
import os
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'dist'
BASE_URL = os.environ.get('SITE_BASE_URL', 'https://silverfoxy.github.io/decktation').rstrip('/')
LOCALES = ['en', 'es']  # Only complete locales are published.
template = (ROOT / 'src/template.html').read_text()
asset_version = {name: hashlib.sha256((ROOT / 'public' / name).read_bytes()).hexdigest()[:10] for name in ['app.js', 'styles.css']}
source = json.loads((ROOT / 'src/i18n/en.json').read_text())
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
shutil.copytree(ROOT / 'public', OUTPUT)
for locale in LOCALES:
    strings = json.loads((ROOT / f'src/i18n/{locale}.json').read_text())
    if strings.keys() != source.keys():
        raise ValueError(f'Incomplete translation: {locale}')
    assets = '.' if locale == 'en' else '..'
    home = './' if locale == 'en' else '../'
    locale_names = {'en': 'English', 'es': 'Español'}
    url = BASE_URL + '/' + ('' if locale == 'en' else locale + '/')
    body = template.replace('{{LOCALE}}', locale)
    for key, value in strings.items():
        if key.startswith('seo.') or key.startswith('copy.') or key.startswith('a11y.'):
            continue
        # Translations are plain text, except the intentional hero line breaks.
        safe = html.escape(value).replace('&lt;br&gt;', '<br>')
        pattern = r'(<(?P<tag>[\w]+)\b[^>]*data-i18n="' + re.escape(key) + r'"[^>]*>).*?(</(?P=tag)>)'
        body, count = re.subn(pattern, lambda m: m[1] + safe + m[3], body, flags=re.S)
        if not count:
            raise ValueError(f'Unused translation: {key}')
    body = body.replace('{{DOWNLOADS_URL}}', html.escape(os.environ.get('SITE_DOWNLOADS_URL', BASE_URL + '/downloads/'))).replace('{{ASSETS}}', assets).replace('{{HOME}}', home)
    options = ''.join(f'<option value="{lang}" data-url="{home + ("" if lang == "en" else lang + "/")}"' + (' selected' if lang == locale else '') + f'>{locale_names[lang]}</option>' for lang in LOCALES)
    body = body.replace('{{LANGUAGE_OPTIONS}}', options)
    for token, key in [('LANGUAGE_LABEL', 'a11y.language'), ('MENU_LABEL', 'a11y.menu'), ('HERO_ALT', 'a11y.hero'), ('WOW_ALT', 'a11y.wow')]:
        body = body.replace('{{' + token + '}}', html.escape(strings[key]))
    links = ''.join(f'<link rel="alternate" hreflang="{lang}" href="{BASE_URL}/' + ('' if lang == 'en' else lang + '/') + '"/>' for lang in LOCALES)
    schema = {'@context':'https://schema.org','@type':'SoftwareApplication','name':'Decktation','operatingSystem':'SteamOS','applicationCategory':'UtilitiesApplication','url':BASE_URL+'/','isAccessibleForFree':True,'license':'https://github.com/silverfoxy/decktation/blob/master/LICENSE'}
    title = html.escape(strings['seo.title']); description = html.escape(strings['seo.description'])
    page = f'''<!doctype html><html lang="{locale}"><head><meta charset="utf-8"><script>(function(){{let t='auto';try{{t=localStorage.getItem('decktation-theme')||'auto';}}catch(e){{}}document.documentElement.dataset.theme=(t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme: dark)').matches))?'dark':'light';}})();</script><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><meta name="description" content="{description}"><link rel="canonical" href="{url}">{links}<link rel="alternate" hreflang="x-default" href="{BASE_URL}/"><meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE_URL}/assets/og-image.png"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{assets}/assets/decktation-logo.png"><link rel="stylesheet" href="{assets}/vendor/fontawesome/css/all.min.css"><link rel="stylesheet" href="{assets}/styles.css?v={asset_version['styles.css']}"><script type="application/ld+json">{json.dumps(schema)}</script><script src="{assets}/app.js?v={asset_version['app.js']}" defer></script></head><body data-copy-success="{html.escape(strings['copy.success'])}" data-copy-error="{html.escape(strings['copy.error'])}">{body}</body></html>'''
    destination = OUTPUT if locale == 'en' else OUTPUT / locale
    destination.mkdir(exist_ok=True)
    (destination / 'index.html').write_text(page)
(OUTPUT / '.nojekyll').touch()
(OUTPUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n')
(OUTPUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE_URL}/'+('' if lang == 'en' else lang+'/')+'</loc></url>' for lang in LOCALES) + '</urlset>')
print(f'Built {len(LOCALES)} static locales in {OUTPUT}')
