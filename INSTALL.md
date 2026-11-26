# Firefox Startpage: Install Instructions

This makes Firefox's **new tab** open a local HTML file using Firefox AutoConfig. No extension needed.

Every step ends with a **Check** you can run before moving on. All commands assume you are in
this folder (the one with `index.html` in it).

---

## 0. Requirements

| Needed for | Package (Arch) | Check |
|---|---|---|
| Backgrounds (`update-backgrounds.py`) | `python-pillow` | `python3 -c 'import PIL; print(PIL.__version__)'` |
| Offline tools (`update-local-tools.sh`) | `curl jq unzip git wget` | `command -v curl jq unzip git wget` |

```sh
sudo pacman -S --needed python-pillow curl jq unzip git wget
```

Only the startpage itself (steps 1–4) is required. The rest is optional.

---

## 1. Copy the startpage files into place

```sh
mkdir -p ~/.local/share/firefox-startpage
cp -r index.html Background update-backgrounds.py update-local-tools.sh ~/.local/share/firefox-startpage/
```

**Check:** `ls ~/.local/share/firefox-startpage/index.html` prints the path (no error).

---

## 2. Find your Firefox *install* directory

This is the folder that holds the real `firefox` binary, **not** your profile folder.

| Install | Usual folder |
|---|---|
| Firefox from pacman (Arch) | `/usr/lib/firefox` |
| Firefox ESR, manually extracted | `/opt/firefox-esr` |

> **Gotcha:** On Arch, `/usr/bin/firefox` is a 2-line *shell script*, not a symlink, so
> `readlink -f $(which firefox)` just prints `/usr/bin/firefox` and tells you nothing.
> Use one of these instead:
>
> ```sh
> cat "$(command -v firefox)"      # shows: exec /usr/lib/firefox/firefox "$@"
> pgrep -a firefox | head -1       # while Firefox is running: /usr/lib/firefox/firefox
> ```

**Check:** `ls /usr/lib/firefox/firefox` (or your folder) exists. You should also see a
`defaults/pref/` folder next to it.

---

## 3. Install the two AutoConfig files (needs sudo)

### Easy way: the script

```sh
sudo ./install-newtab.sh                    # regular Firefox, /usr/lib/firefox
sudo ./install-newtab.sh /opt/firefox-esr   # or give a different install dir
```

It writes both files, fills in **your** home path automatically (it uses `$SUDO_USER`, so the
path is `/home/<you>/...` and not `/root/...`), and sets the permissions.

### Manual way

```sh
FF=/usr/lib/firefox     # ← your folder from step 2

sudo tee "$FF/defaults/pref/autoconfig.js" >/dev/null <<'EOF'
pref("general.config.filename", "mozilla.cfg");
pref("general.config.obscure_value", 0);
pref("general.config.sandbox_enabled", false);
EOF

# The first line of mozilla.cfg MUST be a comment ("//") or Firefox ignores the whole file.
# $HOME is expanded here by YOUR shell, before sudo runs, so it is your home.
sudo tee "$FF/mozilla.cfg" >/dev/null <<EOF
//
ChromeUtils.importESModule("resource:///modules/AboutNewTab.sys.mjs").AboutNewTab.newTabURL = "file://$HOME/.local/share/firefox-startpage/index.html";
EOF

sudo chmod 644 "$FF/mozilla.cfg" "$FF/defaults/pref/autoconfig.js"
```

(The `autoconfig.js` / `mozilla.cfg` files in this folder are templates with a
`YOUR_USERNAME` placeholder. You don't need to edit or copy them if you use either method above.)

**Check:**

```sh
cat /usr/lib/firefox/defaults/pref/autoconfig.js   # 3 pref(...) lines, incl. sandbox_enabled false
cat /usr/lib/firefox/mozilla.cfg                   # line 1 is "//", line 2 has file:///home/<you>/...
```

Why `sandbox_enabled false`: regular (non-ESR) Firefox sandboxes AutoConfig by default, which
makes the `ChromeUtils` line **silently do nothing**. ESR doesn't need it, but it's harmless there.

---

## 4. Turn off anything else that controls the new tab

Any extension that replaces the new tab page wins over AutoConfig.

1. Open `about:addons` → **Extensions**.
2. Disable or remove new-tab replacers, e.g. **nightTab**, **New Tab Override**, Tabliss, etc.
   (Ignore Firefox's built-in "New Tab" system add-on. That one is fine.)
3. `about:preferences#home` should **not** say "An extension … is controlling your New Tab page".

---

## 5. Fully restart Firefox

Closing the window is not enough. Quit with **Ctrl+Q** (or menu → Quit), then:

```sh
pgrep -a firefox    # must print NOTHING. If it prints something: pkill firefox
```

Relaunch Firefox and press **Ctrl+T**.

**Check:** the new tab shows the startpage. Note the address bar stays empty on new tabs.
That's normal for AutoConfig.

---

## Optional: also show it on launch / Home button

`browser.startup.homepage` only controls the Home button and new windows. What shows on
**launch** is `browser.startup.page` (default `3` = restore previous session).

1. Find your profile folder: open `about:support` → **Profile Folder** → *Open Directory*.
   Or by hand: newer Firefox keeps profiles in **`~/.config/mozilla/firefox/`**, older
   setups in `~/.mozilla/firefox/`. The default one is listed in `profiles.ini`
   under `[Install…] Default=`.
2. Create/append `user.js` in that folder (use `user.js`, **not** `prefs.js`, which Firefox
   overwrites on exit):

   ```js
   user_pref("browser.startup.homepage", "file:///home/YOUR_USERNAME/.local/share/firefox-startpage/index.html");
   user_pref("browser.startup.page", 1);   // 1 = homepage on launch instead of restoring the last session
   ```
3. Fully restart Firefox (step 5). Old tabs are still recoverable via History → Restore Previous Session.

---

## Optional: backgrounds

Drop `.png/.jpg/.webp/.gif/.bmp/.avif` files into `~/.local/share/firefox-startpage/Background/`
(the installed copy, **not** this repo folder), then:

```sh
~/.local/share/firefox-startpage/update-backgrounds.py
```

Auto-regenerate whenever that folder changes:

```sh
mkdir -p ~/.config/systemd/user
cp systemd/startpage-backgrounds.{path,service} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now startpage-backgrounds.path
```

**Check:** `systemctl --user status startpage-backgrounds.path` shows `active (waiting)`.

## Optional: offline tools

```sh
~/.local/share/firefox-startpage/update-local-tools.sh    # ~95 MB into ~/.local/share/firefox-startpage/local/
```

Needs `wget` (see step 0). It fails partway through without it.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| New tab is still Firefox's default | Firefox wasn't fully quit (`pgrep -a firefox`), or files went to the wrong install dir (step 2). |
| Still default, files look right | `mozilla.cfg` line 1 isn't `//`, or `sandbox_enabled false` is missing from `autoconfig.js`. |
| Another page/old copy shows | An extension is controlling new tabs (step 4). New Tab Override's "local file" mode keeps a stale copy. |
| Blank/"file not found" tab | Path in `mozilla.cfg` is wrong (e.g. `/root/...` from running `$HOME` inside sudo, or a typo). Re-run step 3. |
| Worked, then stopped after an update | The install dir was replaced (common for manual `/opt` ESR). Re-run step 3. On Arch the pacman package doesn't own these files, so `pacman -Syu` leaves them alone. |

## Undo

```sh
sudo ./install-newtab.sh --undo
# or: sudo rm /usr/lib/firefox/mozilla.cfg /usr/lib/firefox/defaults/pref/autoconfig.js
```
