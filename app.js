let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];
let searchTimeout = null;

async function init() {
    try {
        const url = `data.json?v=${Date.now()}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        allData = await response.json();
        initializeSelects();
        switchCategory('kits');
    } catch (error) {
        console.error('CRITICAL: Data could not be loaded.', error);
        document.getElementById('catalog-body').innerHTML = `
            <tr>
                <td colspan="4" class="py-20 text-center">
                    <p class="text-red-500 font-black uppercase text-sm tracking-widest mb-2 overflow-hidden">
                        ERROR: ${error.message}
                    </p>
                    <button onclick="location.reload()" class="mt-4 border border-black px-4 py-2 text-[10px] font-bold hover:bg-black hover:text-white transition-all">RETRY</button>
                </td>
            </tr>
        `;
    }
}

function initializeSelects() {
    populateSelect('brand-filter', 'Brand', 'Category', 'MAKE');
    syncDependentFilters();
}

function syncDependentFilters() {
    const brand = document.getElementById('brand-filter').value;
    const model = document.getElementById('model-filter').value;
    
    // Filter data for the dropdowns
    const dataForModel = allData[currentCategory].filter(item => brand === '' || (item.Brand || item.Category) === brand);
    populateSelect('model-filter', 'Model', null, 'MODEL', dataForModel);
    
    const dataForPart = dataForModel.filter(item => model === '' || item.Model === model);
    populateSelect('part-filter', 'Part', 'Category', 'PART', dataForPart);
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
        el.value = opt; el.textContent = opt;
        if (opt === currentVal) el.selected = true;
        select.appendChild(el);
    });
}

function switchCategory(category) {
    currentCategory = category;
    const kitsTab = document.getElementById('tab-kits');
    const hoodsTab = document.getElementById('tab-hoods');
    
    if (category === 'kits') {
        kitsTab.classList.remove('btn-inactive');
        hoodsTab.classList.add('btn-inactive');
    } else {
        hoodsTab.classList.remove('btn-inactive');
        kitsTab.classList.add('btn-inactive');
    }
    
    resetFilters(false);
    initializeSelects();
    handleFilter();
}

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

function handleFilter() {
    // Debounce the search if called from input
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        executeFilter();
        syncDependentFilters();
    }, 150);
}

function executeFilter() {
    const search = document.getElementById('global-search').value.toLowerCase();
    const brand = document.getElementById('brand-filter').value;
    const model = document.getElementById('model-filter').value;
    const part = document.getElementById('part-filter').value;
    const minP = parseFloat(document.getElementById('min-price').value) || 0;
    const maxP = parseFloat(document.getElementById('max-price').value) || Infinity;
    
    filteredData = allData[currentCategory].filter(item => {
        const itemBrand = String(item.Brand || item.Category || '');
        const itemModel = String(item.Model || '');
        const itemPart = String(item.Part || item.Category || '');
        const itemStyle = String(item.Style || '');
        const priceNum = parseFloat(item.Price) || 0;
        
        const matchesSearch = search === '' || 
            itemBrand.toLowerCase().includes(search) || 
            itemModel.toLowerCase().includes(search) || 
            itemPart.toLowerCase().includes(search) ||
            itemStyle.toLowerCase().includes(search) ||
            String(item.SKU || '').toLowerCase().includes(search);

        return matchesSearch &&
               (brand === '' || itemBrand === brand) &&
               (model === '' || itemModel === model) &&
               (part === '' || itemPart === part) &&
               (priceNum >= minP && priceNum <= maxP);
    });
    
    renderTable();
}

function renderTable() {
    const body = document.getElementById('catalog-body');
    const emptyState = document.getElementById('empty-state');
    body.innerHTML = '';
    
    if (filteredData.length === 0) {
        emptyState.classList.remove('hidden'); return;
    }
    emptyState.classList.add('hidden');
    
    const rows = filteredData.map(item => {
        const brand = String(item.Brand || item.Category || '');
        const model = String(item.Model || '');
        const style = String(item.Style || '');
        const part = String(item.Part || item.Category || '');
        const priceStr = item.Price && parseFloat(item.Price) > 0 
            ? `$${parseFloat(item.Price).toLocaleString('en-US', {minimumFractionDigits: 2})}` 
            : '<span class="text-gray-400 italic">Enquire</span>';
        
        // Merge Style into Part Description for "Fluid" UI
        const partSpec = style && style !== model && !part.includes(style) 
            ? `${part} <span class="text-[10px] text-gray-500 block font-normal mt-1">[${style} Design]</span>`
            : part;
        
        return `
            <tr class="row-hover">
                <td data-label="Make" class="brand-col font-bold">${brand}</td>
                <td data-label="Model" class="model-col font-semibold">${model}</td>
                <td data-label="Part Specifications" class="font-medium italic text-gray-900">${partSpec}</td>
                <td data-label="Price" class="price-col text-right">${priceStr}</td>
            </tr>
        `;
    }).join('');
    
    body.innerHTML = rows;
}

init();
