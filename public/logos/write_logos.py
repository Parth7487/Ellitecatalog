#!/usr/bin/env python3
"""Write accurate, clean SVG logos for all car brands — transparent bg, brand colours."""
import os

OUT = os.path.dirname(os.path.abspath(__file__))

LOGOS = {

"nissan": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="none"/>
  <rect x="2" y="2" width="196" height="76" rx="6" fill="none" stroke="#C0C0C0" stroke-width="3"/>
  <rect x="30" y="32" width="140" height="16" rx="0" fill="#C0C0C0"/>
  <text x="100" y="47" text-anchor="middle" font-size="15" font-weight="700"
    fill="#1a1a1a" font-family="Arial,sans-serif" letter-spacing="3">NISSAN</text>
  <circle cx="100" cy="40" r="36" fill="none" stroke="#C0C0C0" stroke-width="3"/>
</svg>''',

"mazda": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
  <rect width="200" height="100" fill="none"/>
  <!-- Mazda M wing emblem -->
  <ellipse cx="100" cy="48" rx="72" ry="44" fill="none" stroke="#B22222" stroke-width="5"/>
  <path d="M100 10 Q68 28 54 48 Q68 68 100 86 Q132 68 146 48 Q132 28 100 10Z"
    fill="none" stroke="#B22222" stroke-width="5"/>
  <path d="M54 48 Q75 38 100 48 Q125 38 146 48"
    fill="none" stroke="#B22222" stroke-width="5"/>
</svg>''',

"ferrari": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 160">
  <rect width="120" height="160" fill="none"/>
  <!-- Shield shape -->
  <path d="M10 10 L110 10 L110 130 Q60 158 10 130 Z"
    fill="#FFCC00" stroke="#000" stroke-width="3"/>
  <!-- Italian stripe green -->
  <path d="M10 10 L38 10 L38 118 Q24 124 10 118 Z" fill="#009246"/>
  <!-- Italian stripe red -->
  <path d="M82 10 L110 10 L110 118 Q96 124 82 118 Z" fill="#CE2B37"/>
  <!-- Prancing horse body -->
  <path d="M60 118 C60 118 44 106 44 88 C44 72 52 62 60 60 C68 62 76 72 76 88 C76 106 60 118 60 118Z"
    fill="#000"/>
  <!-- Horse head/neck -->
  <path d="M55 68 C55 68 52 58 56 50 C58 46 62 44 66 46 C70 48 72 54 70 62"
    fill="none" stroke="#000" stroke-width="6" stroke-linecap="round"/>
  <!-- Tail -->
  <path d="M56 70 L48 55 L55 50" fill="none" stroke="#000" stroke-width="4" stroke-linecap="round"/>
  <!-- Legs -->
  <path d="M48 98 L44 112 M58 102 L56 118 M62 102 L64 118 M72 98 L76 112"
    stroke="#000" stroke-width="5" stroke-linecap="round" fill="none"/>
</svg>''',

"porsche": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 220">
  <rect width="200" height="220" fill="none"/>
  <!-- Outer shield -->
  <path d="M100 8 L190 50 L190 170 L100 212 L10 170 L10 50 Z"
    fill="#fff" stroke="#000" stroke-width="4"/>
  <!-- Vertical divider -->
  <line x1="100" y1="8" x2="100" y2="212" stroke="#000" stroke-width="4"/>
  <!-- Horizontal divider -->
  <line x1="10" y1="110" x2="190" y2="110" stroke="#000" stroke-width="4"/>
  <!-- Top-left antlers (red/black Württemberg) -->
  <rect x="14" y="14" width="42" height="92" fill="#C00"/>
  <rect x="20" y="20" width="12" height="80" fill="#fff"/>
  <rect x="38" y="20" width="12" height="80" fill="#fff"/>
  <!-- Top-right (gold) -->
  <rect x="104" y="14" width="82" height="92" fill="#D4AF37"/>
  <!-- Deer antler lines in gold section -->
  <line x1="145" y1="20" x2="145" y2="102" stroke="#000" stroke-width="3"/>
  <!-- Centre crest (horse) -->
  <circle cx="100" cy="110" r="36" fill="#fff" stroke="#000" stroke-width="3"/>
  <path d="M100 90 C100 90 86 100 86 114 C86 124 92 130 100 130 C108 130 114 124 114 114 C114 100 100 90 100 90Z"
    fill="#C00"/>
  <path d="M96 98 L92 90 L98 86" fill="none" stroke="#C00" stroke-width="4" stroke-linecap="round"/>
  <!-- Bottom halves (stripe pattern) -->
  <rect x="14" y="114" width="42" height="92" fill="#D4AF37"/>
  <rect x="104" y="114" width="82" height="92" fill="#fff"/>
  <line x1="120" y1="120" x2="170" y2="120" stroke="#000" stroke-width="3"/>
  <line x1="120" y1="134" x2="170" y2="134" stroke="#000" stroke-width="3"/>
  <line x1="120" y1="148" x2="170" y2="148" stroke="#000" stroke-width="3"/>
  <line x1="120" y1="162" x2="170" y2="162" stroke="#000" stroke-width="3"/>
  <line x1="120" y1="176" x2="170" y2="176" stroke="#000" stroke-width="3"/>
  <line x1="120" y1="190" x2="170" y2="190" stroke="#000" stroke-width="3"/>
  <text x="100" y="210" text-anchor="middle" font-size="11" font-weight="700"
    fill="#000" font-family="Arial,sans-serif" letter-spacing="2.5">PORSCHE</text>
</svg>''',

"bentley": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
  <rect width="200" height="100" fill="none"/>
  <!-- Wings left -->
  <path d="M5 50 Q20 22 50 32 Q65 38 80 48" fill="none" stroke="#B89A20" stroke-width="6" stroke-linecap="round"/>
  <path d="M5 50 Q20 78 50 68 Q65 62 80 52" fill="none" stroke="#B89A20" stroke-width="6" stroke-linecap="round"/>
  <!-- Wings right -->
  <path d="M195 50 Q180 22 150 32 Q135 38 120 48" fill="none" stroke="#B89A20" stroke-width="6" stroke-linecap="round"/>
  <path d="M195 50 Q180 78 150 68 Q135 62 120 52" fill="none" stroke="#B89A20" stroke-width="6" stroke-linecap="round"/>
  <!-- Center B -->
  <circle cx="100" cy="50" r="32" fill="#395222" stroke="#B89A20" stroke-width="4"/>
  <text x="100" y="60" text-anchor="middle" font-size="38" font-weight="900"
    fill="#B89A20" font-family="Georgia,Times New Roman,serif">B</text>
</svg>''',

"mclaren": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="none"/>
  <!-- McLaren speedmark: flowing orange arc -->
  <path d="M10 65 Q50 10 100 40 Q150 10 190 65"
    fill="none" stroke="#FF8000" stroke-width="12" stroke-linecap="round"/>
  <path d="M25 75 Q100 15 175 75"
    fill="none" stroke="#FF8000" stroke-width="5" stroke-linecap="round" opacity="0.4"/>
</svg>''',

"aston-martin": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 80">
  <rect width="260" height="80" fill="none"/>
  <!-- Wings -->
  <path d="M5 40 L24 22 L44 34 L65 18 L86 34 L104 24 L130 16 L156 24 L174 34 L195 18 L216 34 L236 22 L255 40"
    fill="none" stroke="#4CAF50" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="M5 40 L24 58 L44 46 L65 62 L86 46 L104 56 L130 64 L156 56 L174 46 L195 62 L216 46 L236 58 L255 40"
    fill="none" stroke="#4CAF50" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
  <!-- Center plate -->
  <rect x="90" y="26" width="80" height="28" rx="3" fill="#1a3a6a" stroke="#4CAF50" stroke-width="2"/>
  <text x="130" y="44" text-anchor="middle" font-size="10" font-weight="700"
    fill="#fff" font-family="Arial,sans-serif" letter-spacing="1">ASTON MARTIN</text>
</svg>''',

"alfa-romeo": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <!-- Outer ring -->
  <circle cx="60" cy="60" r="56" fill="#D00027"/>
  <circle cx="60" cy="60" r="56" fill="none" stroke="#fff" stroke-width="5"/>
  <!-- Vertical divider -->
  <line x1="60" y1="4" x2="60" y2="116" stroke="#fff" stroke-width="4"/>
  <!-- Left half: red cross on white -->
  <rect x="4" y="32" width="56" height="56" fill="#fff" opacity="0.12"/>
  <rect x="22" y="36" width="10" height="48" rx="2" fill="#fff"/>
  <rect x="14" y="54" width="42" height="10" rx="2" fill="#fff"/>
  <!-- Right half: serpent (Biscione) -->
  <path d="M64 38 C72 42 80 50 80 60 C80 72 72 78 64 82"
    fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>
  <path d="M64 38 C78 30 88 38 86 52 C84 62 74 66 64 62"
    fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
  <!-- Crown at top right -->
  <path d="M64 24 L70 18 L74 24 L80 16 L86 24 L90 18 L96 24"
    fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/>
</svg>''',

"mini": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <circle cx="60" cy="60" r="56" fill="#1a1a1a" stroke="#C5A028" stroke-width="5"/>
  <circle cx="60" cy="60" r="42" fill="none" stroke="#C5A028" stroke-width="3"/>
  <text x="60" y="67" text-anchor="middle" font-size="22" font-weight="900"
    fill="#fff" font-family="Arial,Helvetica,sans-serif" letter-spacing="2">MINI</text>
</svg>''',

"mitsubishi": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <!-- Three diamond Mitsubishi logo -->
  <!-- Top diamond -->
  <polygon points="60,5 75,35 60,28 45,35" fill="#E4001B"/>
  <!-- Left diamond -->
  <polygon points="27,38 60,28 60,58 27,68" fill="#E4001B"/>
  <!-- Right diamond -->
  <polygon points="93,38 60,28 60,58 93,68" fill="#E4001B"/>
  <!-- Bottom-left -->
  <polygon points="27,68 60,58 60,88 27,98" fill="#E4001B"/>
  <!-- Bottom-right -->
  <polygon points="93,68 60,58 60,88 93,98" fill="#E4001B"/>
</svg>''',

"chevrolet": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="none"/>
  <!-- Gold bowtie — left half -->
  <path d="M5 30 H76 V46 H36 V50 H76 V62 H5 V50 H28 V46 H5 Z" fill="#D4AF37"/>
  <!-- Gold bowtie — right half -->
  <path d="M84 30 H195 V46 H124 V50 H195 V62 H84 V50 H132 V46 H84 Z" fill="#D4AF37"/>
</svg>''',

"lexus": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <!-- Lexus ellipse -->
  <ellipse cx="60" cy="60" rx="56" ry="56" fill="none" stroke="#1a1a1a" stroke-width="5"/>
  <!-- Stylised L inside ellipse -->
  <text x="60" y="82" text-anchor="middle" font-size="68" font-weight="200"
    fill="#1a1a1a" font-family="Arial,Helvetica,sans-serif">L</text>
</svg>''',

"subaru": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <ellipse cx="60" cy="60" rx="56" ry="56" fill="#003B9D"/>
  <ellipse cx="60" cy="60" rx="56" ry="56" fill="none" stroke="#fff" stroke-width="4"/>
  <!-- Six Pleiades stars -->
  <circle cx="60" cy="60" r="9"  fill="#fff"/>
  <circle cx="33" cy="44" r="7"  fill="#fff"/>
  <circle cx="87" cy="44" r="7"  fill="#fff"/>
  <circle cx="20" cy="67" r="6"  fill="#fff"/>
  <circle cx="100" cy="67" r="6" fill="#fff"/>
  <circle cx="60" cy="30" r="6"  fill="#fff"/>
</svg>''',

"suzuki": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">
  <rect width="120" height="80" fill="none"/>
  <!-- Suzuki S badge -->
  <rect width="120" height="80" rx="6" fill="#003087"/>
  <text x="60" y="62" text-anchor="middle" font-size="70" font-weight="900"
    fill="#fff" font-family="Arial,Helvetica,sans-serif">S</text>
</svg>''',

"isuzu": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="none"/>
  <text x="100" y="62" text-anchor="middle" font-size="54" font-weight="900"
    fill="#CC0000" font-family="Arial,Helvetica,sans-serif" letter-spacing="-2">ISUZU</text>
</svg>''',

"daihatsu": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <!-- Daihatsu D letterform -->
  <path d="M24 12 L24 108 L60 108 Q96 108 96 60 Q96 12 60 12 Z"
    fill="none" stroke="#003087" stroke-width="8" stroke-linejoin="round"/>
  <path d="M24 28 L62 28 Q80 28 80 60 Q80 92 62 92 L24 92"
    fill="none" stroke="#003087" stroke-width="7"/>
</svg>''',

"lamborghini": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="none"/>
  <!-- Gold-bordered black shield -->
  <rect x="5" y="5" width="110" height="110" rx="6" fill="#1a1100" stroke="#D4AF37" stroke-width="5"/>
  <!-- Bull silhouette -->
  <path d="M36 76 C36 56 48 42 60 38 C72 42 84 56 84 76" fill="none" stroke="#D4AF37" stroke-width="6"/>
  <!-- Horns -->
  <path d="M38 70 L26 54 L36 46" fill="none" stroke="#D4AF37" stroke-width="5" stroke-linecap="round"/>
  <path d="M82 70 L94 54 L84 46" fill="none" stroke="#D4AF37" stroke-width="5" stroke-linecap="round"/>
  <!-- Body oval -->
  <ellipse cx="60" cy="82" rx="22" ry="14" fill="none" stroke="#D4AF37" stroke-width="4"/>
</svg>''',

}

ok = []
for name, content in LOGOS.items():
    dest = os.path.join(OUT, f"{name}.svg")
    # Only write if not already present (from earlier successful download)
    if not os.path.exists(dest):
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Wrote  {name}.svg")
        ok.append(name)
    else:
        print(f"⏩ Exists {name}.svg — skipping")

print(f"\nWrote {len(ok)} new logos")
print("Files now in dir:", sorted(os.listdir(OUT)))
