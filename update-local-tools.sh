#!/usr/bin/env bash
# Download / refresh offline copies of tools linked from the startpage "Local" card.
# Usage: ./update-local-tools.sh            (all)
#        ./update-local-tools.sh cyberchef  (just one: cyberchef|revshells|gtfobins|lolbas)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)/local"
mkdir -p "$DIR"
UA='Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0'

cyberchef() {
  local url tmp
  url=$(curl -fsSL https://api.github.com/repos/gchq/CyberChef/releases/latest \
        | jq -r '.assets[] | select(.name | endswith(".zip")) | .browser_download_url' | head -1)
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/cc.zip" "$url"
  rm -rf "$DIR/CyberChef" && mkdir -p "$DIR/CyberChef"
  unzip -q "$tmp/cc.zip" -d "$DIR/CyberChef"
  rm -rf "$tmp"
  # stable entry point regardless of version in the filename
  ln -sf "$(cd "$DIR/CyberChef" && ls CyberChef_v*.html | head -1)" "$DIR/CyberChef/index.html"
  echo "CyberChef -> $(basename "$url")"
}

revshells() {
  if [[ -d "$DIR/revshells/.git" ]]; then
    git -C "$DIR/revshells" pull -q --ff-only
  else
    git clone -q --depth 1 https://github.com/0dayCTF/reverse-shell-generator "$DIR/revshells"
  fi
  echo "RevShells -> $(git -C "$DIR/revshells" log -1 --format=%cs)"
}

# Static-site mirrors: wget rewrites links so they work from file://
mirror() {
  local name=$1 url=$2
  rm -rf "$DIR/$name.tmp"
  wget -q -U "$UA" --mirror --convert-links --adjust-extension --page-requisites \
       --no-parent -e robots=off -nH -P "$DIR/$name.tmp" "$url" || true  # wget exits 8 on any 404
  [[ -f "$DIR/$name.tmp/index.html" ]] || { echo "$name mirror failed" >&2; rm -rf "$DIR/$name.tmp"; return 1; }
  rm -rf "$DIR/$name" && mv "$DIR/$name.tmp" "$DIR/$name"
  echo "$name -> $(find "$DIR/$name" -name '*.html' | wc -l) pages"
}

gtfobins() { mirror gtfobins https://gtfobins.org/; }
lolbas()   { mirror lolbas https://lolbas-project.github.io/; }

if (( $# )); then for t in "$@"; do "$t"; done
else cyberchef; revshells; gtfobins; lolbas; fi
