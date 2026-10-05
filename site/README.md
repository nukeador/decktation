# Decktation product landing

First implementation of the supplied landing specification and HTML prototype.
Dependency-free static generation keeps the plugin build unchanged.

```sh
python3 site/build.py
python3 -m http.server 4173 --directory site/dist
```

Open http://localhost:4173/ (English) or /es/ (Spanish). The layout is in
`src/template.html`, complete translations in `src/i18n/*.json`, and styles,
behavior and media in `public/`. Add a complete locale JSON and register it in
`build.py` to publish another static route. The builder rejects missing keys.
French, German, Portuguese and Italian remain pending complete reviewed copy;
the partial prototype translations are intentionally not advertised.

The existing Pages deployment builds this site and overlays it on the downloads
artifact. Its original index moves to `/downloads/`; release ZIPs, `latest.zip`,
branch builds, metadata and store catalogs are retained. Nothing is deployed by
running the local build. GitHub Actions performs deployment after a push.

Hero and chat WebP images are illustrative demo composites, clearly labeled on-page.
Replace them with real, anonymized SteamOS/Decktation and WoW captures before
calling the page production-ready. The screenshot `public/assets/og-image.png`
is a browser capture of the English hero for social previews; regenerate after
major visual changes. Font Awesome Free 6.7.2 is vendored locally (including its license); no CDN or analytics are used. The original project logo is animated with CSS, with a static fallback for reduced motion.

Verified locally: static builds, locale completeness, relative links, desktop
and mobile layout (320–1440 px), navigation/Escape, FAQ and install URL copying.
Lighthouse scores and a live GitHub Actions deployment have not been measured.

The language dropdown uses Font Awesome's language icon. Default-route visits
use a saved manual choice or the browser's primary language, falling back to
English; explicit localized URLs are respected. Query strings and section
anchors survive language changes.

Game marks are original assets from the publishers' sites, stored locally:
- World of Warcraft: https://blz-contentstack-images.akamaized.net/v3/assets/bltf408a0557f4e4998/bltb7c1db49cad77069/60a81b45b078b00d8a909fce/world-of-warcraft.svg
- Guild Wars 2: https://guildwars2.staticwars.com/wp-content/themes/guildwars2.com-live/img/gw2-logotype.723cc563.svg
- Generic: Font Awesome Free's Steam brand icon.

The updated demo combines Valve's official Steam Deck frontal render with the
WoW screenshot from PC Gamer's The War Within review. Recording indicator
geometry, colors, nine bars and bottom position follow
`backend/src/recording_overlay.py`; this remains a composed example.

Source media: `src/media/`. Run `python3 site/compose-demo.py` to regenerate
intermediate SVG compositions in `generated/`, then capture each at 1000×620
as WebP in the browser into `public/assets/`. Do not edit the third-party source
images when replacing the gameplay capture.
- Device: https://cdn.fastly.steamstatic.com/steamdeck/images/overview_steamDeck_heroCrop.png
- Gameplay attribution: https://www.pcgamer.com/games/world-of-warcraft/world-of-warcraft-the-war-within-review/

The hero now uses a logo-inspired illustrated device (`deck-mockup.svg`) with
live HTML layers over the example gameplay (`wow-screen.webp`). A lightweight
animation cycles through recording, transcribing, typing and the completed
party message. Copy is localized. The demo pauses outside the viewport, in
background tabs and through its pause control. Reduced-motion users see the
completed message without animation. The existing static hero composition is
retained as a reusable fallback asset.

The animated hero now uses a static, softly colored schematic game scene (`game-placeholder.svg`) so recording and text entry remain the focus. The WoW proof section retains its separate gameplay example.

The WoW proof section uses actual gameplay from Blizzard's official UI/HUD
article, with localized example chat and the recording pill as separate HTML
layers. Image source:
https://bnetcmsus-a.akamaihd.net/cms/content_entry_media/XSHS00F6IFZ91650386025907.jpg
Publisher article:
https://news.blizzard.com/en-us/article/23837944/get-into-the-grid-of-things-with-the-updated-ui-and-hud

Latest WoW proof asset: `public/assets/wow-forever-chat.webp`, using the actual
Forever beta tauren gameplay screenshot from GameStar:
https://www.gamestar.de/galerien/world_of_warcraft_forever,137281.html
https://images.cgames.de/images/gamestar/287/world-of-warcraft-forever_6441900.jpg
The built-in image generator edited the chat to show `[Party] Ready to pull?`
and `/p Ready to pull?` with a cursor; this is labeled as an edited chat demo.
Original and full generated edit are kept in `src/media/`, alongside the exact
prompt in `wow-forever-edit-prompt.txt`. This replaces the earlier Dragonflight
image in the live page. The hero inserts the full message at once after a short
transcription stage, rather than typing character by character.

Pages publication now generates the downloads index at `/downloads/`, preserves
all existing ZIP/metadata/catalog paths, and publishes the landing at `/`.
Branch builds also persist a shareable copy under `/landing/<branch-slug>/`.
`SITE_BASE_URL` configures canonical/social/sitemap URLs for the hosting fork
and each branch preview. Production install links still target the upstream
stable package; the proposed landing does not advertise its dev build as stable.

### Native chat animation in the WoW section

The current WoW example uses a full gameplay screenshot from GameStar's WoW:
Forever beta gallery, with native chat edited through ImageGen. It alternates
between `wow-chat-empty.webp` and `wow-chat-filled-en.webp` / `wow-chat-filled-es.webp`.
There is no HTML chat panel or pause control in this section. The centered
recording indicator animates during listening; the completed native chat frame
appears after transcription. Each demo stops offscreen and in background tabs;
reduced-motion users see the completed frame.

Gameplay source: https://www.gamestar.de/galerien/world_of_warcraft_forever,137281.html

During transcription, both screenshot frames zoom toward the bottom-left chat over 1.7 seconds. The completed native chat appears at once after the zoom finishes, remains visible, then returns to the full frame on the next cycle. Reduced motion disables this zoom.

### Independent CI publication

`landing.yml` validates and publishes changes to `site/` without building the plugin. `build.yml` ignores web-only changes and publishes only plugin downloads. Both workflows share a publication concurrency group to preserve the shared Pages tree. The landing workflow keeps existing download paths and branch previews intact.
