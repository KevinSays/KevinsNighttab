# Making new tabs open the startpage

Firefox gets its new-tab page from **AutoConfig**: two small files in the Firefox
*install* folder (not the profile). It applies to every profile of that install.
Each Firefox install (regular, ESR) needs its own copy.

| Install | Typical folder |
|---|---|
| Firefox (distro package, e.g. Arch/pacman) | `/usr/lib/firefox` |
| Firefox ESR (manual install) | `/opt/firefox-esr` |

Not sure? `readlink -f $(which firefox)` shows where your `firefox` actually lives.

## 1. Install the two files (needs sudo)

Swap `/usr/lib/firefox` for `/opt/firefox-esr` to do ESR instead.

```sh
FF=/usr/lib/firefox

# autoconfig.js: tells Firefox to load mozilla.cfg
sudo tee "$FF/defaults/pref/autoconfig.js" >/dev/null <<'EOF'
pref("general.config.filename", "mozilla.cfg");
pref("general.config.obscure_value", 0);
pref("general.config.sandbox_enabled", false);
EOF

# mozilla.cfg: sets the new-tab URL (the first line MUST be a comment)
sudo tee "$FF/mozilla.cfg" >/dev/null <<EOF
//
ChromeUtils.importESModule("resource:///modules/AboutNewTab.sys.mjs").AboutNewTab.newTabURL = "file://$HOME/.local/share/firefox-startpage/index.html";
EOF

sudo chmod 644 "$FF/mozilla.cfg" "$FF/defaults/pref/autoconfig.js"
cat "$FF/mozilla.cfg"    # check the path looks right
```

- `sandbox_enabled false` is **required on regular Firefox**. Without it the
  `ChromeUtils` line silently does nothing. ESR doesn't need it, but it's harmless.
- On Arch, these files aren't owned by the package, so `pacman -Syu` won't overwrite them.
  Other distros/installs may replace them on upgrade (re-run step 1).

## 2. Remove anything else controlling new tabs

Any extension that sets the new tab page wins over AutoConfig.

1. `about:addons` → Extensions.
2. Disable or remove it, e.g. **New Tab Override**. Its "local file" mode may keep a
   saved copy of the page (so new tabs show a stale version) and that copy can't load
   `Background/` or `local/`.

## 3. Restart

Fully quit Firefox (check that `pgrep -a firefox` shows nothing for that install), relaunch, and open a new tab.

## Optional: also show it on launch / Home button

Add to the profile's `user.js` (`~/.mozilla/firefox/<profile>/user.js`), not `prefs.js`:

```js
user_pref("browser.startup.homepage", "file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html");
user_pref("browser.startup.page", 1);   // 1 = homepage on launch instead of restoring the last session
```


## Still showing the wrong page?

- Wrong folder: `readlink -f $(which firefox)` and check which install you're actually running.
- `mozilla.cfg` first line isn't a comment → Firefox ignores the whole file.
- An extension is still controlling new tabs (step 2). `about:preferences#home` says
  "An extension … is controlling your New Tab page" if so.
- A big Firefox upgrade can drop the files if the install is replaced wholesale (e.g. a
  manual `/opt` ESR install re-extracted). Re-run step 1.

## Undo

```sh
sudo rm /usr/lib/firefox/mozilla.cfg /usr/lib/firefox/defaults/pref/autoconfig.js
```
