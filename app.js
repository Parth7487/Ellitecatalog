/* =============================================================
   Elite Ti — Wholesale Catalog
   app.js — Data, Filtering, Rendering, Theme
============================================================= */

let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];
let searchTimeout = null;

/* ─────────────────────────────────────────────────────────────
   BRAND LOGO MAP
   Uses brand-specific SVG logo URLs from Wikipedia / CDN
   that are widely reliable.
───────────────────────────────────────────────────────────── */
// jsDelivr-hosted car makes icons (MIT licensed, no hotlink blocking)
const CDN = 'https://cdn.jsdelivr.net/gh/dangnelson/car-makes-icons/svgs/';

const BRAND_LOGOS = {
    'ALFA ROMEO':   CDN + 'alfa-romeo.svg',
    'ASTON MARTIN': CDN + 'aston-martin.svg',
    'AUDI':         CDN + 'audi.svg',
    'BENTLEY':      CDN + 'bentley.svg',
    'BENZ':         CDN + 'mercedes-benz.svg',
    'BMW':          CDN + 'bmw.svg',
    'CHEVROLET':    CDN + 'chevrolet.svg',
    'DAIHATSU':     CDN + 'daihatsu.svg',
    'FERRARI':      CDN + 'ferrari.svg',
    'FERARRI':      CDN + 'ferrari.svg',
    'FORD':         CDN + 'ford.svg',
    'HONDA':        CDN + 'honda.svg',
    'ISUZU':        CDN + 'isuzu.svg',
    'LAMBORGHINI':  CDN + 'lamborghini.svg',
    'LEXUS':        CDN + 'lexus.svg',
    'MAZDA':        CDN + 'mazda.svg',
    'MCLAREN':      CDN + 'mclaren.svg',
    'MINI':         CDN + 'mini.svg',
    'MITSUBISHI':   CDN + 'mitsubishi.svg',
    'NISSAN':       CDN + 'nissan.svg',
    'PORSCHE':      CDN + 'porsche.svg',
    'SUBARU':       CDN + 'subaru.svg',
    'SUZUKI':       CDN + 'suzuki.svg',
    'TESLA':        CDN + 'tesla.svg',
    'TOYOTA':       CDN + 'toyota.svg',
};

/* Normalise brand key lookup (handles "Mclaren", "Ferarri" variants) */
function getBrandLogoUrl(brandRaw) {
    const key = String(brandRaw).toUpperCase().trim();
    return BRAND_LOGOS[key] || null;
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
        const logoUrl  = getBrandLogoUrl(brand);

        const priceHTML = priceNum > 0
            ? `$${priceNum.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
            : `<span class="price-enquire">Enquire</span>`;

        const styleHTML = style && style !== model && !part.includes(style)
            ? `<span class="part-style">[${style} Design]</span>`
            : '';

        const brandLogoHTML = logoUrl
            ? `<img src="${logoUrl}" alt="${brand} logo" class="brand-logo" loading="lazy" onerror="this.style.display='none'">`
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
