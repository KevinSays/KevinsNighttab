#!/usr/bin/env python3
"""Scan Background/ and write Background/backgrounds.js with a theme per image.

The startpage is opened from file://, where a page can't list a folder or read
pixels from local images, so the colour and layout analysis happens here.
Re-run after adding or removing images:  ./update-backgrounds.py
"""
import colorsys
import json
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent
BG_DIR = ROOT / "Background"
THUMBS = BG_DIR / ".thumbs"
OUT = BG_DIR / "backgrounds.js"
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif"}
GRID = 12


# ── colour helpers ──
def rel_lum(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    hi, lo = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def from_hls(h, l, s):
    return tuple(round(c * 255) for c in colorsys.hls_to_rgb(h % 1, l, s))


def to_hls(rgb):
    return colorsys.rgb_to_hls(*(c / 255 for c in rgb))


def hue_dist(a, b):
    d = abs(a - b) % 1
    return min(d, 1 - d)


def lighten_until(h, l, s, against, ratio):
    """Raise lightness until the colour reaches `ratio` contrast against `against`."""
    rgb = from_hls(h, l, s)
    while contrast(rgb, against) < ratio and l < 0.97:
        l += 0.02
        rgb = from_hls(h, l, s)
    return rgb


def triplet(rgb):
    return ",".join(str(c) for c in rgb)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── analysis ──
def palette(img):
    q = img.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    total = img.width * img.height
    cols = []
    for count, idx in q.getcolors():
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        h, l, s = to_hls(rgb)
        cols.append({"rgb": rgb, "h": h, "l": l, "s": s, "share": count / total})

    def accent_score(c):
        return c["s"] * c["share"] ** 0.5 * (1 - abs(c["l"] - 0.5))

    ranked = sorted(cols, key=accent_score, reverse=True)
    a1 = ranked[0]
    a2 = next((c for c in ranked[1:] if hue_dist(c["h"], a1["h"]) > 0.08), None)
    h1 = a1["h"]
    h2 = a2["h"] if a2 else h1 + 0.1

    grey = max(c["s"] for c in cols) < 0.12
    s1 = 0.15 if grey else clamp(a1["s"], 0.35, 0.75)
    s2 = 0.15 if grey else clamp(a2["s"] if a2 else s1, 0.35, 0.75)

    darks = [c for c in cols if c["l"] < 0.35]
    base = max(darks, key=lambda c: c["share"]) if darks else a1
    bg = from_hls(base["h"], 0.075, min(base["s"], 0.3))
    surface = from_hls(base["h"], 0.13, min(base["s"], 0.3))  # worst case under cards

    accent = lighten_until(h1, 0.6, s1, surface, 4.5)
    accent2 = lighten_until(h2, 0.6, s2, surface, 4.5)
    text = lighten_until(h1, 0.82, min(s1, 0.3), surface, 7)
    return {"bg": triplet(bg), "accent": triplet(accent), "accent2": triplet(accent2), "text": triplet(text)}


def layout(img):
    grey = img.convert("L")
    edges = grey.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2))
    cw, ch = img.width / GRID, img.height / GRID
    cells = [[ImageStat.Stat(edges.crop((int(x * cw), int(y * ch), int((x + 1) * cw), int((y + 1) * ch)))).mean[0]
              for x in range(GRID)] for y in range(GRID)]

    # focal point: centroid of the busiest quarter of the image
    flat = sorted(v for row in cells for v in row)
    cut = flat[int(len(flat) * 0.75)]
    wsum = xs = ys = 0
    for y, row in enumerate(cells):
        for x, v in enumerate(row):
            if v >= cut:
                wsum += v
                xs += v * (x + 0.5)
                ys += v * (y + 0.5)
    fx, fy = (xs / wsum / GRID, ys / wsum / GRID) if wsum else (0.5, 0.5)

    # hero text goes in the calmest third of the band the hero will show
    band = [row for y, row in enumerate(cells) if abs((y + 0.5) / GRID - fy) <= 0.2] or cells
    thirds = [sum(row[x] for row in band for x in range(i * GRID // 3, (i + 1) * GRID // 3)) for i in range(3)]
    calm = min(range(3), key=thirds.__getitem__)
    if thirds[1] <= thirds[calm] * 1.25:
        calm = 1  # prefer centred unless the middle is clearly busier
    align = ["flex-start", "center", "flex-end"][calm]

    mean_l = ImageStat.Stat(grey).mean[0] / 255
    busy = clamp(ImageStat.Stat(edges).mean[0] / 40, 0, 1)
    return {
        "pos": f"{fx * 100:.0f}% {fy * 100:.0f}%",
        "align": align,
        "bright": round(clamp(0.16 / max(mean_l, 0.05), 0.25, 0.65), 2),
        "blur": round(6 + busy * 10),
        "surface": round(0.78 + busy * 0.12, 2),
    }


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)
    entries, keep = [], set()
    for f in sorted(BG_DIR.iterdir(), key=lambda p: p.name.lower()):
        if f.suffix.lower() not in EXTS or not f.is_file():
            continue
        try:
            with Image.open(f) as im:
                img = ImageOps.exif_transpose(im).convert("RGB")
        except Exception as e:
            print(f"skip {f.name}: {e}")
            continue
        small = img.copy()
        small.thumbnail((320, 320))
        thumb = THUMBS / (f.stem + ".webp")
        small.save(thumb, quality=80)
        keep.add(thumb.name)
        entries.append({"file": f.name, "thumb": f".thumbs/{thumb.name}", **palette(small), **layout(small)})
        print(f"{f.name}: accent rgb({entries[-1]['accent']}) align={entries[-1]['align']} pos={entries[-1]['pos']}")

    for t in THUMBS.iterdir():
        if t.name not in keep:
            t.unlink()
    js = ("// generated by update-backgrounds.py — re-run it after changing Background/\n"
          f"window.STARTPAGE_BACKGROUNDS = {json.dumps(entries, indent=2)};\n")
    # only write on change: the systemd path watcher on Background/ would re-trigger otherwise
    if OUT.exists() and OUT.read_text() == js:
        print(f"{OUT} unchanged ({len(entries)} backgrounds)")
        return
    OUT.write_text(js)
    print(f"wrote {OUT} ({len(entries)} backgrounds)")


if __name__ == "__main__":
    main()
