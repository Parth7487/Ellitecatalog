let healthData = null;
let currentMake = 'all';
let currentMismatchFilter = 'all';
let currentModelFilter = 'all';
let currentSearch = '';

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

function calculateMismatchStats(folders) {
    let e_but_0_live = 0;
    let raw_ne_edited = 0;
    let edited_ne_live = 0;
    let total_mismatches = 0;
    
    folders.forEach(f => {
        const photosLiveVal = f.photos_live !== undefined ? f.photos_live : 0;
        const has_e_0 = f.status === 'edited' && f.edited_count > 0 && photosLiveVal === 0;
        const has_r_e = f.edited_count > f.raw_count;
        const has_e_l = f.status === 'edited' && photosLiveVal > 0 && f.edited_count !== photosLiveVal;
        
        if (has_e_0) e_but_0_live++;
        if (has_r_e) raw_ne_edited++;
        if (has_e_l) edited_ne_live++;
        if (has_e_0 || has_r_e || has_e_l) total_mismatches++;
    });
    
    return {
        e_but_0_live,
        raw_ne_edited,
        edited_ne_live,
        total_mismatches
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
    currentMismatchFilter = 'all';
    currentModelFilter = 'all';
    document.getElementById('filter-mismatch').value = 'all';
    document.getElementById('folder-search').value = '';
    currentSearch = '';
    
    renderBrandList();
    updateStats(make);
    rebuildModelDropdown();
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
    
    // Gather all folders for mismatch calculation
    let folders = [];
    if (make === 'all') {
        healthData.brands.forEach(b => {
            folders = folders.concat(b.folders);
        });
    } else {
        const brand = healthData.brands.find(b => b.make === make);
        folders = brand.folders;
    }
    
    // Calculate mismatch stats
    const mStats = calculateMismatchStats(folders);
    document.getElementById('val-total-mismatches').textContent = mStats.total_mismatches;
    document.getElementById('val-edited-but-0-live').textContent = mStats.e_but_0_live;
    document.getElementById('val-raw-ne-edited').textContent = mStats.raw_ne_edited;
    document.getElementById('val-edited-ne-live').textContent = mStats.edited_ne_live;
}

function rebuildModelDropdown() {
    let folders = [];
    if (currentMake === 'all') {
        healthData.brands.forEach(b => {
            folders = folders.concat(b.folders);
        });
    } else {
        const brand = healthData.brands.find(b => b.make === currentMake);
        folders = brand.folders;
    }
    
    // Extract unique models
    const models = new Set();
    folders.forEach(f => {
        const model = f.path.split('/')[0];
        if (model) models.add(model);
    });
    
    const sortedModels = Array.from(models).sort();
    
    const modelSelect = document.getElementById('filter-model');
    modelSelect.innerHTML = '<option value="all">All Models</option>';
    
    sortedModels.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        modelSelect.appendChild(opt);
    });
    
    currentModelFilter = 'all';
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
            
        // Mismatch / Status filter
        let matchesMismatch = true;
        const photosLiveVal = f.photos_live !== undefined ? f.photos_live : 0;
        
        if (currentMismatchFilter === 'all_mismatches') {
            matchesMismatch = (f.edited_count > f.raw_count) || (f.status === 'edited' && f.edited_count !== photosLiveVal);
        } else if (currentMismatchFilter === 'edited_but_0_live') {
            matchesMismatch = f.status === 'edited' && f.edited_count > 0 && photosLiveVal === 0;
        } else if (currentMismatchFilter === 'raw_ne_edited') {
            matchesMismatch = f.edited_count > f.raw_count;
        } else if (currentMismatchFilter === 'edited_ne_live') {
            matchesMismatch = f.status === 'edited' && photosLiveVal > 0 && f.edited_count !== photosLiveVal;
        } else if (currentMismatchFilter === 'status_edited') {
            matchesMismatch = f.status === 'edited';
        } else if (currentMismatchFilter === 'status_raw_only') {
            matchesMismatch = f.status === 'raw_only';
        } else if (currentMismatchFilter === 'status_empty') {
            matchesMismatch = f.status === 'empty';
        }
        
        // Model filter
        let matchesModel = true;
        if (currentModelFilter !== 'all') {
            const folderModel = f.path.split('/')[0];
            matchesModel = folderModel === currentModelFilter;
        }
        
        return matchesSearch && matchesMismatch && matchesModel;
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
    
    // Update active visual states for the mismatch cards
    updateActiveCardStyles();
    
    if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');
    
    const rows = filteredFolders.map(f => {
        let rowClass = 'hover:bg-brand-card-hover/50 transition-all';
        
        // Setup mismatch/status badges (can display multiple badges if there are multiple mismatches)
        let badgesHtml = '<div class="flex flex-wrap gap-1 justify-center">';
        
        const photosLiveVal = f.photos_live !== undefined ? f.photos_live : 0;
        const has_e_0 = f.status === 'edited' && f.edited_count > 0 && photosLiveVal === 0;
        const has_r_e = f.edited_count > f.raw_count;
        const has_e_l = f.status === 'edited' && photosLiveVal > 0 && f.edited_count !== photosLiveVal;
        
        if (f.status === 'edited') {
            badgesHtml += `<span class="text-[8px] font-black text-green-400 bg-green-500/10 border border-green-500/25 px-1.5 py-0.5 rounded-sm uppercase tracking-wider">Edited</span>`;
        } else if (f.status === 'raw_only') {
            badgesHtml += `<span class="text-[8px] font-black text-red-400 bg-red-500/10 border border-red-500/25 px-1.5 py-0.5 rounded-sm uppercase tracking-wider">Raw Only</span>`;
        } else {
            badgesHtml += `<span class="text-[8px] font-black text-yellow-500 bg-yellow-500/10 border border-yellow-500/25 px-1.5 py-0.5 rounded-sm uppercase tracking-wider">Empty</span>`;
        }
        
        if (has_e_0) {
            badgesHtml += `<span class="text-[8px] font-black text-red-400 bg-red-500/10 border border-red-500/30 px-1.5 py-0.5 rounded-sm uppercase tracking-wider shadow-[0_0_8px_rgba(239,68,68,0.1)]">0 Live</span>`;
        }
        if (has_r_e) {
            badgesHtml += `<span class="text-[8px] font-black text-yellow-500 bg-yellow-500/10 border border-yellow-500/30 px-1.5 py-0.5 rounded-sm uppercase tracking-wider shadow-[0_0_8px_rgba(245,158,11,0.1)]">Raw ≠ Edited</span>`;
        }
        if (has_e_l) {
            badgesHtml += `<span class="text-[8px] font-black text-purple-400 bg-purple-500/10 border border-purple-500/30 px-1.5 py-0.5 rounded-sm uppercase tracking-wider shadow-[0_0_8px_rgba(139,92,246,0.1)]">Edited ≠ Live</span>`;
        }
        badgesHtml += '</div>';
        
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
            
        const liveColor = photosLiveVal > 0 ? 'text-brand-lime' : 'text-zinc-600';
        return `
            <tr class="${rowClass}">
                <td class="p-3 text-xs font-semibold text-zinc-300 select-all leading-relaxed">${f.displayPath}</td>
                <td class="p-3 text-center border-x border-zinc-800/30">${linksHtml}</td>
                <td class="p-3 text-center">${badgesHtml}</td>
                <td class="p-3 text-center text-xs font-bold ${f.raw_count > 0 ? 'text-white' : 'text-zinc-600'}">${f.raw_count}</td>
                <td class="p-3 text-center text-xs font-bold ${f.edited_count > 0 ? 'text-brand-lime' : 'text-zinc-600'}">${f.edited_count}</td>
                <td class="p-3 text-center text-xs font-bold ${liveColor}">${photosLiveVal}</td>
                <td class="p-3 text-right text-xs font-mono">${dateStr}</td>
            </tr>
        `;
    }).join('');
    
    body.innerHTML = rows;
}

function updateActiveCardStyles() {
    const cardIds = {
        'all_mismatches': 'card-total-mismatches',
        'edited_but_0_live': 'card-edited-but-0-live',
        'raw_ne_edited': 'card-raw-ne-edited',
        'edited_ne_live': 'card-edited-ne-live'
    };
    
    Object.keys(cardIds).forEach(filter => {
        const el = document.getElementById(cardIds[filter]);
        if (!el) return;
        
        if (currentMismatchFilter === filter) {
            el.classList.remove('border-brand-border', 'bg-zinc-950/40');
            el.classList.add('border-brand-lime/60', 'bg-brand-lime/[0.03]', 'glow-lime-sm');
        } else {
            el.classList.remove('border-brand-lime/60', 'bg-brand-lime/[0.03]', 'glow-lime-sm');
            el.classList.add('border-brand-border', 'bg-zinc-950/40');
        }
    });
}

function handleMismatchFilterChange() {
    currentMismatchFilter = document.getElementById('filter-mismatch').value;
    renderFolderTable();
}

function handleModelFilterChange() {
    currentModelFilter = document.getElementById('filter-model').value;
    renderFolderTable();
}

function applyQuickFilter(filter) {
    if (currentMismatchFilter === filter) {
        currentMismatchFilter = 'all';
    } else {
        currentMismatchFilter = filter;
    }
    document.getElementById('filter-mismatch').value = currentMismatchFilter;
    renderFolderTable();
}

function handleFolderSearch() {
    currentSearch = document.getElementById('folder-search').value;
    renderFolderTable();
}

function resetTableFilters() {
    document.getElementById('folder-search').value = '';
    currentSearch = '';
    currentMismatchFilter = 'all';
    currentModelFilter = 'all';
    document.getElementById('filter-mismatch').value = 'all';
    document.getElementById('filter-model').value = 'all';
    renderFolderTable();
}

// Start Dashboard
init();
