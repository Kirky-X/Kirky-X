#!/usr/bin/env bash
# Regenerates dist/stats.svg (crates · downloads · public repos) from live crates.io + GitHub data.
# Runs in GitHub Actions (ubuntu-latest: curl, jq, gh, python3 preinstalled) and locally for previews.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dist
UA="kirky-profile-readme (github.com/Kirky-X)"

# Thousands separator: 85058 -> 85,058
fmt() { sed -re ':a;s/([0-9]+)([0-9]{3})/\1,\2/;ta' <<< "$1"; }

total=0
count=0
while read -r crate; do
  [ -z "$crate" ] && continue
  dl=$(curl -sf --retry 3 --retry-delay 2 -A "$UA" "https://crates.io/api/v1/crates/$crate" | jq -r '.crate.downloads')
  total=$((total + dl))
  count=$((count + 1))
done < crates.txt

kb=$(awk -v t="$total" 'BEGIN{printf "%.1fk", t/1000}')
repos=$(gh api "users/Kirky-X/repos?per_page=100" --paginate --jq '[.[] | select(.fork == false and .archived == false)] | length' | tail -n 1)
stats="${count} crates · ${kb} downloads · ${repos} public repos"
w=$(( ${#stats} * 7 + 48 ))
tw=$(( w / 2 ))
cat > dist/stats.svg <<EOF
<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="28" role="img" aria-label="${stats}">
  <rect width="${w}" height="28" rx="14" fill="#222222"/>
  <text x="${tw}" y="19" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" fill="#f8f8f8">${stats}</text>
</svg>
EOF
echo "refresh-stats: ${stats}"
