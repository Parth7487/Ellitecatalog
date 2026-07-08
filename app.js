/* =============================================================
   Elite Ti — Wholesale Catalog
   app.js — Data, Filtering, Rendering, Theme
============================================================= */

let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];
let searchTimeout = null;

/* ─────────────────────────────────────────────────────────────
   BRAND LOGOS — inline SVG data URIs in real brand colours
   No CDN, no network, always visible.
───────────────────────────────────────────────────────────── */
function svg(content, vb = '0 0 100 100') {
    const encoded = encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}">${content}</svg>`);
    return `data:image/svg+xml,${encoded}`;
}

const BRAND_LOGOS = {

    // ── AUDI — four silver rings ──────────────────────────────
    'AUDI': svg(`
      <rect width="100" height="100" fill="#000"/>
      <circle cx="18" cy="50" r="14" fill="none" stroke="#C0C0C0" stroke-width="4.5"/>
      <circle cx="36" cy="50" r="14" fill="none" stroke="#C0C0C0" stroke-width="4.5"/>
      <circle cx="54" cy="50" r="14" fill="none" stroke="#C0C0C0" stroke-width="4.5"/>
      <circle cx="72" cy="50" r="14" fill="none" stroke="#C0C0C0" stroke-width="4.5"/>
    `, '0 0 90 100'),

    // ── BMW — blue & white roundel ────────────────────────────
    'BMW': svg(`
      <circle cx="50" cy="50" r="48" fill="#1C69D4"/>
      <circle cx="50" cy="50" r="48" fill="none" stroke="#fff" stroke-width="6"/>
      <circle cx="50" cy="50" r="33" fill="none" stroke="#fff" stroke-width="5"/>
      <path d="M50 17 A33 33 0 0 1 83 50 L50 50 Z" fill="#fff"/>
      <path d="M50 83 A33 33 0 0 1 17 50 L50 50 Z" fill="#fff"/>
    `),

    // ── TOYOTA — red three-ellipse emblem ────────────────────
    'TOYOTA': svg(`
      <rect width="100" height="100" fill="#EB0A1E" rx="8"/>
      <ellipse cx="50" cy="54" rx="40" ry="26" fill="none" stroke="#fff" stroke-width="4.5"/>
      <ellipse cx="50" cy="54" rx="18" ry="38" fill="none" stroke="#fff" stroke-width="4.5"/>
      <line x1="10" y1="28" x2="90" y2="28" stroke="#fff" stroke-width="4.5"/>
    `),

    // ── HONDA — red H on white ────────────────────────────────
    'HONDA': svg(`
      <rect width="100" height="100" fill="#E40521" rx="6"/>
      <rect x="14" y="22" width="11" height="56" rx="2" fill="#fff"/>
      <rect x="75" y="22" width="11" height="56" rx="2" fill="#fff"/>
      <rect x="14" y="43" width="72" height="11" rx="2" fill="#fff"/>
    `),

    // ── NISSAN — silver/dark badge ────────────────────────────
    'NISSAN': svg(`
      <rect width="100" height="100" fill="#1a1a1a" rx="6"/>
      <circle cx="50" cy="50" r="44" fill="none" stroke="#C0C0C0" stroke-width="5"/>
      <rect x="6" y="41" width="88" height="18" fill="#1a1a1a" stroke="#C0C0C0" stroke-width="3"/>
      <text x="50" y="56" text-anchor="middle" font-size="11" font-weight="bold" fill="#C0C0C0" font-family="Arial,sans-serif" letter-spacing="1">NISSAN</text>
    `),

    // ── MAZDA — red wing emblem ───────────────────────────────
    'MAZDA': svg(`
      <rect width="100" height="100" fill="#E30613" rx="6"/>
      <ellipse cx="50" cy="50" rx="40" ry="28" fill="none" stroke="#fff" stroke-width="4"/>
      <path d="M50 22 Q28 36 18 50 Q28 64 50 78 Q72 64 82 50 Q72 36 50 22Z" fill="none" stroke="#fff" stroke-width="4"/>
      <path d="M18 50 Q34 42 50 50 Q66 42 82 50" fill="none" stroke="#fff" stroke-width="3.5"/>
    `),

    // ── FERRARI — yellow shield with black horse ──────────────
    'FERRARI': svg(`
      <path d="M10 5 L90 5 L90 80 Q50 100 10 80 Z" fill="#FFCC00" stroke="#000" stroke-width="3"/>
      <rect x="10" y="5" width="32" height="38" fill="#009246"/>
      <rect x="58" y="5" width="32" height="38" fill="#CE2B37"/>
      <path d="M50 70 C50 70 38 60 38 48 C38 38 44 32 50 32 C56 32 62 38 62 48 C62 60 50 70 50 70Z" fill="#000"/>
      <path d="M46 35 L50 24 L54 35" fill="#000"/>
      <path d="M38 46 L30 40 M62 46 L70 40" stroke="#000" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    `),

    // ── FERARRI (typo variant) ────────────────────────────────
    'FERARRI': svg(`
      <path d="M10 5 L90 5 L90 80 Q50 100 10 80 Z" fill="#FFCC00" stroke="#000" stroke-width="3"/>
      <path d="M50 70 C50 70 38 60 38 48 C38 38 44 32 50 32 C56 32 62 38 62 48 C62 60 50 70 50 70Z" fill="#000"/>
      <path d="M46 35 L50 24 L54 35" fill="#000"/>
    `),

    // ── PORSCHE — multicolour crest ───────────────────────────
    'PORSCHE': svg(`
      <path d="M50 4 L92 28 L92 72 L50 96 L8 72 L8 28 Z" fill="#AE9142" stroke="#000" stroke-width="2"/>
      <path d="M50 4 L50 96" stroke="#000" stroke-width="3"/>
      <path d="M8 50 L92 50" stroke="#000" stroke-width="3"/>
      <circle cx="50" cy="50" r="20" fill="#000"/>
      <circle cx="50" cy="50" r="15" fill="#C0392B"/>
      <path d="M50 35 L50 50 L38 44" fill="#fff"/>
      <text x="50" y="88" text-anchor="middle" font-size="7" font-weight="bold" fill="#000" font-family="Arial">PORSCHE</text>
    `),

    // ── LAMBORGHINI — gold/black badge ───────────────────────
    'LAMBORGHINI': svg(`
      <rect width="100" height="100" fill="#1a1100" rx="4" stroke="#D4AF37" stroke-width="4"/>
      <path d="M30 62 C30 46 40 36 50 33 C60 36 70 46 70 62" fill="none" stroke="#D4AF37" stroke-width="5"/>
      <path d="M32 57 L22 45 L30 39" fill="none" stroke="#D4AF37" stroke-width="3.5" stroke-linecap="round"/>
      <path d="M68 57 L78 45 L70 39" fill="none" stroke="#D4AF37" stroke-width="3.5" stroke-linecap="round"/>
      <ellipse cx="50" cy="65" rx="17" ry="11" fill="none" stroke="#D4AF37" stroke-width="3.5"/>
    `),

    // ── BENTLEY — dark green winged B ─────────────────────────
    'BENTLEY': svg(`
      <rect width="100" height="100" fill="#3D5A1E" rx="6"/>
      <path d="M8 40 Q28 20 50 30 Q72 20 92 40" fill="none" stroke="#C5A028" stroke-width="5" stroke-linecap="round"/>
      <path d="M8 60 Q28 80 50 70 Q72 80 92 60" fill="none" stroke="#C5A028" stroke-width="5" stroke-linecap="round"/>
      <circle cx="50" cy="50" r="18" fill="none" stroke="#C5A028" stroke-width="4"/>
      <text x="50" y="57" text-anchor="middle" font-size="22" font-weight="900" fill="#C5A028" font-family="Georgia,serif">B</text>
    `),

    // ── McLAREN — orange speedmark ────────────────────────────
    'MCLAREN': svg(`
      <rect width="100" height="100" fill="#1a1a1a" rx="6"/>
      <path d="M8 62 Q30 18 50 50 Q70 18 92 62" fill="none" stroke="#FF8000" stroke-width="9" stroke-linecap="round"/>
      <path d="M18 74 Q50 28 82 74" fill="none" stroke="#FF8000" stroke-width="4.5" stroke-linecap="round" opacity="0.5"/>
    `),

    // ── ASTON MARTIN — dark green wings ──────────────────────
    'ASTON MARTIN': svg(`
      <rect width="100" height="100" fill="#003153" rx="6"/>
      <path d="M4 50 L18 36 L32 46 L50 28 L68 46 L82 36 L96 50" fill="none" stroke="#C5A028" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M4 50 L18 64 L32 54 L50 72 L68 54 L82 64 L96 50" fill="none" stroke="#C5A028" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="34" y="42" width="32" height="16" rx="2" fill="#C5A028"/>
      <text x="50" y="54" text-anchor="middle" font-size="8" font-weight="bold" fill="#003153" font-family="Arial,sans-serif">AM</text>
    `),

    // ── ALFA ROMEO — red/white circular badge ─────────────────
    'ALFA ROMEO': svg(`
      <circle cx="50" cy="50" r="48" fill="#D40000"/>
      <circle cx="50" cy="50" r="48" fill="none" stroke="#fff" stroke-width="4"/>
      <line x1="50" y1="2" x2="50" y2="98" stroke="#fff" stroke-width="4"/>
      <rect x="8" y="28" width="20" height="44" rx="2" fill="#fff"/>
      <path d="M50 28 Q60 34 64 42 Q68 50 64 58 Q60 66 50 72" fill="#fff" stroke="none"/>
      <circle cx="15" cy="22" r="4" fill="#fff"/>
    `),

    // ── MINI — circular badge ─────────────────────────────────
    'MINI': svg(`
      <circle cx="50" cy="50" r="48" fill="#1a1a1a" stroke="#C5A028" stroke-width="5"/>
      <circle cx="50" cy="50" r="35" fill="none" stroke="#C5A028" stroke-width="3"/>
      <text x="50" y="56" text-anchor="middle" font-size="16" font-weight="900" fill="#fff" font-family="Arial,sans-serif" letter-spacing="1.5">MINI</text>
    `),

    // ── MITSUBISHI — three red diamonds ──────────────────────
    'MITSUBISHI': svg(`
      <rect width="100" height="100" fill="#fff" rx="6"/>
      <polygon points="50,6 62,28 50,22 38,28" fill="#E4001B"/>
      <polygon points="24,38 50,22 50,52 24,66" fill="#E4001B"/>
      <polygon points="76,38 50,22 50,52 76,66" fill="#E4001B"/>
      <polygon points="24,66 50,52 50,78 24,94" fill="#E4001B"/>
      <polygon points="76,66 50,52 50,78 76,94" fill="#E4001B"/>
    `),

    // ── FORD — blue oval ──────────────────────────────────────
    'FORD': svg(`
      <rect width="100" height="100" fill="#003099" rx="8"/>
      <ellipse cx="50" cy="50" rx="44" ry="30" fill="none" stroke="#fff" stroke-width="4"/>
      <text x="50" y="59" text-anchor="middle" font-size="26" font-weight="bold" fill="#fff" font-family="Arial,sans-serif" font-style="italic">Ford</text>
    `),

    // ── CHEVROLET — gold/black bowtie ────────────────────────
    'CHEVROLET': svg(`
      <rect width="100" height="100" fill="#1a1a1a" rx="6"/>
      <path d="M5 40 H38 V50 H18 V54 H38 V62 H5 V54 H16 V50 H5 Z" fill="#D4AF37"/>
      <path d="M42 40 H95 V50 H62 V54 H95 V62 H42 V54 H72 V50 H42 Z" fill="#D4AF37"/>
    `),

    // ── LEXUS — black oval with L ─────────────────────────────
    'LEXUS': svg(`
      <rect width="100" height="100" fill="#1a1a1a" rx="6"/>
      <ellipse cx="50" cy="50" rx="44" ry="44" fill="none" stroke="#C0C0C0" stroke-width="4"/>
      <text x="50" y="66" text-anchor="middle" font-size="48" font-weight="200" fill="#C0C0C0" font-family="Arial,sans-serif">L</text>
    `),

    // ── SUBARU — blue with six Pleiades stars ─────────────────
    'SUBARU': svg(`
      <rect width="100" height="100" fill="#003B9D" rx="6"/>
      <circle cx="50" cy="50" r="8"  fill="#fff"/>
      <circle cx="28" cy="37" r="6.5" fill="#fff"/>
      <circle cx="72" cy="37" r="6.5" fill="#fff"/>
      <circle cx="18" cy="58" r="5"  fill="#fff"/>
      <circle cx="82" cy="58" r="5"  fill="#fff"/>
      <circle cx="50" cy="26" r="5"  fill="#fff"/>
    `),

    // ── SUZUKI — blue S badge ─────────────────────────────────
    'SUZUKI': svg(`
      <rect width="100" height="100" fill="#003087" rx="6"/>
      <text x="50" y="70" text-anchor="middle" font-size="68" font-weight="900" fill="#fff" font-family="Arial,sans-serif">S</text>
    `),

    // ── TESLA — red T mark ────────────────────────────────────
    'TESLA': svg(`
      <rect width="100" height="100" fill="#E31937" rx="6"/>
      <path d="M50 88 L50 24" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
      <path d="M14 24 L86 24" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
      <path d="M14 24 Q50 10 86 24" fill="none" stroke="#fff" stroke-width="6"/>
      <path d="M32 24 Q50 36 50 24" fill="none" stroke="#E31937" stroke-width="5"/>
    `),

    // ── MERCEDES-BENZ — silver three-point star ───────────────
    'BENZ': svg(`
      <circle cx="50" cy="50" r="48" fill="#fff" stroke="#C0C0C0" stroke-width="4"/>
      <circle cx="50" cy="50" r="36" fill="none" stroke="#C0C0C0" stroke-width="3"/>
      <line x1="50" y1="14" x2="50" y2="50" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>
      <line x1="50" y1="50" x2="18" y2="68" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>
      <line x1="50" y1="50" x2="82" y2="68" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>
      <circle cx="50" cy="50" r="7" fill="#1a1a1a"/>
    `),

    // ── ISUZU — red I-beam ────────────────────────────────────
    'ISUZU': svg(`
      <rect width="100" height="100" fill="#CC0000" rx="6"/>
      <rect x="38" y="15" width="24" height="70" rx="2" fill="#fff"/>
      <rect x="18" y="15" width="64" height="14" rx="2" fill="#fff"/>
      <rect x="18" y="71" width="64" height="14" rx="2" fill="#fff"/>
    `),

    // ── DAIHATSU — blue D ─────────────────────────────────────
    'DAIHATSU': svg(`
      <rect width="100" height="100" fill="#003087" rx="6"/>
      <path d="M22 15 L22 85 L54 85 Q82 85 82 50 Q82 15 54 15 Z" fill="none" stroke="#fff" stroke-width="6"/>
      <path d="M22 30 L56 30 Q70 30 70 50 Q70 70 56 70 L22 70" fill="none" stroke="#fff" stroke-width="5"/>
    `),
};


/* Normalise brand key lookup (handles "Mclaren", "Ferarri" variants) */
function getBrandLogoUrl(brandRaw) {
    const key = String(brandRaw).toUpperCase().trim();
    return BRAND_LOGOS[key] || null;
}

/* Build an inline SVG IMG tag for the brand (auto-coloured via CSS filter) */
function getBrandLogoHTML(brandRaw) {
    const url = getBrandLogoUrl(brandRaw);
    if (!url) return '';
    return `<img src="${url}" alt="${brandRaw}" class="brand-logo" loading="lazy">`;
}

/* ─────────────────────────────────────────────────────────────
   THEME
───────────────────────────────────────────────────────────── */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const logo       = document.getElementById('site-logo');
    const darkLabel  = document.getElementById('lever-dark-label');
    const lightLabel = document.getElementById('lever-light-label');

    if (theme === 'dark') {
        if (logo) logo.src = 'public/logo-white-green.svg';
        if (darkLabel)  { darkLabel.classList.add('active'); }
        if (lightLabel) { lightLabel.classList.remove('active'); }
    } else {
        if (logo) logo.src = 'public/logo-black-green.svg';
        if (darkLabel)  { darkLabel.classList.remove('active'); }
        if (lightLabel) { lightLabel.classList.add('active'); }
    }

    localStorage.setItem('eti-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next    = current === 'dark' ? 'light' : 'dark';
    const curtain = document.getElementById('curtain-overlay');

    if (!curtain) { applyTheme(next); return; }

    // Phase 1: sweep curtain IN
    curtain.classList.remove('opening');
    curtain.classList.add('closing');

    // Phase 2: apply theme while curtain is fully closed
    setTimeout(() => {
        applyTheme(next);
    }, 440);

    // Phase 3: sweep curtain OUT
    setTimeout(() => {
        curtain.classList.remove('closing');
        curtain.classList.add('opening');
    }, 480);

    // Phase 4: reset
    setTimeout(() => {
        curtain.classList.remove('opening');
    }, 940);
}

/* Restore saved theme on load */
(function initTheme() {
    const saved = localStorage.getItem('eti-theme') || 'dark';
    applyTheme(saved);
})();

/* ─────────────────────────────────────────────────────────────
   DATA INIT
───────────────────────────────────────────────────────────── */
async function init() {
    try {
        const response = await fetch(`data.json?v=${Date.now()}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        allData = await response.json();

        // Normalise brand keys (handle "Ferarri", "Mclaren" etc.)
        ['kits', 'hoods'].forEach(cat => {
            allData[cat] = allData[cat].map(item => ({
                ...item,
                _brandNorm: String(item.Brand || item.Category || '').toUpperCase().trim(),
            }));
        });

        initializeSelects();
        switchCategory('kits');
    } catch (error) {
        console.error('CRITICAL: Data could not be loaded.', error);
        document.getElementById('catalog-body').innerHTML = `
            <tr>
                <td colspan="4" style="padding:60px 24px;text-align:center">
                    <p style="color:#ef4444;font-weight:800;font-size:13px;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:16px">
                        Error: ${error.message}
                    </p>
                    <button onclick="location.reload()" style="border:2px solid currentColor;padding:8px 24px;font-size:10px;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;cursor:pointer;background:none;color:inherit">
                        Retry
                    </button>
                </td>
            </tr>
        `;
    }
}

/* ─────────────────────────────────────────────────────────────
   FILTER DROPDOWNS
───────────────────────────────────────────────────────────── */
function initializeSelects() {
    populateSelect('brand-filter', 'Brand', 'Category', 'Make');
    syncDependentFilters();
}

function syncDependentFilters() {
    const brand = document.getElementById('brand-filter').value;
    const model = document.getElementById('model-filter').value;

    const dataForModel = allData[currentCategory].filter(item =>
        brand === '' || (item.Brand || item.Category) === brand
    );
    populateSelect('model-filter', 'Model', null, 'Model', dataForModel);

    const dataForPart = dataForModel.filter(item =>
        model === '' || item.Model === model
    );
    populateSelect('part-filter', 'Part', 'Category', 'Part', dataForPart);
}

function populateSelect(id, optKey, altKey, label, datasource = null) {
    const select = document.getElementById(id);
    const source = datasource || allData[currentCategory];
    const options = new Set();

    source.forEach(item => {
        const val = item[optKey] || (altKey ? item[altKey] : null);
        if (val && String(val).trim() !== '') options.add(val);
    });

    const sorted = Array.from(options).sort();
    const currentVal = select.value;

    select.innerHTML = `<option value="">${label}</option>`;
    sorted.forEach(opt => {
        const el = document.createElement('option');
        el.value = opt;
        el.textContent = opt;
        if (opt === currentVal) el.selected = true;
        select.appendChild(el);
    });
}

/* ─────────────────────────────────────────────────────────────
   CATEGORY SWITCH
───────────────────────────────────────────────────────────── */
function switchCategory(category) {
    currentCategory = category;

    const kitsTab  = document.getElementById('tab-kits');
    const hoodsTab = document.getElementById('tab-hoods');

    if (category === 'kits') {
        kitsTab.classList.replace('inactive', 'active');
        kitsTab.setAttribute('aria-pressed', 'true');
        hoodsTab.classList.replace('active', 'inactive');
        hoodsTab.setAttribute('aria-pressed', 'false');
    } else {
        hoodsTab.classList.replace('inactive', 'active');
        hoodsTab.setAttribute('aria-pressed', 'true');
        kitsTab.classList.replace('active', 'inactive');
        kitsTab.setAttribute('aria-pressed', 'false');
    }

    resetFilters(false);
    initializeSelects();
    handleFilter();

    // Smooth scroll to table top
    document.getElementById('catalog-top').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ─────────────────────────────────────────────────────────────
   RESET
───────────────────────────────────────────────────────────── */
function resetFilters(trigger = true) {
    ['global-search', 'brand-filter', 'model-filter', 'part-filter', 'min-price', 'max-price'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    if (trigger) {
        initializeSelects();
        handleFilter();
    }
}

/* ─────────────────────────────────────────────────────────────
   FILTER (debounced)
───────────────────────────────────────────────────────────── */
function handleFilter() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        executeFilter();
        syncDependentFilters();
    }, 150);
}

function executeFilter() {
    const search = document.getElementById('global-search').value.toLowerCase();
    const brand  = document.getElementById('brand-filter').value;
    const model  = document.getElementById('model-filter').value;
    const part   = document.getElementById('part-filter').value;
    const minP   = parseFloat(document.getElementById('min-price').value) || 0;
    const maxP   = parseFloat(document.getElementById('max-price').value) || Infinity;

    filteredData = allData[currentCategory].filter(item => {
        const itemBrand = String(item.Brand || item.Category || '');
        const itemModel = String(item.Model || '');
        const itemPart  = String(item.Part  || item.Category || '');
        const itemStyle = String(item.Style || '');
        const priceNum  = parseFloat(item.Price) || 0;

        const matchesSearch = search === '' ||
            itemBrand.toLowerCase().includes(search) ||
            itemModel.toLowerCase().includes(search) ||
            itemPart.toLowerCase().includes(search)  ||
            itemStyle.toLowerCase().includes(search) ||
            String(item.SKU || '').toLowerCase().includes(search);

        return matchesSearch &&
               (brand === '' || itemBrand === brand) &&
               (model === '' || itemModel === model) &&
               (part  === '' || itemPart  === part)  &&
               (priceNum >= minP && priceNum <= maxP);
    });

    renderTable();
}

/* ─────────────────────────────────────────────────────────────
   RENDER
───────────────────────────────────────────────────────────── */
function renderTable() {
    const body       = document.getElementById('catalog-body');
    const emptyState = document.getElementById('empty-state');
    const badge      = document.getElementById('results-count-badge');
    const label      = document.getElementById('results-label');

    body.innerHTML = '';

    // Update results count
    badge.textContent = filteredData.length.toLocaleString();
    label.textContent = filteredData.length === 1 ? 'result' : 'results';

    if (filteredData.length === 0) {
        emptyState.classList.add('visible');
        return;
    }
    emptyState.classList.remove('visible');

    const fragment = document.createDocumentFragment();

    filteredData.forEach((item, i) => {
        const brand    = String(item.Brand || item.Category || '');
        const model    = String(item.Model || '');
        const style    = String(item.Style || '');
        const part     = String(item.Part  || item.Category || '');
        const priceNum = parseFloat(item.Price);
        const brandLogoHTML = getBrandLogoHTML(brand);

        const priceHTML = priceNum > 0
            ? `$${priceNum.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
            : `<span class="price-enquire">Enquire</span>`;

        const styleHTML = style && style !== model && !part.includes(style)
            ? `<span class="part-style">[${style} Design]</span>`
            : '';


        const tr = document.createElement('tr');
        tr.style.animationDelay = `${Math.min(i * 12, 300)}ms`;
        tr.innerHTML = `
            <td data-label="Make">
                <div class="brand-cell">
                    ${brandLogoHTML}
                    <span class="brand-name">${brand}</span>
                </div>
            </td>
            <td data-label="Model" class="model-col">${model}</td>
            <td data-label="Part / Description" class="part-col">${part}${styleHTML}</td>
            <td data-label="Wholesale Price" class="price-col">${priceHTML}</td>
        `;
        fragment.appendChild(tr);
    });

    body.appendChild(fragment);
}

/* ─────────────────────────────────────────────────────────────
   BOOT
───────────────────────────────────────────────────────────── */
init();
