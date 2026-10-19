# Firefox Startpage — Install Instructions

This sets your new tab page to a local HTML file via Firefox AutoConfig (no extension needed).

## 1. Place the startpage files

```
mkdir -p ~/.local/share/firefox-startpage
cp -r index.html Background update-backgrounds.py update-local-tools.sh ~/.local/share/firefox-startpage/
```

To add backgrounds, drop images into `Background/` and run `update-backgrounds.py` (needs Python 3 + Pillow), or set up the optional systemd watcher. See the README sections "Backgrounds" and "Local / Offline tools".

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

Fully quit Firefox (not just close the window — make sure no `firefox` process is left running), then relaunch. New tabs should now open the startpage. If it doesn't work, verify:
- The path in `mozilla.cfg` matches where you put `index.html`
- Both files are in the right Firefox directories
- Firefox ESR vs standard Firefox — make sure you're editing the right install dir
- **Standard (non-ESR) release builds sandbox AutoConfig scripts by default**, which silently blocks the `ChromeUtils.importESModule(...)` call in `mozilla.cfg` — no error, it just does nothing. `autoconfig.js` already includes `pref("general.config.sandbox_enabled", false);` to disable that sandbox; if this pref gets stripped or overridden elsewhere, the new-tab override won't take effect. (Mozilla has signaled this override may eventually be removed entirely, at which point ESR would be the only way to keep using this approach.)
- **A conflicting extension can silently win.** Any installed extension using `chrome_url_overrides.newtab` in its manifest overrides AutoConfig's setting entirely. Check `about:addons` → Extensions for anything (including another new-tab-replacement addon) that might be claiming the new tab page, and disable/remove it.
- Your desktop's taskbar/dock may cache app metadata (icon/name) from before you edited any `.desktop` launcher files — if a launcher still shows a stale label after a fix, log out/in or restart your panel process.

## Notes

- **Package updates**: `mozilla.cfg` lives in the Firefox install dir and can be overwritten by major Firefox upgrades. Re-copy it after updates.
- **Multiple profiles**: This applies to all profiles in that Firefox install.
- **Homepage vs new tab**: `browser.startup.homepage` (below) only controls what the Home button and new windows load — it does **not** control what shows when Firefox first launches. That's governed separately by `browser.startup.page`, which most modern Firefox installs default to `3` ("resume previous session"). To also show the startpage on launch, add both lines to your Firefox profile's `user.js`:
  ```
  ~/.mozilla/firefox/PROFILE_DIR/user.js
  ```
  ```js
  user_pref("browser.startup.homepage", "file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html");
  user_pref("browser.startup.page", 1);
  ```
  Note this replaces "resume previous session" — your previously open tabs won't auto-restore (though they're still recoverable via History → Recently Closed / Restore Previous Session). Editing `user.js` only takes effect on the next full restart, and edits made while Firefox is running should go in `user.js` rather than `prefs.js`, since Firefox overwrites `prefs.js` from its in-memory state on exit.
