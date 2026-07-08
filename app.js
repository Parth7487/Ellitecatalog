/* =============================================================
   Elite Ti — Wholesale Catalog
   app.js — Data, Filtering, Rendering, Theme
============================================================= */

let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];
let searchTimeout = null;

/* ─────────────────────────────────────────────────────────────
   BRAND LOGOS — from filippofilip95/car-logos-dataset
   Stored locally in public/logos/{brand}/logo.png
───────────────────────────────────────────────────────────── */
const LOGOS_PATH = 'public/logos/';

const BRAND_LOGOS = {
    'ALFA ROMEO':   LOGOS_PATH + 'alfa-romeo/logo.png',
    'ASTON MARTIN': LOGOS_PATH + 'aston-martin/logo.png',
    'AUDI':         LOGOS_PATH + 'audi/logo.png',
    'BENTLEY':      LOGOS_PATH + 'bentley/logo.png',
    'BENZ':         LOGOS_PATH + 'mercedes/logo.png',
    'BMW':          LOGOS_PATH + 'bmw/logo.png',
    'CHEVROLET':    LOGOS_PATH + 'chevrolet/logo.png',
    'DAIHATSU':     LOGOS_PATH + 'daihatsu/logo.png',
    'FERRARI':      LOGOS_PATH + 'ferrari/logo.png',
    'FERARRI':      LOGOS_PATH + 'ferrari/logo.png',
    'FORD':         LOGOS_PATH + 'ford/logo.png',
    'HONDA':        LOGOS_PATH + 'honda/logo.png',
    'ISUZU':        LOGOS_PATH + 'isuzu/logo.png',
    'LAMBORGHINI':  LOGOS_PATH + 'lamborghini/logo.png',
    'LEXUS':        LOGOS_PATH + 'lexus/logo.png',
    'MAZDA':        LOGOS_PATH + 'mazda/logo.png',
    'MCLAREN':      LOGOS_PATH + 'mclaren/logo.png',
    'MINI':         LOGOS_PATH + 'mini/logo.png',
    'MITSUBISHI':   LOGOS_PATH + 'mitsubishi/logo.png',
    'NISSAN':       LOGOS_PATH + 'nissan/logo.png',
    'PORSCHE':      LOGOS_PATH + 'porsche/logo.png',
    'SUBARU':       LOGOS_PATH + 'subaru/logo.png',
    'SUZUKI':       LOGOS_PATH + 'suzuki/logo.png',
    'TESLA':        LOGOS_PATH + 'tesla/logo.png',
    'TOYOTA':       LOGOS_PATH + 'toyota/logo.png',
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
    const overlay = document.getElementById('fade-overlay');

    if (!overlay) { applyTheme(next); return; }

    overlay.classList.add('active');

    setTimeout(() => {
        applyTheme(next);
    }, 220); // wait for fade overlay to be fully visible (matches the 0.22s CSS transition)

    setTimeout(() => {
        overlay.classList.remove('active');
    }, 350);
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
        initCustomBrandSelectEvents();
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

    // If it's the brand-filter, also update the custom brand select UI
    if (id === 'brand-filter') {
        buildCustomBrandDropdown(sorted, currentVal);
    }
}

/* ─────────────────────────────────────────────────────────────
   CUSTOM BRAND DROPDOWN LOGIC
───────────────────────────────────────────────────────────── */
function buildCustomBrandDropdown(sortedBrands, currentVal) {
    const dropdown = document.getElementById('brand-custom-dropdown');
    const triggerLabel = document.getElementById('brand-trigger-label');
    const triggerLogo = document.getElementById('brand-trigger-logo');
    const select = document.getElementById('brand-filter');

    if (!dropdown) return;

    dropdown.innerHTML = '';

    // 1. Add "Make" reset item
    const resetItem = document.createElement('div');
    resetItem.className = 'brand-dropdown-item reset-item';
    resetItem.textContent = 'All Makes';
    if (!currentVal) {
        resetItem.classList.add('selected');
        triggerLabel.textContent = 'Make';
        triggerLogo.src = '';
        triggerLogo.classList.remove('visible');
    }
    resetItem.onclick = () => {
        select.value = '';
        select.dispatchEvent(new Event('change'));
        closeCustomBrandDropdown();
    };
    dropdown.appendChild(resetItem);

    // 2. Add each brand item with logo
    sortedBrands.forEach(brand => {
        const item = document.createElement('div');
        item.className = 'brand-dropdown-item';
        if (brand === currentVal) {
            item.classList.add('selected');
            triggerLabel.textContent = brand;
            const logoUrl = getBrandLogoUrl(brand);
            if (logoUrl) {
                triggerLogo.src = logoUrl;
                triggerLogo.classList.add('visible');
            } else {
                triggerLogo.src = '';
                triggerLogo.classList.remove('visible');
            }
        }

        // Add logo image if it exists in BRAND_LOGOS
        const logoUrl = getBrandLogoUrl(brand);
        if (logoUrl) {
            const img = document.createElement('img');
            img.className = 'brand-item-logo';
            img.src = logoUrl;
            img.alt = brand;
            img.loading = 'lazy';
            img.onerror = () => {
                img.style.display = 'none';
            };
            item.appendChild(img);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'brand-item-logo-placeholder';
            item.appendChild(placeholder);
        }

        const nameSpan = document.createElement('span');
        nameSpan.textContent = brand;
        item.appendChild(nameSpan);

        item.onclick = () => {
            select.value = brand;
            select.dispatchEvent(new Event('change'));
            closeCustomBrandDropdown();
        };

        dropdown.appendChild(item);
    });
}

function initCustomBrandSelectEvents() {
    const customSelect = document.getElementById('brand-custom-select');
    const trigger = document.getElementById('brand-custom-trigger');

    if (!customSelect || !trigger) return;

    trigger.onclick = (e) => {
        e.stopPropagation();
        const isOpen = customSelect.classList.contains('open');
        if (isOpen) {
            closeCustomBrandDropdown();
        } else {
            customSelect.classList.add('open');
            customSelect.setAttribute('aria-expanded', 'true');
        }
    };

    // Close on clicking outside
    document.addEventListener('click', () => {
        closeCustomBrandDropdown();
    });

    // Close on ESC key or handle keyboard interactions
    customSelect.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeCustomBrandDropdown();
        }
    });
}

function closeCustomBrandDropdown() {
    const customSelect = document.getElementById('brand-custom-select');
    if (customSelect) {
        customSelect.classList.remove('open');
        customSelect.setAttribute('aria-expanded', 'false');
    }
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
