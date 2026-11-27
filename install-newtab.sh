#!/usr/bin/env bash
# Install the Firefox AutoConfig files so new tabs, the homepage, and
# Firefox's launch page all open the startpage.
#
#   sudo ./install-newtab.sh                 # regular Firefox (/usr/lib/firefox)
#   sudo ./install-newtab.sh /opt/firefox-esr
#   sudo ./install-newtab.sh --newtab-only   # only new tabs; keep homepage + session restore
#   sudo ./install-newtab.sh --undo          # remove the files again
#
# The startpage files must already be in ~/.local/share/firefox-startpage
# (INSTALL.md step 1). Run with sudo; the target user's home is taken from
# $SUDO_USER so the path in mozilla.cfg points at *your* home, not /root.
set -euo pipefail

undo=0 newtab_only=0
while [[ ${1:-} == --* ]]; do
  case $1 in
    --undo)        undo=1 ;;
    --newtab-only) newtab_only=1 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done
FF=${1:-/usr/lib/firefox}

[[ $EUID -eq 0 ]] || { echo "Run with sudo: sudo $0 $*" >&2; exit 1; }
[[ -x $FF/firefox ]] || { echo "No firefox binary in $FF, so that is not a Firefox install dir." >&2; exit 1; }

if (( undo )); then
  rm -v -f "$FF/mozilla.cfg" "$FF/defaults/pref/autoconfig.js"
  echo "Removed. Fully quit and restart Firefox."
  exit 0
fi

user=${SUDO_USER:-$(logname 2>/dev/null || echo root)}
home=$(getent passwd "$user" | cut -d: -f6)
page="$home/.local/share/firefox-startpage/index.html"
[[ -f $page ]] || { echo "Missing $page. Do INSTALL.md step 1 first." >&2; exit 1; }

install -d -m 755 "$FF/defaults/pref"

cat > "$FF/defaults/pref/autoconfig.js" <<'EOF'
pref("general.config.filename", "mozilla.cfg");
pref("general.config.obscure_value", 0);
pref("general.config.sandbox_enabled", false);
EOF

# First line MUST be a comment or Firefox ignores the file.
cat > "$FF/mozilla.cfg" <<EOF
//
// New tabs
ChromeUtils.importESModule("resource:///modules/AboutNewTab.sys.mjs").AboutNewTab.newTabURL = "file://$page";
EOF

if (( ! newtab_only )); then
  # Homepage (Home button + new windows) and show it on launch instead of
  # restoring the last session. pref() re-applies at every startup, for every
  # profile of this install; changes made in Settings last until the next restart.
  cat >> "$FF/mozilla.cfg" <<EOF
// Homepage + on launch
pref("browser.startup.homepage", "file://$page");
pref("browser.startup.page", 1);
EOF
fi

chmod 644 "$FF/mozilla.cfg" "$FF/defaults/pref/autoconfig.js"

echo "Installed into $FF:"
echo "  $FF/defaults/pref/autoconfig.js"
echo "  $FF/mozilla.cfg  ->  file://$page"
if (( newtab_only )); then
  echo "  (new tabs only)"
else
  echo "  (new tabs + homepage + on launch; last session no longer auto-restores)"
fi
echo
echo "Now FULLY quit Firefox (pgrep -a firefox should print nothing), relaunch, open a new tab."
