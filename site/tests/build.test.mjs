import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import test from 'node:test';

const dist = new URL('../dist/', import.meta.url);
const source = new URL('../src/', import.meta.url);
const locales = readdirSync(new URL('i18n/', source)).filter(name => name.endsWith('.json')).map(name => name.slice(0, -5));

test('localized pages contain working install, downloads, and asset links', () => {
  for (const locale of locales) {
    const route = locale === 'en' ? 'index.html' : `${locale}/index.html`;
    const page = readFileSync(new URL(route, dist), 'utf8');
    assert.match(page, new RegExp(`<html lang="${locale}"`));
    assert.ok(page.includes('https://decktation.com/Decktation.zip'));
    assert.ok(!page.includes('https://decktation.com/plugins.json'));
    assert.ok(!page.includes('custom-store'));
    assert.ok(page.includes('href="/downloads/"'));
    assert.ok(!page.includes('{{'));
    assert.ok(!page.includes('&lt;br&gt;'));
    for (const [, path] of page.matchAll(/(?:src|href)="(\/(?:assets|vendor)\/[^"?#]+|\/(?:styles\.css|app\.js))[^" ]*"/g)) {
      assert.ok(existsSync(new URL(path.slice(1), dist)), `Missing asset ${path} in ${route}`);
    }
    const localeData = JSON.parse(readFileSync(new URL(`i18n/${locale}.json`, source), 'utf8'));
    assert.ok(page.includes(localeData['seo.title']));
    for (const language of locales) assert.ok(page.includes(`hreflang="${language}"`));
  }
});

test('all translations have matching keys and the rendered page uses each content key', () => {
  const en = JSON.parse(readFileSync(new URL('i18n/en.json', source), 'utf8'));
  for (const locale of locales) {
    const translated = JSON.parse(readFileSync(new URL(`i18n/${locale}.json`, source), 'utf8'));
    assert.deepEqual(Object.keys(en).sort(), Object.keys(translated).sort(), locale);
  }
  const page = readFileSync(new URL('index.html', dist), 'utf8');
  for (const key of Object.keys(en)) {
    if (!/^(seo|copy|a11y)\./.test(key)) assert.ok(page.includes(`data-i18n="${key}"`), `Unused translation: ${key}`);
  }
});

test('canonical URLs, sitemap, and robots use the deployed site origin', () => {
  const base = process.env.SITE_BASE_URL || 'https://decktation.com';
  for (const locale of locales) {
    const route = locale === 'en' ? 'index.html' : `${locale}/index.html`;
    const suffix = locale === 'en' ? '/' : `/${locale}/`;
    assert.ok(readFileSync(new URL(route, dist), 'utf8').includes(`rel="canonical" href="${new URL(suffix, base)}"`));
  }
  assert.ok(readFileSync(new URL('robots.txt', dist), 'utf8').includes(`${base}/sitemap.xml`));
  const sitemap = readFileSync(new URL('sitemap.xml', dist), 'utf8');
  for (const locale of locales) assert.ok(sitemap.includes(`${base}${locale === 'en' ? '/' : `/${locale}/`}`));
});
