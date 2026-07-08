#!/usr/bin/env python3
"""Download official car brand SVG logos — corrected Wikimedia URLs."""
import urllib.request, os, time

OUT = os.path.dirname(os.path.abspath(__file__))

# Each entry: filename → list of URLs to try in order
LOGOS = {
    "nissan":       ["https://upload.wikimedia.org/wikipedia/commons/2/20/Nissan_2020_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/b/b8/Nissan_logo.svg"],
    "mazda":        ["https://upload.wikimedia.org/wikipedia/commons/e/e3/Mazda_logo_with_wordmark.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/7/70/Mazda.svg"],
    "ferrari":      ["https://upload.wikimedia.org/wikipedia/en/d/d1/Ferrari-Logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/8/8e/Ferrari-Logo.svg"],
    "porsche":      ["https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Porsche_logo.svg/640px-Porsche_logo.svg.png",
                     "https://upload.wikimedia.org/wikipedia/de/b/b4/Porsche-Logo.svg"],
    "lamborghini":  ["https://upload.wikimedia.org/wikipedia/commons/7/7a/Automobili_Lamborghini_S.p.A._Logo.svg"],
    "bentley":      ["https://upload.wikimedia.org/wikipedia/commons/6/60/Bentley_logo_and_wordmark.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/9/92/Bentley-Logo.svg"],
    "mclaren":      ["https://upload.wikimedia.org/wikipedia/commons/6/60/McLaren_Automotive_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/0/00/McLaren_logo.svg"],
    "aston-martin": ["https://upload.wikimedia.org/wikipedia/commons/2/28/Aston_Martin_logo_2.svg",
                     "https://upload.wikimedia.org/wikipedia/en/a/a2/Aston_Martin_Lagonda_logo.svg"],
    "alfa-romeo":   ["https://upload.wikimedia.org/wikipedia/commons/8/89/Alfa_Romeo_Logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/b/be/Alfa_Romeo_Logo.svg"],
    "mini":         ["https://upload.wikimedia.org/wikipedia/commons/7/7b/MINI_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/9/9f/Mini_logo.svg"],
    "mitsubishi":   ["https://upload.wikimedia.org/wikipedia/commons/6/64/Mitsubishi_motors_new_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/7/7e/Mitsubishi_logo.svg"],
    "chevrolet":    ["https://upload.wikimedia.org/wikipedia/commons/a/a3/Chevrolet_Gold_Bowtie_Logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/5/51/Chevrolet_Bowtie_1990s.svg"],
    "lexus":        ["https://upload.wikimedia.org/wikipedia/commons/3/3f/Lexus_division_emblem.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/b/b2/Lexus_division_emblem.svg"],
    "subaru":       ["https://upload.wikimedia.org/wikipedia/commons/9/90/Subaru_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/4/48/Subaru_logo.svg"],
    "suzuki":       ["https://upload.wikimedia.org/wikipedia/commons/f/f7/Suzuki_logo_2.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/1/12/Suzuki_logo_2.svg"],
    "isuzu":        ["https://upload.wikimedia.org/wikipedia/commons/7/77/Isuzu_Motors_Logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/b/bb/Isuzu_logo.svg"],
    "daihatsu":     ["https://upload.wikimedia.org/wikipedia/commons/5/5e/Daihatsu_logo.svg",
                     "https://upload.wikimedia.org/wikipedia/commons/5/52/Daihatsu_logo.svg"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120",
}

# Also re-download lamborghini and mercedes with correct file
LOGOS["lamborghini"] = ["https://upload.wikimedia.org/wikipedia/commons/7/7a/Automobili_Lamborghini_S.p.A._Logo.svg"]
LOGOS["mercedes"]    = ["https://upload.wikimedia.org/wikipedia/commons/6/67/Mercedes-Benz_logo_2010.svg",
                         "https://upload.wikimedia.org/wikipedia/commons/9/90/Mercedes-Logo.svg"]

ok, fail = [], []
for name, urls in LOGOS.items():
    dest = os.path.join(OUT, f"{name}.svg")
    success = False
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            # Sanity: must be SVG text, not huge HTML/PNG
            if len(data) > 2_000_000 or not (b"<svg" in data[:2000] or b"<?xml" in data[:200]):
                print(f"⚠️  {name:20s}  Skipping (not SVG or too large {len(data)}B)  {url}")
                continue
            with open(dest, "wb") as f:
                f.write(data)
            print(f"✅ {name:20s}  {len(data):7d}B  {url}")
            success = True
            ok.append(name)
            break
        except Exception as e:
            print(f"   {name:20s}  {e}  →  {url}")
        time.sleep(0.4)
    if not success:
        print(f"❌ {name:20s}  ALL URLS FAILED")
        fail.append(name)
    time.sleep(0.3)

print(f"\nDone: {len(ok)} OK, {len(fail)} failed")
if fail:
    print("Failed:", fail)
