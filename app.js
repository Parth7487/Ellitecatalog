/* =============================================================
   Elite Ti — Wholesale Catalog
   app.js — Data, Filtering, Rendering, Theme
============================================================= */

let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];
let searchTimeout = null;

/* ─────────────────────────────────────────────────────────────
   BRAND LOGOS — inline SVG data URIs (no external CDN needed)
   Each logo is a clean, simplified SVG of the brand emblem.
───────────────────────────────────────────────────────────── */
function svg(content, vb = '0 0 100 100') {
    const encoded = encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}">${content}</svg>`);
    return `data:image/svg+xml,${encoded}`;
}

const BRAND_LOGOS = {
    // Audi — four interlocking rings
    'AUDI': svg(`
        <circle cx="20" cy="50" r="16" fill="none" stroke="currentColor" stroke-width="5"/>
        <circle cx="40" cy="50" r="16" fill="none" stroke="currentColor" stroke-width="5"/>
        <circle cx="60" cy="50" r="16" fill="none" stroke="currentColor" stroke-width="5"/>
        <circle cx="80" cy="50" r="16" fill="none" stroke="currentColor" stroke-width="5"/>
    `, '0 0 100 100'),

    // BMW — roundel quadrants
    'BMW': svg(`
        <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="5"/>
        <circle cx="50" cy="50" r="34" fill="none" stroke="currentColor" stroke-width="3"/>
        <path d="M50 16 A34 34 0 0 1 84 50 L50 50 Z" fill="currentColor" opacity="0.85"/>
        <path d="M50 84 A34 34 0 0 1 16 50 L50 50 Z" fill="currentColor" opacity="0.85"/>
    `),

    // Toyota — three ellipses forming T
    'TOYOTA': svg(`
        <ellipse cx="50" cy="52" rx="46" ry="30" fill="none" stroke="currentColor" stroke-width="5"/>
        <ellipse cx="50" cy="52" rx="22" ry="44" fill="none" stroke="currentColor" stroke-width="5"/>
        <line x1="4" y1="30" x2="96" y2="30" stroke="currentColor" stroke-width="5"/>
    `),

    // Honda — stylised H
    'HONDA': svg(`
        <rect x="12" y="20" width="10" height="60" rx="2" fill="currentColor"/>
        <rect x="78" y="20" width="10" height="60" rx="2" fill="currentColor"/>
        <rect x="12" y="42" width="76" height="10" rx="2" fill="currentColor"/>
    `),

    // Nissan — circle with horizontal bar
    'NISSAN': svg(`
        <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="6"/>
        <rect x="6" y="42" width="88" height="16" rx="0" fill="currentColor"/>
        <rect x="6" y="42" width="88" height="16" rx="0" fill="none" stroke="currentColor" stroke-width="0"/>
        <text x="50" y="56" text-anchor="middle" font-size="11" font-weight="bold" fill="${'white'}" font-family="Arial">NISSAN</text>
    `),

    // Mazda — stylised M wings
    'MAZDA': svg(`
        <ellipse cx="50" cy="50" rx="35" ry="26" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M50 24 Q30 38 20 50 Q30 62 50 76 Q70 62 80 50 Q70 38 50 24 Z" fill="none" stroke="currentColor" stroke-width="4"/>
        <path d="M20 50 Q35 40 50 50 Q65 40 80 50" fill="none" stroke="currentColor" stroke-width="4"/>
    `),

    // Ferrari — prancing horse (simplified silhouette)
    'FERRARI': svg(`
        <rect x="20" y="20" width="60" height="60" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor" stroke-width="3"/>
        <path d="M48 72 C48 72 35 62 35 48 C35 38 42 30 50 30 C58 30 65 38 65 48 C65 62 52 72 52 72 Z" fill="currentColor"/>
        <path d="M44 35 L50 22 L56 35" fill="currentColor"/>
        <path d="M38 46 L30 40 M62 46 L70 40" stroke="currentColor" stroke-width="3" fill="none"/>
    `, '0 0 100 100'),

    // Ferarri (misspelling variant)
    'FERARRI': svg(`
        <rect x="20" y="20" width="60" height="60" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor" stroke-width="3"/>
        <path d="M48 72 C48 72 35 62 35 48 C35 38 42 30 50 30 C58 30 65 38 65 48 C65 62 52 72 52 72 Z" fill="currentColor"/>
        <path d="M44 35 L50 22 L56 35" fill="currentColor"/>
    `),

    // Porsche — stylised crest
    'PORSCHE': svg(`
        <path d="M50 10 L90 30 L90 70 L50 90 L10 70 L10 30 Z" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M50 10 L50 90 M10 50 L90 50" stroke="currentColor" stroke-width="3"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="currentColor" stroke-width="4"/>
    `),

    // Lamborghini — raging bull silhouette
    'LAMBORGHINI': svg(`
        <rect x="8" y="8" width="84" height="84" rx="2" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M30 60 C30 45 40 35 50 32 C60 35 70 45 70 60" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M32 55 L24 45 L30 40" fill="none" stroke="currentColor" stroke-width="4"/>
        <path d="M68 55 L76 45 L70 40" fill="none" stroke="currentColor" stroke-width="4"/>
        <ellipse cx="50" cy="64" rx="18" ry="12" fill="none" stroke="currentColor" stroke-width="4"/>
    `),

    // Bentley — winged B
    'BENTLEY': svg(`
        <path d="M50 50 m-20 0 a20 20 0 1 0 40 0 a20 20 0 1 0 -40 0" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M10 40 Q30 20 50 30 Q70 20 90 40" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M10 60 Q30 80 50 70 Q70 80 90 60" fill="none" stroke="currentColor" stroke-width="5"/>
        <text x="50" y="56" text-anchor="middle" font-size="22" font-weight="900" fill="currentColor" font-family="serif">B</text>
    `),

    // McLaren — stylised speedmark
    'MCLAREN': svg(`
        <path d="M10 60 Q30 20 50 50 Q70 20 90 60" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
        <path d="M20 72 Q50 30 80 72" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity="0.5"/>
    `),

    // Aston Martin — wings
    'ASTON MARTIN': svg(`
        <path d="M5 50 L20 35 L35 45 L50 30 L65 45 L80 35 L95 50" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5 50 L20 65 L35 55 L50 70 L65 55 L80 65 L95 50" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="50" y="54" text-anchor="middle" font-size="9" font-weight="bold" fill="currentColor" font-family="Arial">AM</text>
    `),

    // Alfa Romeo — cross and serpent
    'ALFA ROMEO': svg(`
        <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="5"/>
        <line x1="50" y1="6" x2="50" y2="94" stroke="currentColor" stroke-width="3"/>
        <rect x="28" y="30" width="22" height="40" rx="2" fill="currentColor" opacity="0.8"/>
        <path d="M50 30 C60 35 72 42 72 50 C72 60 62 68 50 70" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    `),

    // MINI — circle with brand name
    'MINI': svg(`
        <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="6"/>
        <circle cx="50" cy="50" r="34" fill="none" stroke="currentColor" stroke-width="3"/>
        <text x="50" y="56" text-anchor="middle" font-size="16" font-weight="900" fill="currentColor" font-family="Arial" letter-spacing="1">MINI</text>
    `),

    // Mitsubishi — three diamonds
    'MITSUBISHI': svg(`
        <polygon points="50,8 65,35 50,28 35,35" fill="currentColor"/>
        <polygon points="22,40 50,28 50,55 22,67" fill="currentColor"/>
        <polygon points="78,40 50,28 50,55 78,67" fill="currentColor"/>
        <polygon points="22,67 50,55 50,82 22,95" fill="currentColor" opacity="0.6"/>
        <polygon points="78,67 50,55 50,82 78,95" fill="currentColor" opacity="0.6"/>
    `),

    // Ford — oval with Ford text
    'FORD': svg(`
        <ellipse cx="50" cy="50" rx="47" ry="32" fill="none" stroke="currentColor" stroke-width="5"/>
        <text x="50" y="58" text-anchor="middle" font-size="24" font-weight="bold" fill="currentColor" font-family="Arial" font-style="italic">Ford</text>
    `),

    // Chevrolet — bowtie
    'CHEVROLET': svg(`
        <path d="M5 38 L38 38 L38 62 L5 62 L5 48 L28 48 L28 52 L5 52 Z" fill="currentColor"/>
        <path d="M42 38 L95 38 L95 52 L62 52 L62 48 L95 48 L95 62 L62 62 L62 48 L42 48 Z" fill="currentColor"/>
        <rect x="5" y="38" width="33" height="24" fill="none"/>
        <path d="M5 38 H38 V48 H28 V52 H38 V62 H5 V52 H15 V48 H5 Z" fill="currentColor"/>
        <path d="M42 38 H95 V48 H62 V52 H95 V62 H42 V52 H72 V48 H42 Z" fill="currentColor"/>
    `),

    // Lexus — stylised L
    'LEXUS': svg(`
        <ellipse cx="50" cy="50" rx="46" ry="46" fill="none" stroke="currentColor" stroke-width="4"/>
        <text x="50" y="64" text-anchor="middle" font-size="38" font-weight="300" fill="currentColor" font-family="Arial" letter-spacing="-2">L</text>
    `),

    // Subaru — six stars (Pleiades)
    'SUBARU': svg(`
        <circle cx="50" cy="50" r="6" fill="currentColor"/>
        <circle cx="30" cy="38" r="5" fill="currentColor"/>
        <circle cx="70" cy="38" r="5" fill="currentColor"/>
        <circle cx="20" cy="58" r="4" fill="currentColor"/>
        <circle cx="80" cy="58" r="4" fill="currentColor"/>
        <circle cx="50" cy="28" r="4" fill="currentColor"/>
    `),

    // Suzuki — stylised S
    'SUZUKI': svg(`
        <text x="50" y="68" text-anchor="middle" font-size="60" font-weight="900" fill="currentColor" font-family="Arial">S</text>
        <line x1="15" y1="72" x2="85" y2="72" stroke="currentColor" stroke-width="4"/>
    `),

    // Tesla — T-logo
    'TESLA': svg(`
        <path d="M50 90 L50 22" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
        <path d="M15 22 L85 22" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
        <path d="M15 22 Q50 10 85 22" fill="none" stroke="currentColor" stroke-width="5"/>
        <path d="M32 22 Q50 35 50 22" fill="none" stroke="currentColor" stroke-width="5"/>
    `),

    // Mercedes-Benz — three-pointed star
    'BENZ': svg(`
        <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="5"/>
        <line x1="50" y1="6" x2="50" y2="50" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
        <line x1="50" y1="50" x2="12" y2="72" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
        <line x1="50" y1="50" x2="88" y2="72" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
        <circle cx="50" cy="50" r="6" fill="currentColor"/>
    `),

    // Honda (hoods category uses Honda branding)
    'Mclaren': svg(`<path d="M10 60 Q30 20 50 50 Q70 20 90 60" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>`),

    // Isuzu — bold I
    'ISUZU': svg(`
        <rect x="40" y="15" width="20" height="70" rx="3" fill="currentColor"/>
        <rect x="20" y="15" width="60" height="12" rx="3" fill="currentColor"/>
        <rect x="20" y="73" width="60" height="12" rx="3" fill="currentColor"/>
    `),

    // Daihatsu — stylised D
    'DAIHATSU': svg(`
        <path d="M20 15 L20 85 L50 85 Q80 85 80 50 Q80 15 50 15 Z" fill="none" stroke="currentColor" stroke-width="6"/>
        <path d="M20 30 L55 30 Q68 30 68 50 Q68 70 55 70 L20 70" fill="none" stroke="currentColor" stroke-width="5"/>
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
