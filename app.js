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
        
        // Dynamic JDM & Euro Folder Health Monitor loader
        await initHealthDashboard();
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

// ==========================================
// 📂 GOOGLE DRIVE FOLDER HEALTH MONITOR SECTION
// ==========================================
let healthData = { totals: {}, brands: [] };
let activeHealthBrand = null;
let drawerStatusFilter = 'all';

async function initHealthDashboard() {
    try {
        const res = await fetch(`health_data.json?v=${Date.now()}`);
        if (!res.ok) throw new Error("Health data file not found");
        healthData = await res.json();
        renderHealthDashboard();
    } catch (err) {
        console.warn("Folder health data could not be loaded. Hiding dashboard.", err);
        const section = document.getElementById('health-dashboard-section');
        if (section) section.style.display = 'none';
    }
}

function renderHealthDashboard() {
    const totals = healthData.totals;
    if (!totals || !totals.total_folders) return;

    document.getElementById('grand-percentage').textContent = `${totals.completion_percentage}%`;
    document.getElementById('grand-progress-bar').style.width = `${totals.completion_percentage}%`;
    document.getElementById('total-folders-count').textContent = totals.total_folders.toLocaleString();
    document.getElementById('completed-folders-count').textContent = totals.folders_with_edited.toLocaleString();
    document.getElementById('raw-folders-count').textContent = totals.folders_with_only_raw.toLocaleString();
    document.getElementById('empty-folders-count').textContent = totals.folders_empty.toLocaleString();

    const grid = document.getElementById('brand-health-grid');
    if (!grid) return;
    grid.innerHTML = '';

    healthData.brands.forEach(brand => {
        const pct = brand.total_folders > 0 ? ((brand.folders_with_edited / brand.total_folders) * 100).toFixed(1) : "0.0";
        
        let colorClass = "text-zinc-400";
        let barClass = "bg-zinc-700";
        let statusBadge = "bg-zinc-800 text-zinc-400";
        let statusText = "Placeholder";
        
        const pctNum = parseFloat(pct);
        if (pctNum >= 80.0) {
            colorClass = "text-emerald-400";
            barClass = "bg-emerald-500";
            statusBadge = "bg-emerald-950/80 text-emerald-400 border border-emerald-800/40";
            statusText = "Finalizing";
        } else if (pctNum >= 30.0) {
            colorClass = "text-blue-400";
            barClass = "bg-blue-500";
            statusBadge = "bg-blue-950/80 text-blue-400 border border-blue-800/40";
            statusText = "In Progress";
        } else if (brand.folders_with_only_raw > 0) {
            colorClass = "text-amber-400";
            barClass = "bg-amber-500";
            statusBadge = "bg-amber-950/80 text-amber-400 border border-amber-800/40";
            statusText = "Awaiting Edits";
        }

        const card = document.createElement('div');
        card.className = "bg-zinc-900 border border-zinc-800 hover:border-zinc-700 p-5 rounded cursor-pointer transition-all hover:scale-[1.02] flex flex-col justify-between h-40 group relative overflow-hidden";
        card.onclick = () => openBrandHealthDetails(brand.make);
        
        card.innerHTML = `
            <div>
                <div class="flex justify-between items-start mb-2">
                    <span class="font-black text-xs uppercase tracking-wider">${brand.make}</span>
                    <span class="text-[7px] uppercase tracking-widest font-black px-1.5 py-0.5 rounded ${statusBadge}">${statusText}</span>
                </div>
                <div class="text-[9px] text-zinc-400 uppercase font-black tracking-wider mb-4">
                    ${brand.folders_with_edited} / ${brand.total_folders} Completed
                </div>
            </div>
            
            <div>
                <div class="flex justify-between text-[9px] font-black uppercase text-zinc-500 mb-1">
                    <span>Progress</span>
                    <span class="${colorClass}">${pct}%</span>
                </div>
                <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                    <div class="h-full rounded-full ${barClass} transition-all duration-500" style="width: ${pct}%"></div>
                </div>
            </div>
            
            <!-- Absolute background hover glow -->
            <div class="absolute -bottom-8 -right-8 w-20 h-20 rounded-full blur-2xl opacity-0 group-hover:opacity-10 transition-opacity duration-300 ${barClass}"></div>
        `;
        grid.appendChild(card);
    });
}

function toggleHealthDrawer(open) {
    const drawer = document.getElementById('health-drawer');
    const overlay = document.getElementById('health-overlay');
    if (!drawer || !overlay) return;
    
    if (open) {
        drawer.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        drawer.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }
}

function openBrandHealthDetails(brandName) {
    activeHealthBrand = healthData.brands.find(b => b.make === brandName);
    if (!activeHealthBrand) return;

    document.getElementById('drawer-title').textContent = `${brandName} FOLDER HEALTH`;
    document.getElementById('drawer-search').value = '';
    
    // Set status filter to all
    setDrawerStatusFilter('all', false);
    
    // Open drawer UI
    toggleHealthDrawer(true);
    
    // Load table
    renderDrawerFolders();
}

function setDrawerStatusFilter(filter, triggerRender = true) {
    drawerStatusFilter = filter;
    
    // Update button states
    ['all', 'edited', 'raw_only', 'empty'].forEach(f => {
        const btn = document.getElementById(`filter-btn-${f}`);
        if (!btn) return;
        if (f === filter) {
            btn.className = btn.className.replace('bg-zinc-900', 'bg-zinc-800').replace('border-zinc-800', 'border-zinc-700');
        } else {
            btn.className = btn.className.replace('bg-zinc-800', 'bg-zinc-900').replace('border-zinc-700', 'border-zinc-800');
        }
    });
    
    if (triggerRender) renderDrawerFolders();
}

function filterDrawerFolders() {
    renderDrawerFolders();
}

function renderDrawerFolders() {
    if (!activeHealthBrand) return;

    const tbody = document.getElementById('drawer-folders-body');
    const emptyState = document.getElementById('drawer-empty-state');
    if (!tbody || !emptyState) return;
    
    tbody.innerHTML = '';

    const search = document.getElementById('drawer-search').value.toLowerCase().trim();
    
    const filtered = activeHealthBrand.folders.filter(f => {
        const matchesSearch = search === '' || f.path.toLowerCase().includes(search);
        const matchesFilter = drawerStatusFilter === 'all' || f.status === drawerStatusFilter;
        return matchesSearch && matchesFilter;
    });

    if (filtered.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');

    filtered.forEach((f, idx) => {
        let statusBadge = '';
        let statusRowClass = '';
        if (f.status === 'edited') {
            statusBadge = '<span class="bg-emerald-950 text-emerald-400 text-[8px] font-black uppercase px-2 py-0.5 rounded border border-emerald-900/40">🟢 Done</span>';
            statusRowClass = 'hover:bg-emerald-950/10';
        } else if (f.status === 'raw_only') {
            statusBadge = '<span class="bg-amber-950 text-amber-400 text-[8px] font-black uppercase px-2 py-0.5 rounded border border-amber-980/40">🔴 Raw</span>';
            statusRowClass = 'hover:bg-amber-950/10';
        } else {
            statusBadge = '<span class="bg-zinc-800 text-zinc-400 text-[8px] font-black uppercase px-2 py-0.5 rounded">⚪ Empty</span>';
            statusRowClass = 'hover:bg-zinc-900/50';
        }

        const tr = document.createElement('tr');
        tr.className = `transition-colors duration-150 border-b border-zinc-900/40 text-[10px] ${statusRowClass}`;
        
        tr.innerHTML = `
            <td class="py-3 px-2 text-zinc-500 text-center">${idx + 1}</td>
            <td class="py-3 px-2 font-mono text-zinc-200 text-left truncate max-w-[280px]" title="${f.path}">${f.path}</td>
            <td class="py-3 px-2 text-center text-zinc-400">${f.raw_count || 0}</td>
            <td class="py-3 px-2 text-center text-zinc-400">${f.edited_count || 0}</td>
            <td class="py-3 px-2 text-right">${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

init();
