let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];

async function init() {
    try {
        // Add cache buster to ensure Vercel serves the latest data
        const response = await fetch('data.json?v=' + Date.now());
        if (!response.ok) throw new Error('Network response was not ok');
        allData = await response.json();
        
        console.log('Data loaded successfully:', allData.metadata.counts);
        
        initializeAllFilters();
        switchCategory('kits');
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('catalog-body').innerHTML = `
            <tr>
                <td colspan="6" class="py-20 text-center text-red-500 font-bold uppercase tracking-widest">
                    Data Load Error: Please refresh the page or check data.json
                </td>
            </tr>
        `;
    }
}

function initializeAllFilters() {
    populateSelect('brand-filter', 'Brand', 'Category', 'MAKE');
    populateSelect('model-filter', 'Model', null, 'MODEL');
    populateSelect('style-filter', 'Style', null, 'STYLE');
    populateSelect('part-filter', 'Part', 'Category', 'PART');
}

function populateSelect(id, optKey, altKey, label) {
    const select = document.getElementById(id);
    const options = new Set();
    
    allData[currentCategory].forEach(item => {
        const val = item[optKey] || (altKey ? item[altKey] : null);
        if (val && String(val).trim() !== '') options.add(val);
    });
    
    const sorted = Array.from(options).sort();
    select.innerHTML = `<option value="">${label}</option>`;
    sorted.forEach(opt => {
        const el = document.createElement('option');
        el.value = opt;
        el.textContent = opt;
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
    initializeAllFilters();
    handleFilter();
}

function resetFilters(trigger = true) {
    document.getElementById('global-search').value = '';
    document.getElementById('brand-filter').value = '';
    document.getElementById('model-filter').value = '';
    document.getElementById('style-filter').value = '';
    document.getElementById('part-filter').value = '';
    document.getElementById('sku-filter').value = '';
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    if (trigger) handleFilter();
}

function handleFilter() {
    const search = document.getElementById('global-search').value.toLowerCase();
    const brand = document.getElementById('brand-filter').value;
    const model = document.getElementById('model-filter').value;
    const style = document.getElementById('style-filter').value;
    const part = document.getElementById('part-filter').value;
    const sku = document.getElementById('sku-filter').value.toLowerCase();
    const minP = parseFloat(document.getElementById('min-price').value) || 0;
    const maxP = parseFloat(document.getElementById('max-price').value) || Infinity;
    
    const rawData = allData[currentCategory];
    
    filteredData = rawData.filter(item => {
        const itemBrand = String(item.Brand || item.Category || '');
        const itemModel = String(item.Model || '');
        const itemStyle = String(item.Style || '');
        const itemPart = String(item.Part || item.Category || '');
        const itemSku = String(item.SKU || '').toLowerCase();
        const itemPrice = parseFloat(item.Price) || 0;
        
        const matchesSearch = search === '' || Object.values(item).join(' ').toLowerCase().includes(search);
        const matchesBrand = brand === '' || itemBrand === brand;
        const matchesModel = model === '' || itemModel === model;
        const matchesStyle = style === '' || itemStyle === style;
        const matchesPart = part === '' || itemPart === part;
        const matchesSku = sku === '' || itemSku.includes(sku);
        const matchesPrice = itemPrice >= minP && itemPrice <= maxP;
        
        return matchesSearch && matchesBrand && matchesModel && matchesStyle && matchesPart && matchesSku && matchesPrice;
    });
    
    renderTable();
}

function renderTable() {
    const body = document.getElementById('catalog-body');
    const emptyState = document.getElementById('empty-state');
    
    body.innerHTML = '';
    
    if (filteredData.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');
    
    let lastBrand = null;
    let lastModel = null;
    
    const rows = filteredData.map(item => {
        const brand = String(item.Brand || item.Category || '');
        const model = String(item.Model || '');
        const style = String(item.Style || '');
        const part = String(item.Part || item.Category || '');
        const sku = String(item.SKU || '');
        const price = item.Price ? `$${parseFloat(item.Price).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '';
        
        // Match the clustered display from screenshot
        const brandDisp = brand === lastBrand ? '' : brand;
        const modelDisp = (brand === lastBrand && model === lastModel) ? '' : model;
        
        lastBrand = brand;
        lastModel = model;
        
        return `
            <tr class="row-hover">
                <td class="brand-col">${brandDisp}</td>
                <td class="model-col">${modelDisp}</td>
                <td class="style-col">${style}</td>
                <td class="part-col">${part}</td>
                <td class="sku-col">${sku}</td>
                <td class="price-col">${price}</td>
            </tr>
        `;
    }).join('');
    
    body.innerHTML = rows;
}

init();
