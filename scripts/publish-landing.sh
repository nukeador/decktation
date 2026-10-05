#!/usr/bin/env bash
set -euo pipefail
: "${PAGES_BASE_URL:?PAGES_BASE_URL is required}"
: "${REF_NAME:?REF_NAME is required}"
WORKSPACE_DIR="$(pwd)"
PAGES_DIR="$WORKSPACE_DIR/pages-site"
# The workflow checks out the existing tree so downloads and other previews survive.
test -d "$PAGES_DIR/.git"
SITE_BASE_URL="$PAGES_BASE_URL" python3 site/build.py
cp -R site/dist/. "$PAGES_DIR/"
LANDING_KEY="$(python3 scripts/branch-slug.py "$REF_NAME")"
LANDING_DIR="$PAGES_DIR/landing/$LANDING_KEY"
mkdir -p "$LANDING_DIR"
SITE_DOWNLOADS_URL="$PAGES_BASE_URL/downloads/" SITE_BASE_URL="$PAGES_BASE_URL/landing/$LANDING_KEY" python3 site/build.py
cp -R site/dist/. "$LANDING_DIR/"
cd "$PAGES_DIR"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add .
if ! git diff --cached --quiet; then
  git commit -m "Publish landing for $REF_NAME"
  git push origin HEAD:gh-pages
fi
