# firefox-startpage

![screenshot](assets/screenshot.png)

A cyberpunk-themed Firefox new tab page. No extensions required — uses Firefox AutoConfig to load a local HTML file.

**Features:**
- Live clock and date
- DuckDuckGo search bar
- Link cards: hacking platforms, bug bounty, OSINT, exploit databases, crypto tools, cheatsheets, privesc, learning, and more
- **Swappable backgrounds** — drop images into `Background/`; each one gets its own theme (palette, dimming, focal point, hero alignment) generated from the image
- **⟳ change background** button and a thumbnail picker (with a "shuffle each load" option); picks up new images without reloading the page
- **Local / Offline card** — offline copies of CyberChef, RevShells, GTFOBins and LOLBAS, plus a local HackTricks container with an up/down status dot
- Monospace font stack (JetBrains Mono / Fira Code / Cascadia Code)

## Install

### 1. Place the startpage files

```sh
mkdir -p ~/.local/share/firefox-startpage
cp -r index.html Background update-backgrounds.py update-local-tools.sh ~/.local/share/firefox-startpage/
```

`update-backgrounds.py` needs Python 3 with Pillow (`sudo pacman -S python-pillow` / `pip install pillow`).

### 2. Find your Firefox install directory

```sh
which firefox          # e.g. /usr/bin/firefox → install dir is /usr/lib/firefox
# or for Firefox ESR:
which firefox-esr
ls /opt/firefox-esr/   # if manually installed
```

### 3. Install the AutoConfig files

Replace `YOUR_FIREFOX_DIR` with your actual path and `YOUR_USERNAME` with your Linux username.

```sh
# Edit mozilla.cfg — replace YOUR_USERNAME with your actual username
nano mozilla.cfg

# Then copy both files:
sudo cp autoconfig.js YOUR_FIREFOX_DIR/defaults/pref/autoconfig.js
sudo cp mozilla.cfg YOUR_FIREFOX_DIR/mozilla.cfg
```

The path to update in `mozilla.cfg`:
```
file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html
```

### 4. Restart Firefox

Fully quit Firefox (all windows/processes, not just close-window) and relaunch. New tabs should now open the startpage.

**Troubleshooting:**
- Verify the path in `mozilla.cfg` matches where you placed `index.html`
- Make sure both AutoConfig files are in the right Firefox directory
- Firefox ESR and standard Firefox have separate install dirs — edit the right one
- **Standard release Firefox sandboxes AutoConfig by default**, which silently no-ops the `ChromeUtils.importESModule(...)` line in `mozilla.cfg` (no error shown). `autoconfig.js` already sets `pref("general.config.sandbox_enabled", false);` to disable that — if new tabs still show the default page, confirm this pref actually landed in the installed `autoconfig.js`.
- **Check for a conflicting extension.** Any extension with `chrome_url_overrides.newtab` in its manifest (e.g. another new-tab-replacement addon) silently overrides AutoConfig. Check `about:addons` → Extensions and disable/remove anything else controlling the new tab page.

### Optional: Set as homepage too

`browser.startup.homepage` only affects the Home button and new windows — it does **not** control what loads when Firefox first launches (that's `browser.startup.page`, usually defaulting to "resume previous session"). To also show the startpage on launch, add both lines to `~/.mozilla/firefox/YOUR_PROFILE/user.js`:

```js
user_pref("browser.startup.homepage", "file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html");
user_pref("browser.startup.page", 1);
```

This replaces session-resume behavior on launch (old tabs are still recoverable via History → Restore Previous Session). Put changes in `user.js`, not `prefs.js` — Firefox overwrites `prefs.js` from memory on exit, so direct edits there get silently reverted.

## Backgrounds

Put any `.png` / `.jpg` / `.webp` / `.gif` / `.bmp` / `.avif` into `Background/`, then run:

```sh
~/.local/share/firefox-startpage/update-backgrounds.py
```

This writes `Background/backgrounds.js` (palette + layout per image) and thumbnails in `Background/.thumbs/`. It has to run outside the browser: a `file://` page can't list a folder or read pixels from local images. The page re-reads `backgrounds.js` whenever you click **⟳ change background** or open the picker, so no reload is needed. With no backgrounds at all, the page falls back to the original purple theme.

You can force a background with a URL hash, e.g. `index.html#bg=LoneHacker.png`.

### Optional: regenerate automatically

A systemd user path unit re-runs the script whenever `Background/` changes:

```sh
mkdir -p ~/.config/systemd/user
cp systemd/startpage-backgrounds.{path,service} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now startpage-backgrounds.path

journalctl --user -u startpage-backgrounds.service -n 20   # see what it picked up
systemctl --user disable --now startpage-backgrounds.path  # turn it off
```

The script only rewrites `backgrounds.js` when its content changes, so its own write doesn't re-trigger the watcher.

## Local / Offline tools

```sh
~/.local/share/firefox-startpage/update-local-tools.sh            # download / refresh all (~95 MB)
~/.local/share/firefox-startpage/update-local-tools.sh cyberchef  # or one: cyberchef|revshells|gtfobins|lolbas
```

Copies land in `local/` (git-ignored). Needs `curl`, `jq`, `unzip`, `git`, `wget`.

The HackTricks links expect a local [HackTricks](https://github.com/HackTricks-wiki/hacktricks) checkout at `~/hacktricks`, served by Docker on `http://localhost:3337` (the dot next to the link shows whether it's up). The "offline book" link opens `~/hacktricks/book/` from disk; its search only works through the container.

## Wallpaper

The background images in `Background/` are **not my creation**. I do not know the original artists. If you are the creator of one and would like it removed or credited properly, please open an issue or contact me and I will make the change immediately.

## Notes

- **Package updates**: `mozilla.cfg` lives in the Firefox install dir and may be overwritten by major upgrades. Re-copy it after updates.
- **Multiple profiles**: The AutoConfig applies to all profiles in that Firefox install.
- **Customizing links**: Edit the cards directly in `index.html` — each `.card` block is self-contained.
- **Colors**: Theme colors are CSS variables at the top of the `<style>` block, set as RGB triplets (`--accent-rgb` etc.) so each background can override them. Use `rgba(var(--accent-rgb), …)` rather than hardcoding colors.

## File Structure

```
firefox-startpage/
├── index.html               # The startpage
├── Background/
│   ├── *.png                # Background images (add/remove freely)
│   ├── backgrounds.js       # Generated: per-image theme + layout
│   └── .thumbs/             # Generated: picker thumbnails
├── update-backgrounds.py    # Regenerates Background/backgrounds.js
├── update-local-tools.sh    # Downloads offline tool copies into local/
├── systemd/                 # Optional watcher for Background/
├── assets/screenshot.png
├── autoconfig.js            # Tells Firefox to load mozilla.cfg
└── mozilla.cfg              # Redirects new tab to the local HTML file
```
