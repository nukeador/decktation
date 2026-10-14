# Spoken punctuation (issue #2)

Issue [#2](https://github.com/silverfoxy/decktation/issues/2) reports that saying
“comma” or “question mark” inserts those words literally. Whisper recognizes
speech and often supplies inferred punctuation, but Decktation previously had
no layer for interpreting these words as dictation commands.

## Existing implementations

Handy's [default post-processing prompt](https://github.com/cjpais/Handy/blob/main/src-tauri/src/settings.rs)
explicitly asks an LLM to replace spoken punctuation, alongside spelling,
capitalization, number conversion, and filler removal. Its settings define a
separate “Transcribe with Post-Processing” shortcut and configurable providers.
This offers contextual interpretation, but requires configuring additional
inference and can change text beyond punctuation. A
[Handy proposal for local French commands](https://github.com/cjpais/Handy/discussions/1805)
also describes a deterministic text-processing layer; that discussion is a
proposal, not evidence that Handy ships that implementation.

Google Speech separates
[spoken punctuation](https://docs.cloud.google.com/speech-to-text/docs/v1/spoken-punctuation-emojis)
from automatic punctuation. Its boolean option converts, for example,
`how are you question mark` to `how are you?`; it defaults off outside the
command-and-search model. This distinction fits Decktation: Whisper's inferred
punctuation and explicit spoken commands are different features.

Apple's [dictation command list](https://support.apple.com/en-gb/guide/mac-help/mh40695/mac)
supports punctuation names, including comma, question mark, and period/full
stop, plus formatting commands. This provides familiar command names. Decktation
implements a smaller punctuation vocabulary appropriate for chat.

## Decktation implementation

The resident Whisper boundary already folds presentation line breaks into
spaces and capitalizes standalone English `I`. The new conversion runs there
before channel parsing, review, countdown, or injection. Consequently test
recordings, draft previews, and sent messages all use the same converted text,
and CPU retries use the same code path. It does not modify the Whisper prompt,
load another model, or make network requests.

The opt-in setting persists in `button_config.json`, is restored at voice-service
startup, and can change without reloading the model. The standalone CLI exposes
the same behavior through `--spoken-punctuation`.

Matching is case-insensitive and uses word boundaries. Multiword commands accept
spaces or hyphens. Punctuation directly around a recognized command is replaced
with the requested symbol: `ready, period.` becomes `ready.`. Spaces before
symbols are removed, and a space separates the next word. Existing text without
commands is unchanged. Casual chat still adjusts initial capitalization, but
retains terminal periods and ellipses inserted by explicit commands. Whisper's
automatic terminal periods are still stripped. Conversion attaches this
provenance to an internal string subclass, which preserves existing string and
JSON behavior. Channel parsing reads it before stripping the prefix and freezes
the formatted message into the draft. Metadata belongs to each recording, so
another recording or a settings change cannot overwrite that distinction.

## Scope and trade-offs

Supported commands: comma, period, full stop, question mark, exclamation mark,
exclamation point, colon, semicolon, ellipsis. These are English commands only,
active with English or Auto Detect selected. The worker returns text without a
detected-language field, so Auto Detect interprets matching English words even
inside mixed-language transcripts; explicitly selecting another language
disables the conversion.

A deterministic converter cannot distinguish the punctuation command “period”
from “a period of time.” The option therefore defaults off and explains how to
retain literal words. There is no contextual rewriting or automatic sentence
recapitalization. Line breaks, paragraph commands, editing commands, and quote
pairing are outside this issue's scope; the existing chat injection boundary
rejects control characters.

Automated coverage exercises commands, recognition punctuation artifacts,
case, word boundaries, Unicode, line wrapping, enabled/disabled behavior,
language changes, persistence, and casual chat through review and confirmation.
Steam Deck microphone and game integration still require hardware validation.

## Explicit slash command prefix

Starting a transcript with `command` identifies a game command rather than
ordinary chat. This is independent of the punctuation toggle and applies only
with English or Auto Detect selected. `command GG.` becomes `/gg`; the longer
`command slash GG` and a Whisper-rendered `command /gg` are accepted too. A complete command name is
required; a bare “slash” or an incomplete prefix stays literal.

The same internal transcript annotation carries command routing until channel
parsing. Commands select an internal `command` destination, bypass casual-case
formatting and preset channel prefixes, and do not update remembered channels.
Review freezes this destination with the command text. Injection uses existing
preset chat keys, clipboard insertion, manual-send behavior, and control-character
checks. Generic presets simply paste the command into the focused field.

Command names are lowercased, argument case is preserved, and inferred trailing
sentence marks are stripped. Punctuation conversion, when enabled, applies only
to arguments so `/period` remains a valid literal command name. Explicit spoken
punctuation in arguments is retained. No command allowlist or game-specific
aliases are inferred.
