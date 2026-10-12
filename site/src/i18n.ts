import en from './i18n/en.json';
import es from './i18n/es.json';
import de from './i18n/de.json';
import fr from './i18n/fr.json';
import ja from './i18n/ja.json';
import ko from './i18n/ko.json';
import pl from './i18n/pl.json';
import pt from './i18n/pt.json';
import ru from './i18n/ru.json';
import zh from './i18n/zh.json';

export const dictionaries = { en, es, de, fr, ja, ko, pl, pt, ru, zh };
export const locales = ['en', 'es', 'de', 'fr', 'ja', 'ko', 'pl', 'pt', 'ru', 'zh'] as const;
export type Locale = typeof locales[number];
export const localeNames = { en: 'English', es: 'Español', de: 'Deutsch', fr: 'Français', ja: '日本語', ko: '한국어', pl: 'Polski', pt: 'Português', ru: 'Русский', zh: '简体中文' };

for (const locale of locales) {
  const keys = Object.keys(dictionaries[locale]).sort();
  if (JSON.stringify(keys) !== JSON.stringify(Object.keys(en).sort())) {
    throw new Error(`Incomplete translation: ${locale}`);
  }
}
