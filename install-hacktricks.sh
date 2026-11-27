#!/usr/bin/env bash
# Install the helper that lets the startpage's "HackTricks (container)" link
# start the local HackTricks container. No sudo needed. Anything still missing
# (Docker, the HackTricks download, the Docker image) is offered in popups the
# first time you click the link.
#
#   ./install-hacktricks.sh          install / update
#   ./install-hacktricks.sh --undo   remove the helper (leaves ~/hacktricks and Docker alone)
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

BIN=$HOME/.local/bin
APPS=${XDG_DATA_HOME:-$HOME/.local/share}/applications
SHARE=${XDG_DATA_HOME:-$HOME/.local/share}/hacktricks-start
DESKTOP=hacktricks-handler.desktop

if [[ ${1:-} == --undo ]]; then
  rm -v -f "$BIN/hacktricks-start" "$APPS/$DESKTOP" "$SHARE/serve.py"
  rmdir "$SHARE" 2>/dev/null || true
  command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
  echo "Removed. If you added the 'hacktricks' function to your shell rc file, delete it by hand."
  exit 0
fi

install -Dm 755 hacktricks/hacktricks-start "$BIN/hacktricks-start"
install -Dm 644 hacktricks/serve.py "$SHARE/serve.py"
install -Dm 644 hacktricks/$DESKTOP "$APPS/$DESKTOP"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
xdg-mime default "$DESKTOP" x-scheme-handler/hacktricks

echo "Installed:"
echo "  $BIN/hacktricks-start"
echo "  $SHARE/serve.py"
echo "  $APPS/$DESKTOP  (handles hacktricks:// links: $(xdg-mime query default x-scheme-handler/hacktricks))"

# A `hacktricks` shell command (start or restart from a terminal).
rc=
case ${SHELL##*/} in zsh) rc=$HOME/.zshrc ;; bash) rc=$HOME/.bashrc ;; esac
if [[ -n $rc ]] && ! grep -q 'hacktricks-start' "$rc" 2>/dev/null; then
  cat >>"$rc" <<'EOF'

# HackTricks local container (http://localhost:3337). Start or restart it;
# take it down with `docker stop hacktricks` (--rm deletes it, so re-run this
# rather than `docker start`). Script: ~/.local/bin/hacktricks-start
hacktricks() { "$HOME/.local/bin/hacktricks-start" --restart "$@"; }
EOF
  echo "  'hacktricks' command added to $rc (open a new terminal to use it)"
fi

missing=()
for c in zenity curl git xdg-open; do command -v "$c" >/dev/null || missing+=("$c"); done
if (( ${#missing[@]} )); then
  echo
  echo "Missing: ${missing[*]}. The setup popups need zenity, and the helper needs curl, git and xdg-open."
  echo "  Arch: sudo pacman -S --needed zenity curl git xdg-utils"
fi

echo
echo "Next: open a new tab, click 'HackTricks (container)'. Firefox asks once whether to open"
echo "the hacktricks link: tick 'Always allow' and choose Open. Popups walk you through the rest."
