# Settings translations

The frontend owns its language independently of the dictation language. Choose
Automatic (system), English or Español under Advanced settings → Interface. Automatic first asks
SteamClient.Settings.GetCurrentLanguage(), with a bounded timeout. Steam names
spanish and latam map to Spanish. navigator.language is a fallback, never the
selected Whisper language. Unsupported languages fall
back to English. The override is stored locally in the renderer and does not
alter backend settings, profiles, language codes or recordings.

Catalogs are src/locales/en.json and es.json, keyed by the English source text.
Add UI strings through t(), not by embedding translated text in components.
Preserve placeholders such as {number}; never translate RPC names, model IDs,
button IDs or game names. Add a catalog and a selector option to support another
language. Missing entries safely fall back to English. Language display names
use Intl.DisplayNames with original names as fallback.

Settings, help, frontend status/fallback messages and frontend notifications are
covered. Raw backend error details, controller diagnostic payloads, custom user
preset names and the separate native recording overlay remain untranslated.

Physical test: switch to Español, navigate all pages with the D-pad, confirm
labels fit and Back works, select a transcription language and model, inspect
button/trash focus, run Test Dictation (no send), reopen QAM and confirm locale
persists. Changing interface language must not change transcription language.
Repeat with English and Automatic. This test build requires physical validation.
