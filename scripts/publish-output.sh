#!/usr/bin/env bash
# Publishes generated assets (dist/) to the output branch, replacing its contents.
# Generated files live on their own branch so main stays clean of commit noise.
set -euo pipefail
cd "$(dirname "$0")/.."

stage=$(mktemp -d)
cp dist/* "$stage"/
rm -f "$stage"/_contact.svg

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

if git ls-remote --exit-code --heads origin output >/dev/null 2>&1; then
  git fetch origin output
  git checkout -B output FETCH_HEAD
else
  git checkout --orphan output
fi

git rm -rf --ignore-unmatch . >/dev/null
git clean -fdq
cp "$stage"/* .
git add -A
if git diff --cached --quiet; then
  echo "publish-output: no changes"
else
  git commit -qm "chore: refresh generated profile assets"
  git push -q origin output
  echo "publish-output: published $(ls -1 | wc -l) files to output"
fi
