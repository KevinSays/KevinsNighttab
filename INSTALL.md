# Firefox Startpage — Install Instructions

This sets your new tab page to a local HTML file via Firefox AutoConfig (no extension needed).

## 1. Place the startpage files

```
mkdir -p ~/.local/share/firefox-startpage/assets
cp index.html ~/.local/share/firefox-startpage/
cp assets/wallpaper.png ~/.local/share/firefox-startpage/assets/
```

To use a different wallpaper, replace `assets/wallpaper.png` with your own image (same filename), or update the `background: url(...)` line in `index.html`.

## 2. Find your Firefox install dir

```
which firefox          # → e.g. /usr/bin/firefox
# or for Firefox ESR:
which firefox-esr
ls /opt/firefox-esr/   # if manually installed
```

## 3. Install the AutoConfig files

Replace `YOUR_FIREFOX_DIR` with the actual path (e.g. `/usr/lib/firefox`, `/opt/firefox-esr`).

```
# Edit mozilla.cfg first — replace YOUR_USERNAME with your actual Linux username
nano mozilla.cfg

# Then copy both files:
sudo cp autoconfig.js YOUR_FIREFOX_DIR/defaults/pref/autoconfig.js
sudo cp mozilla.cfg YOUR_FIREFOX_DIR/mozilla.cfg
```

The `mozilla.cfg` path to update:
```
file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html
```

## 4. Restart Firefox

New tabs should now open the startpage. If it doesn't work, verify:
- The path in `mozilla.cfg` matches where you put `index.html`
- Both files are in the right Firefox directories
- Firefox ESR vs standard Firefox — make sure you're editing the right install dir

## Notes

- **Package updates**: `mozilla.cfg` lives in the Firefox install dir and can be overwritten by major Firefox upgrades. Re-copy it after updates.
- **Multiple profiles**: This applies to all profiles in that Firefox install.
- **Homepage vs new tab**: To also set the homepage, add this to your Firefox profile's `user.js`:
  ```
  ~/.mozilla/firefox/PROFILE_DIR/user.js
  ```
  Add line: `user_pref("browser.startup.homepage", "file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html");`
