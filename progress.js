let healthData = null;
let currentMake = 'all';
let currentFilter = 'all';
let currentSearch = '';

const FILTER_PILL_IDS = {
    'all': 'filter-all',
    'edited': 'filter-edited',
    'raw_only': 'filter-raw',
    'empty': 'filter-empty'
};

async function init() {
    try {
        const response = await fetch(`health_data.json?v=${Date.now()}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        
        healthData = await response.json();
        
        // Calculate global makes count dynamically
        document.getElementById('stats-total-makes').textContent = healthData.brands.length;
        
        renderBrandList();
        selectBrand('all');
    } catch (error) {
        console.error('CRITICAL: Health data could not be loaded.', error);
        document.getElementById('folder-table-body').innerHTML = `
            <tr>
                <td colspan="7" class="p-20 text-center">
                    <p class="text-red-500 font-black uppercase text-xs tracking-widest mb-2">
                        ERROR: ${error.message}
                    </p>
                    <button onclick="location.reload()" class="mt-4 border border-brand-lime text-brand-lime px-6 py-2 text-[10px] font-bold hover:bg-brand-lime hover:text-black transition-all uppercase rounded-sm">RETRY</button>
                </td>
            </tr>
        `;
    }
}

function calculateGlobalStats() {
    let total_folders = 0;
    let raw_images = 0;
    let edited_images = 0;
    let folders_with_edited = 0;
    let folders_with_only_raw = 0;
    let folders_empty = 0;
    
    healthData.brands.forEach(b => {
        total_folders += b.total_folders;
        raw_images += b.raw_images;
        edited_images += b.edited_images;
        folders_with_edited += b.folders_with_edited;
        folders_with_only_raw += b.folders_with_only_raw;
        folders_empty += b.folders_empty;
    });
    
    return {
        total_folders,
        raw_images,
        edited_images,
        folders_with_edited,
        folders_with_only_raw,
        folders_empty
    };
}

function renderBrandList() {
    const list = document.getElementById('sidebar-brand-list');
    list.innerHTML = '';
    
    // Create "All Makes" button first
    const allStats = calculateGlobalStats();
    const allBtn = createBrandButton('all', 'ALL PORTFOLIO', allStats);
    list.appendChild(allBtn);
    
    // Create button for each brand
    healthData.brands.forEach(b => {
        const btn = createBrandButton(b.make, b.make, b);
        list.appendChild(btn);
    });
}

function createBrandButton(makeId, makeLabel, stats) {
    const pct = stats.total_folders > 0 ? ((stats.folders_with_edited / stats.total_folders) * 100).toFixed(1) : "0.0";
    const btn = document.createElement('button');
    btn.setAttribute('data-make', makeId);
    btn.onclick = () => selectBrand(makeId);
    btn.className = `brand-btn text-left p-3 rounded-sm border transition-all flex flex-col gap-1.5 w-full`;
    
    const isActive = currentMake === makeId;
    if (isActive) {
        btn.className += ' bg-brand-lime border-brand-lime text-black font-semibold shadow-[0_0_10px_rgba(196,241,1,0.2)]';
    } else {
        btn.className += ' bg-zinc-950 border-brand-border hover:border-zinc-800 text-zinc-400';
    }
    
    btn.innerHTML = `
        <div class="flex justify-between items-center w-full">
            <span class="font-extrabold text-xs uppercase ${isActive ? 'text-black' : 'text-white'}">${makeLabel}</span>
            <span class="text-[10px] font-black ${isActive ? 'text-black' : 'text-brand-lime'}">${pct}%</span>
        </div>
        <div class="w-full bg-brand-dark/40 h-1 rounded-full overflow-hidden border border-brand-border">
            <div class="${isActive ? 'bg-black' : 'bg-brand-lime'} h-full" style="width: ${pct}%"></div>
        </div>
        <div class="flex justify-between text-[8px] font-bold ${isActive ? 'text-zinc-800' : 'text-zinc-500'} uppercase tracking-wider">
            <span>Folders: ${stats.total_folders}</span>
            <span>Edited: ${stats.folders_with_edited}</span>
        </div>
    `;
    return btn;
}

function selectBrand(make) {
    currentMake = make;
    renderBrandList();
    updateStats(make);
    renderFolderTable();
}

function updateStats(make) {
    const stats = make === 'all' 
        ? calculateGlobalStats() 
        : healthData.brands.find(b => b.make === make);
        
    const pct = stats.total_folders > 0 ? ((stats.folders_with_edited / stats.total_folders) * 100).toFixed(1) : "0.0";
    
    // Overall completion Card
    document.getElementById('stats-completion-pct').textContent = `${pct}%`;
    document.getElementById('stats-completion-bar').style.width = `${pct}%`;
    document.getElementById('stats-folders-pct-label').textContent = `${stats.folders_with_edited}/${stats.total_folders}`;
    
    // Status counts Card
    document.getElementById('stats-folders-total').textContent = stats.total_folders;
    document.getElementById('stats-folders-edited').textContent = stats.folders_with_edited;
    document.getElementById('stats-folders-raw').textContent = stats.folders_with_only_raw;
    document.getElementById('stats-folders-empty').textContent = stats.folders_empty;
    
    // Image Asset Counters Card
    document.getElementById('stats-images-edited').textContent = stats.edited_images;
    document.getElementById('stats-images-raw').textContent = stats.raw_images;
}

function renderFolderTable() {
    const body = document.getElementById('folder-table-body');
    const emptyState = document.getElementById('table-empty-state');
    body.innerHTML = '';
    
    let folders = [];
    if (currentMake === 'all') {
        // Collect all folders and prepend make badge
        healthData.brands.forEach(b => {
            b.folders.forEach(f => {
                folders.push({
                    ...f,
                    make: b.make,
                    displayPath: `<span class="text-brand-lime font-bold text-[9px] bg-brand-lime/10 border border-brand-lime/20 px-2 py-0.5 rounded-sm mr-2">${b.make}</span> ${f.path}`
                });
            });
        });
    } else {
        const brand = healthData.brands.find(b => b.make === currentMake);
        folders = brand.folders.map(f => ({
            ...f,
            make: brand.make,
            displayPath: f.path
        }));
    }
    
    // Apply filters
    const searchVal = currentSearch.trim().toLowerCase();
    const filteredFolders = folders.filter(f => {
        // Search filter
        const matchesSearch = searchVal === '' || 
            f.path.toLowerCase().includes(searchVal) ||
            f.make.toLowerCase().includes(searchVal);
            
        // Status filter
        let matchesStatus = true;
        if (currentFilter !== 'all') {
            matchesStatus = f.status === currentFilter;
        }
        
        return matchesSearch && matchesStatus;
    });
    
    // Update headers info
    const totalCount = folders.length;
    const visibleCount = filteredFolders.length;
    
    document.getElementById('folders-count-visible').textContent = visibleCount;
    document.getElementById('folders-count-total').textContent = totalCount;
    
    const brandTitle = currentMake === 'all' ? 'All Makes Portfolio' : `${currentMake} Portfolio`;
    document.getElementById('selected-brand-title').textContent = brandTitle;
    
    const makeStats = currentMake === 'all' ? calculateGlobalStats() : healthData.brands.find(b => b.make === currentMake);
    const brandSubtitle = `${makeStats.total_folders} Folders | ${makeStats.folders_with_edited} Completed | ${makeStats.folders_with_only_raw} In Progress | ${makeStats.folders_empty} Empty`;
    document.getElementById('selected-brand-subtitle').textContent = brandSubtitle;
    
    if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');
    
    const rows = filteredFolders.map(f => {
        let statusBadge = '';
        let rowClass = 'hover:bg-brand-card-hover/50 transition-all';
        
        if (f.status === 'edited') {
            statusBadge = `<span class="text-[9px] font-black text-green-400 bg-green-500/10 border border-green-500/25 px-2 py-0.5 rounded-sm uppercase tracking-wide">✅ Edited</span>`;
        } else if (f.status === 'raw_only') {
            statusBadge = `<span class="text-[9px] font-black text-red-400 bg-red-500/10 border border-red-500/25 px-2 py-0.5 rounded-sm uppercase tracking-wide">⚠️ Raw Only</span>`;
        } else {
            statusBadge = `<span class="text-[9px] font-black text-yellow-500 bg-yellow-500/10 border border-yellow-500/25 px-2 py-0.5 rounded-sm uppercase tracking-wide">❌ Empty</span>`;
        }
        
        const dateStr = f.upload_date && f.upload_date !== 'N/A' 
            ? `<span class="text-zinc-300 font-semibold">${f.upload_date}</span>`
            : '<span class="text-zinc-600 italic">—</span>';
            
        let linksHtml = `<div class="flex items-center justify-center gap-3">`;
        if (f.drive_url) {
            linksHtml += `<a href="${f.drive_url}" target="_blank" class="text-blue-400 hover:text-blue-300 transition-colors" title="Open Google Drive Folder">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M7.71,3.5L1.15,15L4.58,21L11.13,9.5M9.73,15L6.3,21H19.42L22.85,15M22.28,14L15.72,2.5H8.85L15.41,14H22.28Z" /></svg>
            </a>`;
        } else {
            linksHtml += `<span class="text-zinc-800" title="No Drive Link"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M7.71,3.5L1.15,15L4.58,21L11.13,9.5M9.73,15L6.3,21H19.42L22.85,15M22.28,14L15.72,2.5H8.85L15.41,14H22.28Z" /></svg></span>`;
        }
        
        if (f.shopify_url) {
            linksHtml += `<a href="${f.shopify_url}" target="_blank" class="text-brand-lime hover:text-white transition-colors" title="Open Live Shopify Product">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12,18H6V14H12M21,14V12L20,7H4L3,12V14H4V20H14V14H18V20H20V14M20,4H4V6H20V4Z" /></svg>
            </a>`;
        } else {
             linksHtml += `<span class="text-zinc-800" title="No Shopify Link"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12,18H6V14H12M21,14V12L20,7H4L3,12V14H4V20H14V14H18V20H20V14M20,4H4V6H20V4Z" /></svg></span>`;
        }
        linksHtml += `</div>`;
            
        const photosLiveVal = f.photos_live !== undefined ? f.photos_live : 0;
        const liveColor = photosLiveVal > 0 ? 'text-brand-lime' : 'text-zinc-600';
        return `
            <tr class="${rowClass}">
                <td class="p-3 text-xs font-semibold text-zinc-300 select-all leading-relaxed">${f.displayPath}</td>
                <td class="p-3 text-center border-x border-zinc-800/30">${linksHtml}</td>
                <td class="p-3 text-center">${statusBadge}</td>
                <td class="p-3 text-center text-xs font-bold ${f.raw_count > 0 ? 'text-white' : 'text-zinc-600'}">${f.raw_count}</td>
                <td class="p-3 text-center text-xs font-bold ${f.edited_count > 0 ? 'text-brand-lime' : 'text-zinc-600'}">${f.edited_count}</td>
                <td class="p-3 text-center text-xs font-bold ${liveColor}">${photosLiveVal}</td>
                <td class="p-3 text-right text-xs font-mono">${dateStr}</td>
            </tr>
        `;
    }).join('');
    
    body.innerHTML = rows;
}

function handleFolderSearch() {
    currentSearch = document.getElementById('folder-search').value;
    renderFolderTable();
}

function setFilter(filter) {
    currentFilter = filter;
    
    // Update filter pills classes
    Object.keys(FILTER_PILL_IDS).forEach(f => {
        const el = document.getElementById(FILTER_PILL_IDS[f]);
        if (!el) return;
        if (f === filter) {
            el.className = `text-[9px] font-black uppercase tracking-wider px-3.5 py-2 border-2 border-brand-lime bg-brand-lime text-black transition-all rounded-sm`;
        } else {
            el.className = `text-[9px] font-black uppercase tracking-wider px-3.5 py-2 border border-brand-border text-zinc-400 hover:text-white hover:border-zinc-700 transition-all rounded-sm`;
        }
    });
    
    renderFolderTable();
}

function resetTableFilters() {
    document.getElementById('folder-search').value = '';
    currentSearch = '';
    setFilter('all');
}

// Start Dashboard
init();
