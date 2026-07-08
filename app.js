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
const BRAND_LOGOS = {
    'ALFA ROMEO':   'https://cdn.jsdelivr.net/gh/nicholasgasior/brand-logos@master/brand-logos/alfa-romeo.svg',
    'ASTON MARTIN': 'https://www.carlogos.org/logo/Aston-Martin-logo-2003-1920x1080.png',
    'AUDI':         'https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Audi-Logo_2016.svg/240px-Audi-Logo_2016.svg.png',
    'BENTLEY':      'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Bentley_logo.svg/240px-Bentley_logo.svg.png',
    'BENZ':         'https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Mercedes-Logo.svg/240px-Mercedes-Logo.svg.png',
    'BMW':          'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/BMW.svg/240px-BMW.svg.png',
    'CHEVROLET':    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Chevrolet_logo.svg/240px-Chevrolet_logo.svg.png',
    'DAIHATSU':     'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Daihatsu_logo.svg/240px-Daihatsu_logo.svg.png',
    'FERRARI':      'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Ferrari_logo.svg/240px-Ferrari_logo.svg.png',
    'FERARRI':      'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Ferrari_logo.svg/240px-Ferrari_logo.svg.png',
    'FORD':         'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Ford_logo_flat.svg/240px-Ford_logo_flat.svg.png',
    'HONDA':        'https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Honda.svg/240px-Honda.svg.png',
    'ISUZU':        'https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Isuzu_logo.svg/240px-Isuzu_logo.svg.png',
    'LAMBORGHINI':  'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Lamborghini_logo.svg/240px-Lamborghini_logo.svg.png',
    'LEXUS':        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Lexus_division_wordmark.svg/240px-Lexus_division_wordmark.svg.png',
    'MAZDA':        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Mazda_logo.svg/240px-Mazda_logo.svg.png',
    'MCLAREN':      'https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/McLaren_Automotive_logo.svg/240px-McLaren_Automotive_logo.svg.png',
    'MCLAREN':      'https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/McLaren_Automotive_logo.svg/240px-McLaren_Automotive_logo.svg.png',
    'MINI':         'https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/MINI-Logo.svg/240px-MINI-Logo.svg.png',
    'MITSUBISHI':   'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Mitsubishi_logo.svg/240px-Mitsubishi_logo.svg.png',
    'NISSAN':       'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Nissan_logo.svg/240px-Nissan_logo.svg.png',
    'PORSCHE':      'https://upload.wikimedia.org/wikipedia/de/thumb/7/70/Porsche_Logo.svg/240px-Porsche_Logo.svg.png',
    'SUBARU':       'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Subaru_logo_2019.svg/240px-Subaru_logo_2019.svg.png',
    'SUZUKI':       'https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Suzuki_logo_2.svg/240px-Suzuki_logo_2.svg.png',
    'TESLA':        'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Tesla_Motors.svg/240px-Tesla_Motors.svg.png',
    'TOYOTA':       'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Toyota_carlogo.svg/240px-Toyota_carlogo.svg.png',
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
    const logo = document.getElementById('site-logo');
    const icon  = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');

    if (theme === 'dark') {
        if (logo) logo.src = 'public/logo-white-green.svg';
        if (icon) icon.textContent = '☀️';
        if (label) label.textContent = 'Light';
    } else {
        if (logo) logo.src = 'public/logo-black-green.svg';
        if (icon) icon.textContent = '🌙';
        if (label) label.textContent = 'Dark';
    }

    localStorage.setItem('eti-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(current === 'dark' ? 'light' : 'dark');
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
