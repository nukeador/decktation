import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
const source = readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const detection = source.slice(source.indexOf("if (currentLocale === 'en')"), source.indexOf('const copyButton'));
const supported = ['en','es','de','fr','ja','ko','pl','pt','ru','zh'];
function detect(languages, saved, currentLocale = 'en', blocked = false) {
  let destination;
  vm.runInNewContext(detection, {
    currentLocale, localeOptions: supported.map(value => ({value})),
    navigator: {languages, language: languages[0]},
    localStorage: {getItem(){if(blocked) throw Error('blocked');return saved;}},
    localeUrl: locale => locale,
    window: {location: {replace(locale){destination = locale;}}},
  });
  return destination;
}
test('regional and script variants select their supported base language', () => {
  for (const [tag, expected] of [['es-MX','es'],['es-AR','es'],['pt-BR','pt'],['pt-PT','pt'],['zh-Hant-TW','zh'],['ja-JP','ja'],['ko-KR','ko'],['de-AT','de'],['fr-CA','fr'],['pl-PL','pl'],['ru-RU','ru'],['PT_br','pt']]) assert.equal(detect([tag]), expected, tag);
});
test('browser preferences, explicit choice, unavailable storage and fallback', () => {
  assert.equal(detect(['ar-SA','fr-CA','es']), 'fr');
  assert.equal(detect(['es-MX'],'en'), undefined);
  assert.equal(detect(['es-MX'],'pt-PT'), 'pt');
  assert.equal(detect(['ar-SA'],'bad'), undefined);
  assert.equal(detect(['ja-JP'],undefined,'en',true), 'ja');
  assert.equal(detect(['fr-FR'],undefined,'es'), undefined);
  assert.equal(detect([]), undefined);
});
