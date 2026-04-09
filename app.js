let allData = { kits: [], hoods: [] };
let currentCategory = 'kits';
let filteredData = [];

// Initialize app
async function init() {
    try {
        const response = await fetch('data.json');
        allData = await response.json();
        
        // Populate brand filter
        updateBrandFilter();
        
        // Initial render
        switchCategory('kits');
        
        console.log('Data loaded:', allData);
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('results-grid').innerHTML = `
            <div class="col-span-full py-20 text-center">
                <p class="text-red-400 font-medium">Failed to load catalog data. Please ensure data.json exists.</p>
            </div>
        `;
    }
}

function updateBrandFilter() {
    const brandFilter = document.getElementById('brand-filter');
    const brands = new Set();
    
    const data = allData[currentCategory];
    data.forEach(item => {
        const brand = item.Brand || item.Category || 'Other';
        brands.add(brand);
    });
    
    // Clear and add "All Brands"
    brandFilter.innerHTML = '<option value="">All Brands / Categories</option>';
    
    // Sort and add brands
    Array.from(brands).sort().forEach(brand => {
        const option = document.createElement('option');
        option.value = brand;
        option.textContent = brand;
        brandFilter.appendChild(option);
    });
}

function switchCategory(category) {
    currentCategory = category;
    
    // Update UI tabs
    const kitsTab = document.getElementById('tab-kits');
    const hoodsTab = document.getElementById('tab-hoods');
    
    if (category === 'kits') {
        kitsTab.classList.add('bg-accent-500', 'text-white', 'shadow-lg');
        kitsTab.classList.remove('text-slate-400');
        hoodsTab.classList.remove('bg-accent-500', 'text-white', 'shadow-lg');
        hoodsTab.classList.add('text-slate-400');
    } else {
        hoodsTab.classList.add('bg-accent-500', 'text-white', 'shadow-lg');
        hoodsTab.classList.remove('text-slate-400');
        kitsTab.classList.remove('bg-accent-500', 'text-white', 'shadow-lg');
        kitsTab.classList.add('text-slate-400');
    }
    
    // Reset search and filter
    document.getElementById('search-input').value = '';
    document.getElementById('brand-filter').value = '';
    
    updateBrandFilter();
    handleFilter();
}

function handleFilter() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const brandTerm = document.getElementById('brand-filter').value;
    const sortVal = document.getElementById('sort-filter').value;
    
    const data = allData[currentCategory];
    
    filteredData = data.filter(item => {
        const searchStr = Object.values(item).join(' ').toLowerCase();
        const matchesSearch = searchStr.includes(searchTerm);
        
        const itemBrand = item.Brand || item.Category || 'Other';
        const matchesBrand = !brandTerm || itemBrand === brandTerm;
        
        return matchesSearch && matchesBrand;
    });
    
    // Sorting
    if (sortVal === 'price-asc') {
        filteredData.sort((a, b) => (parseFloat(a.Price) || 0) - (parseFloat(b.Price) || 0));
    } else if (sortVal === 'price-desc') {
        filteredData.sort((a, b) => (parseFloat(b.Price) || 0) - (parseFloat(a.Price) || 0));
    } else if (sortVal === 'model-asc') {
        filteredData.sort((a, b) => String(a.Model).localeCompare(String(b.Model)));
    }
    
    // Update Tag UI
    const brandTag = document.getElementById('active-brand-tag');
    if (brandTerm) {
        brandTag.classList.remove('hidden');
        document.getElementById('current-brand-name').textContent = brandTerm;
    } else {
        brandTag.classList.add('hidden');
    }
    
    renderResults();
}

function renderResults() {
    const grid = document.getElementById('results-grid');
    const countDisplay = document.getElementById('count-display');
    const emptyState = document.getElementById('empty-state');
    
    countDisplay.textContent = filteredData.length;
    
    if (filteredData.length === 0) {
        grid.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    grid.innerHTML = filteredData.map(item => {
        const price = item.Price ? `$${parseFloat(item.Price).toLocaleString()}` : 'Contact Us';
        const brand = item.Brand || item.Category || '-';
        const model = item.Model || '-';
        const style = item.Style || '-';
        const part = item.Part || item.Category || 'Component';
        const sku = item.SKU || 'N/A';
        
        return `
            <div class="glass p-5 rounded-3xl border border-white/5 card-hover flex flex-col gap-4">
                <div class="flex justify-between items-start">
                    <span class="bg-accent-500/10 text-accent-400 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-accent-500/20">
                        ${brand}
                    </span>
                    <span class="text-xs font-mono text-slate-500">#${sku}</span>
                </div>
                
                <div class="space-y-1">
                    <h3 class="text-lg font-bold text-white line-clamp-1">${model}</h3>
                    <p class="text-sm text-slate-400 font-medium">${style}</p>
                </div>
                
                <div class="py-3 border-y border-white/5">
                    <p class="text-[13px] text-slate-300 font-medium leading-relaxed italic">
                        ${part}
                    </p>
                </div>
                
                <div class="mt-auto flex items-center justify-between">
                    <div>
                        <p class="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Wholesale Price</p>
                        <p class="text-xl font-black text-white">${price}</p>
                    </div>
                    <button class="bg-white/5 hover:bg-accent-500 group transition-all p-2.5 rounded-xl border border-white/10 hover:border-accent-400">
                        <svg class="w-5 h-5 text-slate-300 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Start
init();
