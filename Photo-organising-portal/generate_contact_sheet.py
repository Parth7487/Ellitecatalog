import os
import json
import urllib.request
import ssl
import re
import time

STORE = 'myeliteti.myshopify.com'

def load_token():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('SHOPIFY_TOKEN='):
                    return line.strip().split('=', 1)[1].strip('"\'')
    return os.environ.get('SHOPIFY_TOKEN', '')

TOKEN = load_token()
HEALTH_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'health_data.json')
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

brand_mappings = [
    {
        "make": "BMW",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/BMW",
        "collections": [
            "gid://shopify/Collection/472264245529",
            "gid://shopify/Collection/493542867225",
            "gid://shopify/Collection/494958018841",
            "gid://shopify/Collection/512300155161"
        ]
    },
    {
        "make": "Honda",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Honda",
        "collections": [
            "gid://shopify/Collection/491729191193",
            "gid://shopify/Collection/491759272217",
            "gid://shopify/Collection/494449262873",
            "gid://shopify/Collection/513247969561"
        ]
    },
    {
        "make": "Mazda",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Mazda",
        "collections": [
            "gid://shopify/Collection/467566100761",
            "gid://shopify/Collection/476770599193",
            "gid://shopify/Collection/491759632665",
            "gid://shopify/Collection/513398243609",
            "gid://shopify/Collection/512334561561"
        ]
    },
    {
        "make": "Mercedes-Benz",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Mercedes-Benz",
        "collections": [
            "gid://shopify/Collection/513104412953",
            "gid://shopify/Collection/513104445721"
        ]
    },
    {
        "make": "Mitsubishi",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Mitsubishi",
        "collections": [
            "gid://shopify/Collection/468666482969",
            "gid://shopify/Collection/491976720665",
            "gid://shopify/Collection/493713457433",
            "gid://shopify/Collection/496729325849",
            "gid://shopify/Collection/512298778905",
            "gid://shopify/Collection/512350683417"
        ]
    },
    {
        "make": "Porsche",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Porsche",
        "collections": [
            "gid://shopify/Collection/467589366041",
            "gid://shopify/Collection/505526288665",
            "gid://shopify/Collection/505526485273",
            "gid://shopify/Collection/505527304473",
            "gid://shopify/Collection/505527435545",
            "gid://shopify/Collection/505527566617",
            "gid://shopify/Collection/505527795993",
            "gid://shopify/Collection/505527861529",
            "gid://shopify/Collection/512367886617"
        ]
    },
    {
        "make": "Toyota",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Toyota",
        "collections": [
            "gid://shopify/Collection/467479986457",
            "gid://shopify/Collection/467589693721",
            "gid://shopify/Collection/486336659737",
            "gid://shopify/Collection/487731429657",
            "gid://shopify/Collection/493826703641",
            "gid://shopify/Collection/503339417881",
            "gid://shopify/Collection/503339450649",
            "gid://shopify/Collection/513418395929"
        ]
    },
    {
        "make": "Nissan",
        "base_dir": "/Users/parth/Downloads/Shopifydevstudio/Nissan",
        "collections": [
            "gid://shopify/Collection/467557581081",
            "gid://shopify/Collection/467589792025",
            "gid://shopify/Collection/467589890329",
            "gid://shopify/Collection/467591233817",
            "gid://shopify/Collection/467614761241",
            "gid://shopify/Collection/493300711705",
            "gid://shopify/Collection/494909128985",
            "gid://shopify/Collection/495877914905",
            "gid://shopify/Collection/498956435737",
            "gid://shopify/Collection/513440612633"
        ]
    }
]

def graphql_query(query, variables=None):
    url = f"https://{STORE}/admin/api/2024-01/graphql.json"
    headers = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
    data = {"query": query}
    if variables: data["variables"] = variables
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"GraphQL request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None

def fetch_product_by_handle(handle):
    query = """
    query getProductByHandle($handle: String!) {
      productByHandle(handle: $handle) {
        id
        title
        handle
        status
        media(first: 100) {
          nodes {
            id
            mediaContentType
            ... on MediaImage {
              image {
                url
              }
            }
          }
        }
      }
    }
    """
    res = graphql_query(query, {"handle": handle})
    if res and 'data' in res and res['data'].get('productByHandle'):
        return res['data']['productByHandle']
    return None

def fetch_products(collection_id):
    products = []
    has_next = True
    cursor = None
    query = """
    query getProducts($cursor: String, $colId: ID!) {
      collection(id: $colId) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          edges {
            node {
              id
              title
              handle
              status
              media(first: 100) {
                nodes {
                  id
                  mediaContentType
                  ... on MediaImage {
                    image {
                      url
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    while has_next:
        variables = {"cursor": cursor, "colId": collection_id} if cursor else {"colId": collection_id}
        res = graphql_query(query, variables)
        if not res or 'errors' in res or 'data' not in res or not res['data']['collection']: 
            break
        conn = res['data']['collection']['products']
        for edge in conn['edges']:
            products.append(edge['node'])
        has_next = conn['pageInfo']['hasNextPage']
        cursor = conn['pageInfo']['endCursor']
        time.sleep(0.1)
    return products

def get_edited_images(prod_path):
    edit_kw = ['edited', 'edit', 'final', 'cleaned', 'ediited', 'editted', 'photoroom', 'editing', 'edits', 'completed']
    img_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp', '.gif', '.heic', '.heif'}
    
    if not os.path.exists(prod_path):
        return []
    try:
        parent_name = os.path.basename(prod_path).lower()
        for sub in os.listdir(prod_path):
            sub_path = os.path.join(prod_path, sub)
            if os.path.isdir(sub_path):
                if any(kw in sub.lower() for kw in edit_kw) or sub.lower() == parent_name:
                    files = []
                    for f in sorted(os.listdir(sub_path)):
                        if not f.startswith('.') and os.path.splitext(f.lower())[1] in img_extensions:
                            files.append(os.path.join(sub_path, f))
                    return files
    except Exception as e:
        print(f"Error reading path {prod_path}: {e}")
    return []

def get_raw_images(prod_path):
    img_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp', '.gif', '.heic', '.heif'}
    if not os.path.exists(prod_path):
        return []
    try:
        files = []
        for f in sorted(os.listdir(prod_path)):
            full_f_path = os.path.join(prod_path, f)
            if os.path.isfile(full_f_path) and not f.startswith('.') and os.path.splitext(f.lower())[1] in img_extensions:
                files.append(full_f_path)
        return files
    except Exception as e:
        print(f"Error reading raw path {prod_path}: {e}")
    return []

def run():
    print("⏳ Loading local catalog data...")
    with open(HEALTH_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    status_file = os.path.join(os.path.dirname(__file__), 'review_status.json')
    review_statuses = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                review_statuses = json.load(f)
        except Exception:
            pass
        
    product_records = []
    
    for mapping in brand_mappings:
        make = mapping['make']
        base_dir = mapping['base_dir']
        collections = mapping['collections']
        
        if not collections:
            print(f"⚠️ Skipping {make} (No collections configured).")
            continue
            
        print(f"⏳ Fetching live {make} products from Shopify...")
        shopify_products = []
        for col in collections:
            shopify_products.extend(fetch_products(col))
        print(f"✅ Fetched {len(shopify_products)} live products for {make}.")
        shopify_map = {}
        for p in shopify_products:
            shopify_map[p['handle']] = p
            if 'id' in p:
                num_id = p['id'].split('/')[-1]
                shopify_map[num_id] = p
        
        brand_data = next((b for b in data['brands'] if b['make'].upper() == make.upper()), None)
        if not brand_data:
            print(f"⚠️ Brand {make} not found in health_data.json. Skipping.")
            continue
            
        for folder in brand_data['folders']:
            path = folder['path']
            status = folder['status']
            raw_count = folder['raw_count']
            edited_count = folder['edited_count']
            shopify_url = folder.get('shopify_url', '')
            drive_url = folder.get('drive_url', '')
            
            full_path = os.path.join(base_dir, path)
            drive_images = get_edited_images(full_path)
            raw_images = get_raw_images(full_path)
            
            edited_folder_path = os.path.dirname(drive_images[0]) if drive_images else ""
            raw_folder_path = full_path
            
            shopify_title = ""
            product_id = ""
            shortProdId = ""
            live_images = []
            shopify_status = ""
            if shopify_url:
                clean_url = shopify_url.split('?')[0].split('#')[0].rstrip('/')
                handle = clean_url.split('/')[-1]
                prod = shopify_map.get(handle)
                if not prod:
                    print(f"🔍 Product {handle} not found in brand collection. Fetching individually from Shopify...")
                    prod = fetch_product_by_handle(handle)
                    if prod:
                        shopify_map[handle] = prod
                        if 'id' in prod:
                            num_id = prod['id'].split('/')[-1]
                            shopify_map[num_id] = prod
                if prod:
                    product_id = prod['id']
                    shortProdId = product_id.split('/')[-1]
                    shopify_title = prod.get('title', '')
                    shopify_status = prod.get('status', '')
                    for m in prod['media']['nodes']:
                        if m['mediaContentType'] == 'IMAGE' and m.get('image'):
                            img_url = m['image']['url']
                            live_images.append({
                                "id": m['id'],
                                "url": img_url
                            })
            
            if not shortProdId:
                import hashlib
                shortProdId = "local_" + hashlib.md5(full_path.encode('utf-8')).hexdigest()[:12]
            
            actual_live_count = len(live_images)
            has_e_0 = status == 'edited' and len(drive_images) > 0 and actual_live_count == 0
            has_r_e = len(drive_images) > len(raw_images)
            has_e_l = status == 'edited' and actual_live_count > 0 and len(drive_images) != actual_live_count
            
            is_mismatch = has_e_0 or has_r_e or has_e_l
                                   
            product_records.append({
                "shopify_title": shopify_title,
                "make": make,
                "name": os.path.basename(path),
                "path": path,
                "status": status,
                "is_mismatch": is_mismatch,
                "mismatch_reasons": {
                    "Edited but 0 Live": has_e_0,
                    "Raw ≠ Edited": has_r_e,
                    "Edited ≠ Live": has_e_l
                },
                "product_id": product_id,
                "short_id": shortProdId,
                "drive_count": len(drive_images),
                "raw_count": raw_count,
                "raw_folder_path": raw_folder_path,
                "edited_folder_path": edited_folder_path,
                "review_status": review_statuses.get(shortProdId, 'Unreviewed'),
                "shopify_count": len(live_images),
                "drive_images": drive_images,
                "raw_images": raw_images,
                "live_images": live_images,
                "shopify_url": shopify_url,
                "drive_url": drive_url,
                "shopify_status": shopify_status
            })

    print("⏳ Generating HTML Contact Sheet...")
    
    # Calculate global stats
    total_mismatches = sum(1 for p in product_records if p['is_mismatch'])
    total_products = len(product_records)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elite Ti - Visual Image Verifier</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --tile-size: 128px;
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: #070708;
            color: #E4E4E7;
            -webkit-font-smoothing: antialiased;
        }
        .mismatch-card {
            background-color: #171011;
            border: 2px solid #EF4444;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
        }
        .match-card {
            background-color: #141416;
            border: 1px solid #27272A;
        }
        img {
            object-fit: cover;
            border-radius: 4px;
            background-color: #222;
        }
        .tile-img {
            width: var(--tile-size) !important;
            height: var(--tile-size) !important;
            object-fit: cover;
        }
        .image-card {
            width: var(--tile-size) !important;
            height: var(--tile-size) !important;
        }
        .image-card img {
            width: 100% !important;
            height: 100% !important;
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0B0B0C;
        }
        ::-webkit-scrollbar-thumb {
            background: #27272A;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #C4F101;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="border-b border-zinc-800 bg-[#0B0B0C]/80 backdrop-blur sticky top-0 z-50 px-4 py-4 md:px-8">
        <div class="max-w-[1850px] mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-4">
                <a href="progress.html" class="flex items-center gap-2 border border-zinc-800 hover:border-[#C4F101] text-xs font-black tracking-widest px-4 py-2 bg-[#141416] hover:bg-black text-gray-300 hover:text-[#C4F101] transition-all uppercase rounded-sm">
                    <span>← SYNC CONTROL CENTER</span>
                </a>
                <div class="h-6 w-px bg-zinc-800 hidden sm:block"></div>
                <div class="flex items-center gap-2">
                    <span id="server-dot" class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                    <span id="server-text" class="text-xs font-bold uppercase tracking-wider text-red-500">Shopify Helper Offline</span>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <!-- Grid Tile Size Slider -->
                <div class="flex items-center gap-2 bg-[#141416] border border-zinc-800 px-3 py-1.5 rounded-sm">
                    <span class="text-[9px] font-black text-zinc-400 uppercase tracking-wider">Tile Size:</span>
                    <input type="range" id="size-slider" min="64" max="256" step="16" value="128" oninput="updateTileSize(this.value)" class="w-20 sm:w-28 accent-[#C4F101] cursor-pointer">
                    <span id="size-value" class="text-[9px] font-black text-[#C4F101] w-10 text-right">128px</span>
                </div>

                <div class="flex gap-2">
                    <select id="status-filter" class="bg-zinc-900 text-zinc-300 border border-zinc-700 text-[9px] uppercase tracking-wider font-extrabold px-3 py-2 rounded-sm cursor-pointer outline-none" onchange="setStatusFilter(this.value)">
                        <option value="all">All Statuses</option>
                        <option value="Unreviewed">⏳ Unreviewed</option>
                        <option value="Perfect verified">✅ Perfect Verified</option>
                        <option value="Recheck">⚠️ Recheck</option>
                        <option value="Reedits">🔄 Need Reedits</option>
                        <option value="Product missing">❌ Product Missing</option>
                        <option value="Incorrect link">🔗 Incorrect Link</option>
                        <option disabled>──────────</option>
                        <option value="shopify_draft_archived">📦 Draft/Archived Products</option>
                    </select>
                    <button onclick="setFilter('all')" id="btn-filter-all" class="bg-[#C4F101] text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-[#C4F101]">Show All</button>
                    <button onclick="setFilter('mismatch')" id="btn-filter-mismatch" class="bg-zinc-900 hover:bg-zinc-850 text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-zinc-800">Mismatches (0)</button>
                </div>
                <span class="text-lg font-black tracking-tight text-white">ELITE <span class="text-[#C4F101]">TI</span></span>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <div class="flex-grow max-w-[1850px] w-full mx-auto p-4 md:p-8 flex flex-col lg:flex-row gap-6">
        
        <!-- Left Sidebar: Brand Navigation list -->
        <aside class="w-full lg:w-64 flex-shrink-0 flex flex-col gap-4 bg-[#141416] border border-zinc-800 p-4 rounded-md h-fit">
            <div class="border-b border-zinc-800 pb-3">
                <span class="text-[10px] font-black tracking-widest uppercase text-gray-400">Select Brand</span>
            </div>
            <div id="brand-list" class="flex flex-col gap-1">
                <!-- Dynamically populated -->
            </div>
        </aside>

        <!-- Right Content: Products Grid -->
        <main class="flex-grow flex flex-col gap-6">
            <div class="bg-[#141416] border border-zinc-800 p-4 rounded-md flex justify-between items-center">
                <div class="flex items-center gap-6">
                    <h2 id="active-brand-title" class="text-base font-black text-white uppercase tracking-tight">All Brands Portfolio</h2>
                    <div id="status-stats" class="hidden sm:flex items-center gap-3">
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-zinc-400 bg-zinc-900 border border-zinc-800 px-2 py-1 rounded">⏳ Unreviewed: <span id="stat-unreviewed" class="text-white ml-1">0</span></span>
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-[#C4F101] bg-[#C4F101]/10 border border-[#C4F101]/30 px-2 py-1 rounded">✅ Perfect: <span id="stat-perfect" class="text-white ml-1">0</span></span>
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-orange-400 bg-orange-500/10 border border-orange-500/30 px-2 py-1 rounded">⚠️ Recheck: <span id="stat-recheck" class="text-white ml-1">0</span></span>
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-red-400 bg-red-500/10 border border-red-500/30 px-2 py-1 rounded">🔄 Reedits: <span id="stat-reedits" class="text-white ml-1">0</span></span>
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-purple-400 bg-purple-500/10 border border-purple-500/30 px-2 py-1 rounded">❌ Missing: <span id="stat-missing" class="text-white ml-1">0</span></span>
                        <span class="text-[9px] font-extrabold uppercase tracking-widest text-pink-400 bg-pink-500/10 border border-pink-500/30 px-2 py-1 rounded">🔗 Bad Link: <span id="stat-link" class="text-white ml-1">0</span></span>
                    </div>
                </div>
                <div class="flex items-center gap-4 w-full md:w-auto">
                    <div class="relative w-full md:w-64">
                        <input type="text" id="product-search" oninput="renderProducts()" placeholder="SEARCH PRODUCTS..." class="w-full bg-zinc-950 border border-zinc-800 text-white text-[10px] p-2 outline-none focus:border-[#C4F101] transition-all rounded shadow-inner uppercase font-bold tracking-wider">
                    </div>
                    <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest bg-zinc-950 px-3 py-1.5 border border-zinc-800 rounded-sm flex-shrink-0">
                        Showing <span id="visible-count" class="text-[#C4F101]">0</span> of <span id="total-count">0</span> products
                    </div>
                </div>
            </div>

            <!-- Products List -->
            <div id="products-list" class="flex flex-col gap-6">
                <!-- Dynamic Product Columns Injected Here -->
            </div>

            <!-- Empty State -->
            <div id="empty-state" class="hidden py-32 text-center flex flex-col items-center justify-center border border-zinc-800/40 bg-zinc-950/20 rounded-md">
                <span class="text-[10px] font-black tracking-widest text-zinc-500 uppercase">No Products Match Filters</span>
            </div>
        </main>
    </div>

    <!-- Lightbox Overlay -->
    <div id="lightbox" onclick="closeLightbox()" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-4">
        <img id="lightbox-img" src="" class="max-w-full max-h-full object-contain rounded-sm shadow-2xl">
    </div>

    <!-- Notification Toast -->
    <div id="toast" class="fixed bottom-6 right-6 z-50 bg-zinc-900 border border-zinc-800 text-white text-xs font-bold py-3 px-6 rounded-md shadow-2xl transition-all duration-300 opacity-0 translate-y-2 pointer-events-none uppercase tracking-wide flex items-center gap-2">
        <span id="toast-status-icon" class="w-2 h-2 rounded-full bg-[#C4F101]"></span>
        <span id="toast-msg"></span>
    </div>

    <!-- Data Injection -->
    <script>
        const productsData = %PRODUCT_DATA%;
        let currentMake = 'BMW';
        let currentFilter = 'all'; // 'all' or 'mismatch'
        let currentStatusFilter = 'all';
        let serverActive = false;

        function updateStats() {
            let countUnreviewed = 0;
            let countPerfect = 0;
            let countRecheck = 0;
            let countReedits = 0;
            let countMissing = 0;
            let countLink = 0;
            
            const makeFiltered = productsData.filter(p => currentMake === 'all' || p.make === currentMake);
            makeFiltered.forEach(p => {
                if (p.review_status === 'Unreviewed') countUnreviewed++;
                else if (p.review_status === 'Perfect verified') countPerfect++;
                else if (p.review_status === 'Recheck') countRecheck++;
                else if (p.review_status === 'Reedits') countReedits++;
                else if (p.review_status === 'Product missing') countMissing++;
                else if (p.review_status === 'Incorrect link') countLink++;
            });
            
            document.getElementById('stat-unreviewed').textContent = countUnreviewed;
            document.getElementById('stat-perfect').textContent = countPerfect;
            document.getElementById('stat-recheck').textContent = countRecheck;
            document.getElementById('stat-reedits').textContent = countReedits;
            document.getElementById('stat-missing').textContent = countMissing;
            document.getElementById('stat-link').textContent = countLink;
        }

        async function updateReviewStatus(shortProdId, newStatus, btnElement = null) {
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }
            try {
                const response = await fetch('http://localhost:8000/api/update_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: shortProdId, status: newStatus })
                });
                if (!response.ok) throw new Error("Server request failed");
                
                const prod = productsData.find(p => p.short_id === shortProdId);
                if (prod) prod.review_status = newStatus;
                
                if (btnElement) {
                    const container = btnElement.parentElement;
                    container.querySelectorAll('.status-btn').forEach(b => {
                        b.className = 'status-btn text-zinc-500 hover:text-zinc-300 border border-transparent px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    });
                    
                    if (newStatus === 'Unreviewed') {
                        btnElement.className = 'status-btn bg-zinc-800 text-white border border-zinc-600 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    } else if (newStatus === 'Perfect verified') {
                        btnElement.className = 'status-btn bg-[#C4F101]/20 text-[#C4F101] border border-[#C4F101]/50 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    } else if (newStatus === 'Recheck') {
                        btnElement.className = 'status-btn bg-orange-500/20 text-orange-400 border border-orange-500/50 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    } else if (newStatus === 'Reedits') {
                        btnElement.className = 'status-btn bg-red-500/20 text-red-400 border border-red-500/50 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    } else if (newStatus === 'Product missing') {
                        btnElement.className = 'status-btn bg-purple-500/20 text-purple-400 border border-purple-500/50 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    } else if (newStatus === 'Incorrect link') {
                        btnElement.className = 'status-btn bg-pink-500/20 text-pink-400 border border-pink-500/50 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all';
                    }
                    
                    if (currentStatusFilter !== 'all' && currentStatusFilter !== newStatus && currentStatusFilter !== 'shopify_draft_archived') {
                        const section = btnElement.closest('section');
                        if (section) {
                            section.remove();
                            const visibleSpan = document.getElementById('visible-count');
                            if (visibleSpan) {
                                const newCount = parseInt(visibleSpan.textContent) - 1;
                                visibleSpan.textContent = newCount;
                                if (newCount <= 0) {
                                    document.getElementById('empty-state').classList.remove('hidden');
                                }
                            }
                        }
                    }
                }
                
                updateStats();
                initSidebar(); // Refresh percentages on the left sidebar
                showToast("Review status saved!");
            } catch (err) {
                console.error(err);
                showToast("Error saving status.", "error");
            }
        }

        async function openInFinder(folderPath) {
            if (!folderPath) {
                showToast("Folder path not found", "error");
                return;
            }
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }
            try {
                const response = await fetch('http://localhost:8000/api/open_folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: folderPath })
                });
                if (!response.ok) throw new Error("Server request failed");
            } catch (err) {
                console.error(err);
                showToast("Error opening folder.", "error");
            }
        }

        function updateTileSize(val) {
            document.documentElement.style.setProperty('--tile-size', val + 'px');
            document.getElementById('size-value').textContent = val + 'px';
        }

        // Check if helper backend server is running
        async function checkServerStatus() {
            try {
                const res = await fetch('http://localhost:8000/api/status', { method: 'GET' });
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'running') {
                        document.getElementById('server-dot').className = "w-2.5 h-2.5 rounded-full bg-[#C4F101] shadow-[0_0_8px_#C4F101]";
                        document.getElementById('server-text').className = "text-xs font-bold uppercase tracking-wider text-[#C4F101]";
                        document.getElementById('server-text').textContent = "Shopify Helper Online";
                        serverActive = true;
                        
                        // Fetch the latest statuses to prevent regression on page refresh
                        try {
                            const statusRes = await fetch('http://localhost:8000/api/get_statuses', { method: 'GET' });
                            if (statusRes.ok) {
                                const latestStatuses = await statusRes.json();
                                let updated = false;
                                productsData.forEach(p => {
                                    const shortId = p.product_id.split('/').pop();
                                    if (latestStatuses[shortId] && p.review_status !== latestStatuses[shortId]) {
                                        p.review_status = latestStatuses[shortId];
                                        updated = true;
                                    }
                                });
                                if (updated) {
                                    renderProducts();
                                    initSidebar();
                                }
                            }
                        } catch (err) {
                            console.error("Failed to fetch latest statuses", err);
                        }
                    }
                }
            } catch (e) {
                // Keep offline status
            }
        }

        function showToast(msg, type = "success") {
            const toast = document.getElementById('toast');
            const msgEl = document.getElementById('toast-msg');
            const icon = document.getElementById('toast-status-icon');
            
            icon.className = type === "success" ? "w-2 h-2 rounded-full bg-[#C4F101]" : "w-2 h-2 rounded-full bg-red-500";
            msgEl.textContent = msg;
            
            toast.classList.remove('opacity-0', 'translate-y-2', 'pointer-events-none');
            toast.classList.add('opacity-100', 'translate-y-0');
            
            setTimeout(() => {
                toast.classList.remove('opacity-100', 'translate-y-0');
                toast.classList.add('opacity-0', 'translate-y-2', 'pointer-events-none');
            }, 3000);
        }

        // Initialize brand list sidebar
        function initSidebar() {
            const list = document.getElementById('brand-list');
            list.innerHTML = '';

            // Calculate brand sizes
            const brandCounts = {};
            const brandMismatches = {};
            const brandPerfect = {};
            
            productsData.forEach(p => {
                brandCounts[p.make] = (brandCounts[p.make] || 0) + 1;
                if (p.is_mismatch) {
                    brandMismatches[p.make] = (brandMismatches[p.make] || 0) + 1;
                }
                if (p.review_status === 'Perfect verified') {
                    brandPerfect[p.make] = (brandPerfect[p.make] || 0) + 1;
                }
            });

            // Global stats
            const totalProducts = productsData.length;
            const totalMismatches = productsData.filter(p => p.is_mismatch).length;
            const totalPerfect = productsData.filter(p => p.review_status === 'Perfect verified').length;
            const totalPercent = totalProducts > 0 ? Math.round((totalPerfect / totalProducts) * 100) : 0;
            
            document.getElementById('btn-filter-mismatch').textContent = `Mismatches (${totalMismatches})`;

            // All button
            const allBtn = document.createElement('button');
            allBtn.onclick = () => selectBrand('all');
            allBtn.className = `brand-btn text-left p-3 rounded-sm border transition-all flex flex-col w-full ${currentMake === 'all' ? 'bg-[#C4F101] border-[#C4F101] text-black font-semibold shadow-[0_0_10px_rgba(196,241,1,0.15)]' : 'bg-zinc-950 hover:bg-zinc-900 border-zinc-800 text-zinc-400'}`;
            allBtn.innerHTML = `
                <div class="flex justify-between items-center w-full mb-1.5">
                    <span class="font-extrabold text-xs uppercase ${currentMake === 'all' ? 'text-black' : 'text-white'}">ALL PORTFOLIO</span>
                    <span class="text-[10px] font-black ${currentMake === 'all' ? 'text-black' : 'text-[#C4F101]'}">${totalPercent}% Done</span>
                </div>
                <div class="w-full ${currentMake === 'all' ? 'bg-black/20' : 'bg-black/40'} rounded-full h-1 overflow-hidden">
                    <div class="${currentMake === 'all' ? 'bg-black' : 'bg-[#C4F101]'} h-1 rounded-full transition-all duration-500" style="width: ${totalPercent}%"></div>
                </div>
            `;
            list.appendChild(allBtn);

            // Per brand
            const uniqueMakes = [...new Set(productsData.map(p => p.make))].sort();
            uniqueMakes.forEach(make => {
                const count = brandCounts[make] || 0;
                const mis = brandMismatches[make] || 0;
                const perf = brandPerfect[make] || 0;
                const percent = count > 0 ? Math.round((perf / count) * 100) : 0;
                const active = currentMake === make;

                const btn = document.createElement('button');
                btn.onclick = () => selectBrand(make);
                btn.className = `brand-btn text-left p-3 rounded-sm border transition-all flex flex-col w-full ${active ? 'bg-[#C4F101] border-[#C4F101] text-black font-semibold shadow-[0_0_10px_rgba(196,241,1,0.15)]' : 'bg-zinc-950 hover:bg-zinc-900 border-zinc-800 text-zinc-400'}`;
                btn.innerHTML = `
                    <div class="flex justify-between items-center w-full mb-1.5">
                        <span class="font-extrabold text-xs uppercase ${active ? 'text-black' : 'text-white'}">${make}</span>
                        <div class="flex items-center gap-2">
                            ${mis > 0 ? `<span class="text-[9px] font-bold px-1.5 py-0.5 rounded-sm ${active ? 'bg-red-500/20 text-red-900' : 'bg-red-500/10 text-red-400'}">${mis} Bad</span>` : ''}
                            <span class="text-[10px] font-black ${active ? 'text-black' : 'text-[#C4F101]'}">${percent}%</span>
                        </div>
                    </div>
                    <div class="w-full ${active ? 'bg-black/20' : 'bg-black/40'} rounded-full h-1 overflow-hidden">
                        <div class="${active ? 'bg-black' : 'bg-[#C4F101]'} h-1 rounded-full transition-all duration-500" style="width: ${percent}%"></div>
                    </div>
                `;
                list.appendChild(btn);
            });
        }

        function selectBrand(make) {
            currentMake = make;
            document.getElementById('active-brand-title').textContent = make === 'all' ? 'All Brands Portfolio' : `${make} Portfolio`;
            initSidebar();
            renderProducts();
        }

        function setFilter(filter) {
            currentFilter = filter;
            const btnAll = document.getElementById('btn-filter-all');
            const btnMis = document.getElementById('btn-filter-mismatch');

            if (filter === 'all') {
                btnAll.className = "bg-[#C4F101] text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-[#C4F101]";
                btnMis.className = "bg-zinc-900 hover:bg-zinc-850 text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-zinc-800";
            } else {
                btnAll.className = "bg-zinc-900 hover:bg-zinc-850 text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-zinc-800";
                btnMis.className = "bg-red-950 text-red-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded-sm transition-all border border-red-800 shadow-[0_0_10px_rgba(239,68,68,0.1)]";
            }
            renderProducts();
        }

        function setStatusFilter(val) {
            currentStatusFilter = val;
            renderProducts();
        }

        // Live Action: Delete Image from Shopify
        async function deleteImage(btnElement, mediaId, productId) {
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }
            
            if (!confirm("Are you sure you want to delete this image from your Shopify product? This cannot be undone!")) {
                return;
            }

            const imgCard = btnElement.closest('.image-card');
            imgCard.style.opacity = '0.4';

            try {
                const response = await fetch('http://localhost:8000/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mediaId, productId })
                });

                if (!response.ok) throw new Error("HTTP request failed");
                const resData = await response.json();

                if (resData.errors && resData.errors.length > 0) {
                    throw new Error(resData.errors[0].message);
                }

                if (resData.data && resData.data.productDeleteMedia && resData.data.productDeleteMedia.userErrors.length > 0) {
                    throw new Error(resData.data.productDeleteMedia.userErrors[0].message);
                }

                imgCard.remove();
                showToast("Image successfully deleted from Shopify storefront!");
                
                // Update live count label
                const countContainer = document.getElementById(`live-count-${productId.split('/').pop()}`);
                if (countContainer) {
                    const currentVal = parseInt(countContainer.textContent);
                    countContainer.textContent = `${currentVal - 1} Images`;
                }

            } catch (error) {
                imgCard.style.opacity = '1';
                showToast(error.message, "error");
            }
        }

        // Drag and drop variables
        let draggedElement = null;
        let dragRafPending = false; // RAF throttle flag
        let reorderDebounceTimer = null; // Debounce timer for API saves
        let lastCheckboxClicked = null; // For shift-click multi-select on edited images
        let lastRawCheckboxClicked = null; // For shift-click on raw images

        // Store selected images per product
        const selectedLocalImages = {}; // edited
        const selectedRawImages = {};   // raw

        function updateLocalSelectAllBtnText(shortProdId) {
            const container = document.getElementById(`edited-list-${shortProdId}`);
            if (!container) return;
            const allChks = container.querySelectorAll('.local-select-chk');
            const selectAllBtn = document.getElementById(`select-all-local-btn-${shortProdId}`);
            if (!selectAllBtn) return;
            if (allChks.length > 0 && Array.from(allChks).every(c => c.checked)) {
                selectAllBtn.textContent = 'Deselect All';
            } else {
                selectAllBtn.textContent = 'Select All';
            }
        }

        function updateRawSelectAllBtnText(shortProdId) {
            const container = document.getElementById(`raw-list-${shortProdId}`);
            if (!container) return;
            const allChks = container.querySelectorAll('.raw-select-chk');
            const selectAllBtn = document.getElementById(`select-all-raw-btn-${shortProdId}`);
            if (!selectAllBtn) return;
            if (allChks.length > 0 && Array.from(allChks).every(c => c.checked)) {
                selectAllBtn.textContent = 'Deselect All';
            } else {
                selectAllBtn.textContent = 'Select All';
            }
        }

        function handleLocalCheckboxChange(chk, productId, shortProdId, event) {
            const path = chk.getAttribute('data-path');
            
            // Shift-click: select range between last clicked and this one
            if (event && event.shiftKey && lastCheckboxClicked && lastCheckboxClicked !== chk) {
                const container = chk.closest('.local-images-list');
                if (container) {
                    const allChks = Array.from(container.querySelectorAll('.local-select-chk'));
                    const lastIdx = allChks.indexOf(lastCheckboxClicked);
                    const currIdx = allChks.indexOf(chk);
                    const [start, end] = lastIdx < currIdx ? [lastIdx, currIdx] : [currIdx, lastIdx];
                    allChks.slice(start, end + 1).forEach(c => {
                        c.checked = true;
                        const p = c.getAttribute('data-path');
                        if (!selectedLocalImages[productId]) selectedLocalImages[productId] = [];
                        if (!selectedLocalImages[productId].includes(p)) selectedLocalImages[productId].push(p);
                    });
                }
            } else {
                if (!selectedLocalImages[productId]) {
                    selectedLocalImages[productId] = [];
                }
                if (chk.checked) {
                    if (!selectedLocalImages[productId].includes(path)) {
                        selectedLocalImages[productId].push(path);
                    }
                } else {
                    selectedLocalImages[productId] = selectedLocalImages[productId].filter(p => p !== path);
                }
            }
            
            lastCheckboxClicked = chk;

            const btn = document.getElementById(`bulk-local-btn-${shortProdId}`);
            if (btn) {
                const count = selectedLocalImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                if (count > 0) {
                    btn.classList.remove('hidden');
                } else {
                    btn.classList.add('hidden');
                }
            }
            updateLocalSelectAllBtnText(shortProdId);
        }
        
        function selectAllLocalImages(productId, shortProdId, containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            const allChks = container.querySelectorAll('.local-select-chk');
            if (!selectedLocalImages[productId]) selectedLocalImages[productId] = [];
            
            const allSelected = allChks.length > 0 && Array.from(allChks).every(c => c.checked);
            
            allChks.forEach(c => {
                c.checked = !allSelected;
                const p = c.getAttribute('data-path');
                if (!allSelected) {
                    if (!selectedLocalImages[productId].includes(p)) selectedLocalImages[productId].push(p);
                } else {
                    selectedLocalImages[productId] = selectedLocalImages[productId].filter(img => img !== p);
                }
            });
            
            const selectAllBtn = document.getElementById(`select-all-local-btn-${shortProdId}`);
            if (selectAllBtn) {
                selectAllBtn.textContent = allSelected ? 'Select All' : 'Deselect All';
            }
            
            const btn = document.getElementById(`bulk-local-btn-${shortProdId}`);
            if (btn) {
                const count = selectedLocalImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                if (count > 0) {
                    btn.classList.remove('hidden');
                } else {
                    btn.classList.add('hidden');
                }
            }
        }

        async function bulkDeleteLocal(productId, shortProdId, path) {
            const paths = selectedLocalImages[productId] || [];
            if (paths.length === 0) return;

            if (!serverActive) {
                showToast("Helper Server Offline! Run visual_manager_server.py first.", "error");
                return;
            }

            if (!confirm(`Are you sure you want to move the ${paths.length} selected local edited images to trash?`)) {
                return;
            }

            const btnEl = document.getElementById(`bulk-local-btn-${shortProdId}`);
            const container = btnEl.closest('section').querySelector('.local-images-list');
            showLoadingOverlay(container, true);

            let successCount = 0;
            for (const path of paths) {
                try {
                    const response = await fetch('http://localhost:8000/api/delete_local_image', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filePath: path })
                    });
                    if (response.ok) {
                        const resData = await response.json();
                        if (!resData.error) {
                            successCount++;
                            const card = Array.from(container.querySelectorAll('.local-image-card')).find(c => c.getAttribute('data-path') === path);
                            if (card) card.remove();
                        }
                    }
                } catch (e) {
                    console.error("Error deleting local image:", e);
                }
            }

            showLoadingOverlay(container, false);
            showToast(`Moved ${successCount} local edited images to trash!`);

            selectedLocalImages[productId] = [];
            btnEl.classList.add('hidden');
            btnEl.textContent = `Delete Selected (0)`;
            updateLocalSelectAllBtnText(shortProdId);
        }

        // ----- CMD/SHIFT click on edited image cards -----
        function handleEditedCardClick(event, cardEl, productId, shortProdId) {
            if (!event.metaKey && !event.shiftKey) return; // only intercept modifier clicks
            event.preventDefault();
            event.stopPropagation();
            const chk = cardEl.querySelector('.local-select-chk');
            if (!chk) return;
            
            if (event.shiftKey && lastCheckboxClicked && lastCheckboxClicked !== chk) {
                // Range select
                const container = cardEl.closest('.local-images-list');
                if (container) {
                    const allChks = Array.from(container.querySelectorAll('.local-select-chk'));
                    const lastIdx = allChks.indexOf(lastCheckboxClicked);
                    const currIdx = allChks.indexOf(chk);
                    const [start, end] = lastIdx < currIdx ? [lastIdx, currIdx] : [currIdx, lastIdx];
                    if (!selectedLocalImages[productId]) selectedLocalImages[productId] = [];
                    allChks.slice(start, end + 1).forEach(c => {
                        c.checked = true;
                        const p = c.getAttribute('data-path');
                        if (!selectedLocalImages[productId].includes(p)) selectedLocalImages[productId].push(p);
                    });
                }
            } else {
                // Cmd+click: toggle individual
                chk.checked = !chk.checked;
                const path = chk.getAttribute('data-path');
                if (!selectedLocalImages[productId]) selectedLocalImages[productId] = [];
                if (chk.checked) {
                    if (!selectedLocalImages[productId].includes(path)) selectedLocalImages[productId].push(path);
                } else {
                    selectedLocalImages[productId] = selectedLocalImages[productId].filter(p => p !== path);
                }
            }
            lastCheckboxClicked = chk;
            // Update button
            const btn = document.getElementById(`bulk-local-btn-${shortProdId}`);
            if (btn) {
                const count = selectedLocalImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                btn.classList.toggle('hidden', count === 0);
            }
            updateLocalSelectAllBtnText(shortProdId);
        }

        // ----- CMD/SHIFT click on RAW image cards -----
        function handleRawCardClick(event, cardEl, productId, shortProdId) {
            if (!event.metaKey && !event.shiftKey) return;
            event.preventDefault();
            event.stopPropagation();
            const chk = cardEl.querySelector('.raw-select-chk');
            if (!chk) return;
            
            if (event.shiftKey && lastRawCheckboxClicked && lastRawCheckboxClicked !== chk) {
                const container = cardEl.closest('.raw-images-list');
                if (container) {
                    const allChks = Array.from(container.querySelectorAll('.raw-select-chk'));
                    const lastIdx = allChks.indexOf(lastRawCheckboxClicked);
                    const currIdx = allChks.indexOf(chk);
                    const [start, end] = lastIdx < currIdx ? [lastIdx, currIdx] : [currIdx, lastIdx];
                    if (!selectedRawImages[productId]) selectedRawImages[productId] = [];
                    allChks.slice(start, end + 1).forEach(c => {
                        c.checked = true;
                        const p = c.getAttribute('data-path');
                        if (!selectedRawImages[productId].includes(p)) selectedRawImages[productId].push(p);
                    });
                }
            } else {
                chk.checked = !chk.checked;
                const path = chk.getAttribute('data-path');
                if (!selectedRawImages[productId]) selectedRawImages[productId] = [];
                if (chk.checked) {
                    if (!selectedRawImages[productId].includes(path)) selectedRawImages[productId].push(path);
                } else {
                    selectedRawImages[productId] = selectedRawImages[productId].filter(p => p !== path);
                }
            }
            lastRawCheckboxClicked = chk;
            const btn = document.getElementById(`bulk-raw-btn-${shortProdId}`);
            if (btn) {
                const count = selectedRawImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                btn.classList.toggle('hidden', count === 0);
            }
            updateRawSelectAllBtnText(shortProdId);
        }
        
        function handleRawCheckboxChange(chk, productId, shortProdId, event) {
            const path = chk.getAttribute('data-path');
            if (event && event.shiftKey && lastRawCheckboxClicked && lastRawCheckboxClicked !== chk) {
                const container = chk.closest('.raw-images-list');
                if (container) {
                    const allChks = Array.from(container.querySelectorAll('.raw-select-chk'));
                    const lastIdx = allChks.indexOf(lastRawCheckboxClicked);
                    const currIdx = allChks.indexOf(chk);
                    const [start, end] = lastIdx < currIdx ? [lastIdx, currIdx] : [currIdx, lastIdx];
                    if (!selectedRawImages[productId]) selectedRawImages[productId] = [];
                    allChks.slice(start, end + 1).forEach(c => {
                        c.checked = true;
                        const p = c.getAttribute('data-path');
                        if (!selectedRawImages[productId].includes(p)) selectedRawImages[productId].push(p);
                    });
                }
            } else {
                if (!selectedRawImages[productId]) selectedRawImages[productId] = [];
                if (chk.checked) {
                    if (!selectedRawImages[productId].includes(path)) selectedRawImages[productId].push(path);
                } else {
                    selectedRawImages[productId] = selectedRawImages[productId].filter(p => p !== path);
                }
            }
            lastRawCheckboxClicked = chk;
            const btn = document.getElementById(`bulk-raw-btn-${shortProdId}`);
            if (btn) {
                const count = selectedRawImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                btn.classList.toggle('hidden', count === 0);
            }
            updateRawSelectAllBtnText(shortProdId);
        }

        function selectAllRawImages(productId, shortProdId, containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            const allChks = container.querySelectorAll('.raw-select-chk');
            if (!selectedRawImages[productId]) selectedRawImages[productId] = [];
            
            const allSelected = allChks.length > 0 && Array.from(allChks).every(c => c.checked);
            
            allChks.forEach(c => {
                c.checked = !allSelected;
                const p = c.getAttribute('data-path');
                if (!allSelected) {
                    if (!selectedRawImages[productId].includes(p)) selectedRawImages[productId].push(p);
                } else {
                    selectedRawImages[productId] = selectedRawImages[productId].filter(img => img !== p);
                }
            });
            
            const selectAllBtn = document.getElementById(`select-all-raw-btn-${shortProdId}`);
            if (selectAllBtn) {
                selectAllBtn.textContent = allSelected ? 'Select All' : 'Deselect All';
            }
            
            const btn = document.getElementById(`bulk-raw-btn-${shortProdId}`);
            if (btn) {
                const count = selectedRawImages[productId].length;
                btn.textContent = `Delete Selected (${count})`;
                btn.classList.toggle('hidden', count === 0);
            }
        }

        async function bulkDeleteRaw(productId, shortProdId) {
            const paths = selectedRawImages[productId] || [];
            if (paths.length === 0) return;
            if (!serverActive) { showToast("Helper Server Offline!", "error"); return; }
            if (!confirm(`Move ${paths.length} selected raw images to trash?`)) return;
            const btnEl = document.getElementById(`bulk-raw-btn-${shortProdId}`);
            const container = document.getElementById(`raw-list-${shortProdId}`);
            showLoadingOverlay(container, true);
            let successCount = 0;
            for (const path of paths) {
                try {
                    const response = await fetch('http://localhost:8000/api/delete_local_image', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filePath: path })
                    });
                    if (response.ok) {
                        const resData = await response.json();
                        if (!resData.error) {
                            successCount++;
                            const card = Array.from(container.querySelectorAll('.raw-image-card')).find(c => c.getAttribute('data-path') === path);
                            if (card) card.remove();
                        }
                    }
                } catch(e) { console.error(e); }
            }
            showLoadingOverlay(container, false);
            showToast(`Moved ${successCount} raw images to trash!`);
            selectedRawImages[productId] = [];
            btnEl.classList.add('hidden');
            btnEl.textContent = 'Delete Selected (0)';
            updateRawSelectAllBtnText(shortProdId);
        }

        let lastDragOverTarget = null;

        function handleDragStart(e) {
            if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'button') {
                e.preventDefault();
                return;
            }

            draggedElement = this;
            const path = this.getAttribute('data-path');
            if (path) {
                const listEl = this.closest('.local-images-list') || this.closest('.raw-images-list');
                if (listEl) {
                    const productId = listEl.getAttribute('data-product-id');
                    const isRaw = listEl.classList.contains('raw-images-list');
                    const chk = this.querySelector('.local-select-chk') || this.querySelector('.raw-select-chk');
                    const selectionArray = isRaw ? selectedRawImages[productId] : selectedLocalImages[productId];
                    
                    if (chk && chk.checked && selectionArray && selectionArray.length > 0) {
                        e.dataTransfer.setData('text/plain', JSON.stringify({ 
                            type: 'local-images-bulk', 
                            paths: selectionArray 
                        }));
                    } else {
                        e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'local-image', path: path }));
                    }
                } else {
                    e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'local-image', path: path }));
                }
                e.dataTransfer.effectAllowed = 'copy';
            } else {
                e.dataTransfer.setData('text/plain', 'shopify-image');
                e.dataTransfer.effectAllowed = 'move';
            }
            this.style.opacity = '0.4';
        }

        function handleDragOver(e) {
            if (e.preventDefault) e.preventDefault();

            // Check if we are sorting shopify images
            if (draggedElement && !draggedElement.getAttribute('data-path')) {
                e.dataTransfer.dropEffect = 'move';
                if (draggedElement !== this && this.classList.contains('image-card')) {
                    if (lastDragOverTarget && lastDragOverTarget !== this) {
                        lastDragOverTarget.classList.remove('border-l-4', 'border-[#C4F101]');
                    }
                    this.classList.add('border-l-4', 'border-[#C4F101]');
                    lastDragOverTarget = this;
                }
            } else {
                e.dataTransfer.dropEffect = 'copy';
            }
            return false;
        }

        function handleDragEnter(e) {
            if (draggedElement && !draggedElement.getAttribute('data-path')) {
                // Sorting Shopify: handled by dragover
            } else {
                // Uploading from outside: show dashed border
                this.classList.add('border-[#C4F101]', 'border-dashed');
            }
        }

        function handleDragLeave(e) {
            this.classList.remove('border-[#C4F101]', 'border-dashed', 'border-l-4', 'border-[#C4F101]');
            if (lastDragOverTarget === this) {
                lastDragOverTarget = null;
            }
        }

        function handleDrop(e) {
            // Clean up visual indicator
            this.classList.remove('border-l-4', 'border-[#C4F101]', 'border-[#C4F101]', 'border-dashed');
            if (lastDragOverTarget === this) {
                lastDragOverTarget = null;
            }

            if (draggedElement && !draggedElement.getAttribute('data-path')) {
                // Sorting Shopify Live CDN images
                e.preventDefault();
                if (e.stopPropagation) e.stopPropagation();
                
                if (draggedElement !== this && this.classList.contains('image-card')) {
                    const container = this.parentNode;
                    const children = Array.from(container.children);
                    const draggedIndex = children.indexOf(draggedElement);
                    const targetIndex = children.indexOf(this);
                    
                    if (draggedIndex !== -1 && targetIndex !== -1) {
                        // Reorder the DOM on drop
                        if (draggedIndex < targetIndex) {
                            container.insertBefore(draggedElement, this.nextSibling);
                        } else {
                            container.insertBefore(draggedElement, this);
                        }
                        // Save the new order
                        const productId = container.getAttribute('data-product-id');
                        saveReorder(container, productId);
                    }
                }
                return false;
            }

            // If dragging files or local images, do NOT stop propagation so it bubbles to handleZoneDrop
            const isFile = e.dataTransfer.files && e.dataTransfer.files.length > 0;
            const dragDataStr = e.dataTransfer.getData('text/plain');
            let isLocalImage = false;
            if (dragDataStr) {
                try {
                    const dragData = JSON.parse(dragDataStr);
                    if (dragData && (dragData.type === 'local-image' || dragData.type === 'local-images-bulk')) {
                        isLocalImage = true;
                    }
                } catch(err) {}
            }
            if (isFile || isLocalImage) {
                return;
            }
            if (e.stopPropagation) {
                e.stopPropagation();
            }
            e.preventDefault();
            return false;
        }

        async function handleDragEnd(e) {
            this.style.opacity = '1';
            dragRafPending = false;
            const container = this.closest('.shopify-images-list');
            if (container) {
                const cards = container.querySelectorAll('.image-card');
                cards.forEach(card => {
                    card.classList.remove('border-[#C4F101]', 'border-dashed', 'border-l-4');
                });
            }
            if (lastDragOverTarget) {
                lastDragOverTarget.classList.remove('border-l-4', 'border-[#C4F101]');
                lastDragOverTarget = null;
            }
        }

        // Zone Drag & Drop Handlers for direct uploads
        function handleZoneDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            this.classList.add('bg-[#C4F101]/10', 'border-2', 'border-[#C4F101]', 'border-dashed', 'p-2', 'rounded-md');
            return false;
        }

        function handleZoneDragEnter(e) {
            e.preventDefault();
            this.classList.add('bg-[#C4F101]/10', 'border-2', 'border-[#C4F101]', 'border-dashed', 'p-2', 'rounded-md');
        }

        function handleZoneDragLeave(e) {
            this.classList.remove('bg-[#C4F101]/10', 'border-2', 'border-[#C4F101]', 'border-dashed', 'p-2', 'rounded-md');
        }

        async function handleZoneDrop(e) {
            e.stopPropagation();
            e.preventDefault();
            this.classList.remove('bg-[#C4F101]/10', 'border-2', 'border-[#C4F101]', 'border-dashed', 'p-2', 'rounded-md');

            const productId = this.getAttribute('data-product-id');
            const shortProdId = productId.split('/').pop();

            // Case 1: Dropped files from OS
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const files = Array.from(e.dataTransfer.files);
                await handleFileUploads(files, productId, this, shortProdId);
                return false;
            }

            // Case 2: Dropped internal local image from raw/edited column
            const dragDataStr = e.dataTransfer.getData('text/plain');
            if (dragDataStr) {
                try {
                    const dragData = JSON.parse(dragDataStr);
                    if (dragData) {
                        if (dragData.type === 'local-images-bulk' && dragData.paths && dragData.paths.length > 0) {
                            await handleLocalPathsBulkUpload(dragData.paths, productId, this, shortProdId);
                        } else if (dragData.type === 'local-image' && dragData.path) {
                            await handleLocalPathUpload(dragData.path, productId, this, shortProdId);
                        }
                    }
                } catch (err) {
                    console.log("Error parsing drop data:", err);
                }
            }
            return false;
        }

        async function handleLocalPathsBulkUpload(paths, productId, container, shortProdId) {
            if (!serverActive) {
                showToast("Helper Server Offline! Cannot upload images.", "error");
                return;
            }

            showLoadingOverlay(container, true);

            for (const localPath of paths) {
                const fileName = localPath.includes('/') ? localPath.split('/').pop() : localPath.split(String.fromCharCode(92)).pop();
                try {
                    const response = await fetch('http://localhost:8000/api/upload_image', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            productId: productId,
                            localPath: localPath
                        })
                    });

                    if (!response.ok) throw new Error(`HTTP upload failed: ${response.statusText}`);
                    const resData = await response.json();

                    if (resData.errors && resData.errors.length > 0) {
                        throw new Error(resData.errors[0].message);
                    }

                    const userErrors = resData.data?.productCreateMedia?.userErrors || [];
                    if (userErrors.length > 0) {
                        throw new Error(userErrors[0].message);
                    }

                    const media = resData.data?.productCreateMedia?.media || [];
                    if (media.length > 0) {
                        const newMedia = media[0];
                        appendUploadedImageToUI(container, newMedia, productId, shortProdId);
                        showToast(`Successfully uploaded ${fileName} to Shopify!`);
                    } else {
                        throw new Error("No media record returned from Shopify.");
                    }
                } catch (error) {
                    showToast(error.message, "error");
                }
            }

            showLoadingOverlay(container, false);
        }

        async function handleFileUploads(files, productId, container, shortProdId) {
            if (!serverActive) {
                showToast("Helper Server Offline! Cannot upload images.", "error");
                return;
            }

            showLoadingOverlay(container, true);

            for (const file of files) {
                try {
                    const fileData = await readFileAsBase64(file);
                    
                    const response = await fetch('http://localhost:8000/api/upload_image', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            productId: productId,
                            fileName: file.name,
                            fileData: fileData
                        })
                    });

                    if (!response.ok) throw new Error(`HTTP upload failed: ${response.statusText}`);
                    const resData = await response.json();

                    if (resData.errors && resData.errors.length > 0) {
                        throw new Error(resData.errors[0].message);
                    }

                    const userErrors = resData.data?.productCreateMedia?.userErrors || [];
                    if (userErrors.length > 0) {
                        throw new Error(userErrors[0].message);
                    }

                    const media = resData.data?.productCreateMedia?.media || [];
                    if (media.length > 0) {
                        const newMedia = media[0];
                        appendUploadedImageToUI(container, newMedia, productId, shortProdId);
                        showToast(`Successfully uploaded ${file.name} to Shopify!`);
                    } else {
                        throw new Error("No media record returned from Shopify.");
                    }
                } catch (error) {
                    showToast(error.message, "error");
                }
            }

            showLoadingOverlay(container, false);
        }

        async function handleLocalPathUpload(localPath, productId, container, shortProdId) {
            if (!serverActive) {
                showToast("Helper Server Offline! Cannot upload images.", "error");
                return;
            }

            showLoadingOverlay(container, true);
            const fileName = localPath.includes('/') ? localPath.split('/').pop() : localPath.split(String.fromCharCode(92)).pop();

            try {
                const response = await fetch('http://localhost:8000/api/upload_image', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        productId: productId,
                        localPath: localPath
                    })
                });

                if (!response.ok) throw new Error(`HTTP upload failed: ${response.statusText}`);
                const resData = await response.json();

                if (resData.errors && resData.errors.length > 0) {
                    throw new Error(resData.errors[0].message);
                }

                const userErrors = resData.data?.productCreateMedia?.userErrors || [];
                if (userErrors.length > 0) {
                    throw new Error(userErrors[0].message);
                }

                const media = resData.data?.productCreateMedia?.media || [];
                if (media.length > 0) {
                    const newMedia = media[0];
                    appendUploadedImageToUI(container, newMedia, productId, shortProdId);
                    showToast(`Successfully uploaded ${fileName} to Shopify!`);
                } else {
                    throw new Error("No media record returned from Shopify.");
                }
            } catch (error) {
                showToast(error.message, "error");
            }

            showLoadingOverlay(container, false);
        }

        function readFileAsBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
                reader.readAsDataURL(file);
            });
        }

        function showLoadingOverlay(container, show) {
            let overlay = container.querySelector('.upload-loading-overlay');
            if (show) {
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.className = "upload-loading-overlay absolute inset-0 bg-black/60 flex items-center justify-center rounded z-20";
                    overlay.innerHTML = `
                        <div class="flex flex-col items-center gap-2">
                            <svg class="animate-spin h-6 w-6 text-[#C4F101]" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span class="text-[10px] font-bold text-white uppercase tracking-wider">Uploading...</span>
                        </div>
                    `;
                    container.style.position = 'relative';
                    container.appendChild(overlay);
                }
            } else {
                if (overlay) overlay.remove();
            }
        }

        function appendUploadedImageToUI(container, media, productId, shortProdId) {
            const emptyTxt = container.querySelector('p');
            if (emptyTxt && emptyTxt.textContent.includes('No live images')) {
                emptyTxt.remove();
            }

            const imgUrl = media.image?.url || 'https://via.placeholder.com/150';
            const imgCard = document.createElement('div');
            imgCard.className = "image-card relative border border-zinc-800 bg-[#0B0B0C] p-0.5 rounded cursor-grab";
            imgCard.draggable = true;
            imgCard.setAttribute('data-media-id', media.id);
            imgCard.setAttribute('onclick', `handleCardClick(event, '${imgUrl}')`);
            imgCard.innerHTML = `
                <img src="${imgUrl}" class="tile-img select-none pointer-events-none">
                <input type="checkbox" class="bulk-select-chk absolute bottom-1 left-1 w-3.5 h-3.5 z-10 accent-red-600 rounded cursor-pointer" data-media-id="${media.id}" onchange="handleCheckboxChange('${productId}', '${shortProdId}')">
                <button class="delete-btn absolute -top-1 -right-1 bg-red-600 hover:bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[9px] font-black border border-black shadow z-10 cursor-pointer" title="Delete from Shopify">×</button>
            `;

            container.appendChild(imgCard);

            imgCard.addEventListener('dragstart', handleDragStart, false);
            imgCard.addEventListener('dragover', handleDragOver, false);
            imgCard.addEventListener('dragenter', handleDragEnter, false);
            imgCard.addEventListener('dragleave', handleDragLeave, false);
            imgCard.addEventListener('drop', handleDrop, false);
            imgCard.addEventListener('dragend', handleDragEnd, false);
            bindDeleteListeners(imgCard);

            const countContainer = document.getElementById(`live-count-${shortProdId}`);
            if (countContainer) {
                const currentVal = parseInt(countContainer.textContent) || 0;
                countContainer.textContent = `${currentVal + 1} Images`;
            }
        }

        async function deleteLocalImage(event, filePath, button) {
            event.stopPropagation();
            event.preventDefault();

            if (!serverActive) {
                showToast("Helper Server Offline! Run visual_manager_server.py first.", "error");
                return;
            }

            if (!confirm(`Are you sure you want to move this local edited image to trash?`)) {
                return;
            }

            const card = button.closest('.local-image-card');
            card.style.opacity = '0.4';

            try {
                const response = await fetch('http://localhost:8000/api/delete_local_image', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filePath })
                });

                if (!response.ok) throw new Error("HTTP request failed");
                const resData = await response.json();

                if (resData.error) {
                    throw new Error(resData.error);
                }

                card.style.transform = 'scale(0.8)';
                card.style.opacity = '0';
                setTimeout(() => {
                    const parent = card.parentNode;
                    card.remove();
                    const countHeader = parent.previousElementSibling?.querySelector('span:nth-child(2)');
                    if (countHeader) {
                        const currentVal = parseInt(countHeader.textContent) || 0;
                        countHeader.textContent = `${Math.max(0, currentVal - 1)} Images`;
                    }
                }, 300);

                showToast("Local file successfully moved to .trash folder.");
            } catch (error) {
                card.style.opacity = '1';
                showToast(error.message, "error");
            }
        }

        function bindDeleteListeners(card) {
            const delBtn = card.querySelector('.delete-btn');
            if (delBtn) {
                const mediaId = card.getAttribute('data-media-id');
                const productId = card.closest('.shopify-images-list').getAttribute('data-product-id');
                delBtn.onclick = (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    deleteImage(delBtn, mediaId, productId);
                };
            }
        }

        function handleCheckboxChange(productId, shortProdId) {
            const list = document.querySelector(`.shopify-images-list[data-product-id="${productId}"]`);
            const checked = list.querySelectorAll('.bulk-select-chk:checked');
            const btn = document.getElementById(`bulk-btn-${shortProdId}`);
            if (checked.length > 0) {
                btn.classList.remove('hidden');
                btn.textContent = `Delete Selected (${checked.length})`;
            } else {
                btn.classList.add('hidden');
            }
        }

        async function bulkDelete(productId, shortProdId) {
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }
            
            const list = document.querySelector(`.shopify-images-list[data-product-id="${productId}"]`);
            const checked = list.querySelectorAll('.bulk-select-chk:checked');
            if (checked.length === 0) return;
            
            if (!confirm(`Are you sure you want to delete these ${checked.length} images from Shopify? This cannot be undone!`)) {
                return;
            }
            
            const btn = document.getElementById(`bulk-btn-${shortProdId}`);
            btn.textContent = "Deleting...";
            btn.disabled = true;
            
            const promises = Array.from(checked).map(async (chk) => {
                const mediaId = chk.getAttribute('data-media-id');
                const imgCard = chk.closest('.image-card');
                imgCard.style.opacity = '0.4';
                try {
                    const response = await fetch('http://localhost:8000/api/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mediaId, productId })
                    });
                    if (response.ok) {
                        const resData = await response.json();
                        if (!resData.errors && (!resData.data || !resData.data.productDeleteMedia || resData.data.productDeleteMedia.userErrors.length === 0)) {
                            imgCard.remove();
                            return true;
                        }
                    }
                } catch (e) {
                    // ignore
                }
                imgCard.style.opacity = '1';
                return false;
            });
            
            const results = await Promise.all(promises);
            const successCount = results.filter(Boolean).length;
            
            showToast(`Successfully deleted ${successCount} images from Shopify!`);
            
            // Sync local HTML cache on disk for all deleted images
            const htmlPath = 'website-catalog/visual_audit_sheet.html';
            try {
                const response = await fetch('http://localhost:8000/api/status'); // Dummy read to ensure server is still there
                // We let the Python server sync handle disk updates
            } catch (e) {}

            // Update live count label
            const countContainer = document.getElementById(`live-count-${shortProdId}`);
            if (countContainer) {
                const currentVal = parseInt(countContainer.textContent);
                countContainer.textContent = `${currentVal - successCount} Images`;
            }
            
            btn.disabled = false;
            btn.classList.add('hidden');
        }

        async function syncLocalToShopify(productId, shortProdId, path) {
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }

            const p = productsData.find(record => record.path === path);
            if (!p) {
                showToast("Product data not found in cache!", "error");
                return;
            }

            const liveCount = p.live_images ? p.live_images.length : 0;
            const localCount = p.drive_images ? p.drive_images.length : 0;

            if (localCount === 0) {
                showToast("No local edited images found to upload!", "error");
                return;
            }

            const msg = `Are you sure you want to SYNC this product?\n\nThis will:\n1. DELETE all ${liveCount} existing images from Shopify.\n2. UPLOAD all ${localCount} local edited images.\n\nThis cannot be undone!`;
            if (!confirm(msg)) {
                return;
            }

            const liveList = document.querySelector(`.shopify-images-list[data-product-id="${productId}"]`);
            if (liveList) {
                showLoadingOverlay(liveList, true);
                const overlayText = liveList.querySelector('.upload-loading-overlay span');
                if (overlayText) overlayText.textContent = "Syncing...";
            }

            const liveImageIds = p.live_images ? p.live_images.map(img => img.id) : [];
            const localPaths = p.drive_images || [];

            try {
                const response = await fetch('http://localhost:8000/api/sync_product_images', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        productId,
                        liveImageIds,
                        localPaths
                    })
                });

                if (!response.ok) throw new Error("Server request failed");
                const resData = await response.json();

                if (resData.errors && resData.errors.length > 0) {
                    showToast(`Sync warnings: ${resData.errors.join(', ')}`, "error");
                }

                p.live_images = resData.uploadedImages || [];
                p.shopify_count = p.live_images.length;
                p.is_mismatch = false;

                let liveImgsHtml = "";
                if (p.live_images.length > 0) {
                    p.live_images.forEach(img => {
                        liveImgsHtml += `
                            <div class="image-card relative border border-zinc-800 bg-[#0B0B0C] p-0.5 rounded cursor-grab" draggable="true" data-media-id="${img.id}" onclick="handleCardClick(event, '${img.url}')">
                                <img src="${img.url}" class="tile-img select-none pointer-events-none">
                                <input type="checkbox" class="bulk-select-chk absolute bottom-1 left-1 w-3.5 h-3.5 z-10 accent-red-600 rounded cursor-pointer" data-media-id="${img.id}" onchange="handleCheckboxChange('${p.product_id}', '${shortProdId}')">
                                <button class="delete-btn absolute -top-1 -right-1 bg-red-600 hover:bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[9px] font-black border border-black shadow z-10 cursor-pointer" title="Delete from Shopify">×</button>
                            </div>
                        `;
                    });
                } else {
                    liveImgsHtml = '<p class="text-zinc-600 text-xs italic py-4">No live images.</p>';
                }
                
                if (liveList) {
                    showLoadingOverlay(liveList, false);
                    liveList.innerHTML = liveImgsHtml;
                }

                const countContainer = document.getElementById(`live-count-${shortProdId}`);
                if (countContainer) {
                    countContainer.textContent = `${p.shopify_count} Images`;
                }

                const cardSection = liveList ? liveList.closest('section') : null;
                if (cardSection) {
                    cardSection.className = "rounded-lg overflow-hidden transition-all duration-300 p-6 flex flex-col gap-4 match-card";
                    const badgeContainer = cardSection.querySelector('.badge-container');
                    if (badgeContainer) {
                        badgeContainer.innerHTML = `
                            <span class="bg-green-500/20 text-green-400 border border-green-500/30 px-3 py-1 text-[10px] font-black rounded-sm uppercase tracking-wider mr-2">VERIFIED MATCH</span>
                            <button onclick="syncLocalToShopify('${p.product_id}', '${shortProdId}')" class="bg-amber-950 hover:bg-amber-900 text-amber-400 border border-amber-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all" title="Delete all Shopify images and upload all local edited images">Sync Local to Shopify</button>
                            <a href="${p.drive_url || '#'}" target="_blank" class="bg-blue-950 hover:bg-blue-900 text-blue-400 border border-blue-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all ${p.drive_url ? '' : 'pointer-events-none opacity-40'}">Drive Folder</a>
                            <a href="${p.shopify_url || '#'}" target="_blank" class="bg-emerald-950 hover:bg-emerald-900 text-[#C4F101] border border-emerald-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all ${p.shopify_url ? '' : 'pointer-events-none opacity-40'}">Shopify Live</a>
                        `;
                    }
                }

                initSidebar();

            } catch (e) {
                showToast(`Sync failed: ${e.message}`, "error");
                if (liveList) {
                    showLoadingOverlay(liveList, false);
                }
            }
        }

        async function saveReorder(container, productId) {
            if (!serverActive) {
                showToast("Helper Server Offline! Cannot save image order.", "error");
                return;
            }

            const cards = container.querySelectorAll('.image-card');
            const moves = [];
            
            cards.forEach((card, index) => {
                const mediaId = card.getAttribute('data-media-id');
                moves.push({
                    id: mediaId,
                    newPosition: String(index)
                });
            });

            try {
                const response = await fetch('http://localhost:8000/api/reorder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productId, moves })
                });

                if (!response.ok) throw new Error("HTTP request failed");
                const resData = await response.json();

                if (resData.errors && resData.errors.length > 0) {
                    throw new Error(resData.errors[0].message);
                }

                if (resData.data && resData.data.productReorderMedia && resData.data.productReorderMedia.userErrors.length > 0) {
                    throw new Error(resData.data.productReorderMedia.userErrors[0].message);
                }

                showToast("Shopify image order successfully updated!");
            } catch (error) {
                showToast(error.message, "error");
            }
        }

        async function makeProductActive(productId, shortProdId) {
            if (!serverActive) {
                showToast("Helper Server is Offline! Run visual_manager_server.py first.", "error");
                return;
            }
            
            if (!confirm("Are you sure you want to make this product ACTIVE on Shopify?")) {
                return;
            }
            
            const btn = document.getElementById(`activate-btn-${shortProdId}`);
            if (btn) {
                btn.textContent = "Updating...";
                btn.disabled = true;
            }
            
            try {
                const response = await fetch('http://localhost:8000/api/update_product_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ productId, status: 'ACTIVE' })
                });
                
                if (!response.ok) throw new Error("HTTP request failed");
                const resData = await response.json();
                
                if (resData.errors && resData.errors.length > 0) {
                    throw new Error(resData.errors[0].message);
                }
                
                const userErrors = resData.data?.productUpdate?.userErrors || [];
                if (userErrors.length > 0) {
                    throw new Error(userErrors[0].message);
                }
                
                showToast("Shopify product successfully marked as ACTIVE!");
                
                const p = productsData.find(record => record.product_id === productId);
                if (p) p.shopify_status = 'ACTIVE';
                renderProducts();
            } catch (error) {
                showToast(error.message, "error");
                if (btn) {
                    btn.textContent = "Make Active";
                    btn.disabled = false;
                }
            }
        }

        function renderProducts() {
            const container = document.getElementById('products-list');
            const emptyState = document.getElementById('empty-state');
            container.innerHTML = '';

            const searchInput = document.getElementById('product-search');
            const searchQuery = searchInput ? searchInput.value.toLowerCase().trim() : '';
            const searchTerms = searchQuery.split(' ').filter(t => t.length > 0);

            const filtered = productsData.filter(p => {
                const matchesMake = currentMake === 'all' || p.make === currentMake;
                const matchesFilter = currentFilter === 'all' || p.is_mismatch;
                
                let matchesStatus = true;
                if (currentStatusFilter === 'shopify_draft_archived') {
                    matchesStatus = (p.shopify_status && (p.shopify_status.toUpperCase() === 'DRAFT' || p.shopify_status.toUpperCase() === 'ARCHIVED'));
                } else {
                    matchesStatus = currentStatusFilter === 'all' || p.review_status === currentStatusFilter;
                }
                
                let matchesSearch = true;
                if (searchTerms.length > 0) {
                    const nameLower = p.name.toLowerCase();
                    const makeLower = p.make.toLowerCase();
                    matchesSearch = searchTerms.every(term => nameLower.includes(term) || makeLower.includes(term));
                }

                return matchesMake && matchesFilter && matchesStatus && matchesSearch;
            });

            document.getElementById('visible-count').textContent = filtered.length;
            const makeFilteredTotal = productsData.filter(p => currentMake === 'all' || p.make === currentMake).length;
            document.getElementById('total-count').textContent = makeFilteredTotal;
            
            updateStats();

            if (filtered.length === 0) {
                emptyState.classList.remove('hidden');
                return;
            }
            emptyState.classList.add('hidden');

            filtered.forEach(p => {
                const cardClass = p.is_mismatch ? "mismatch-card" : "match-card";
                const type = p.is_mismatch ? "mismatch" : "match";

                let statusBadge = "";
                if (p.is_mismatch) {
                    const reasons = Object.keys(p.mismatch_reasons).filter(k => p.mismatch_reasons[k]);
                    statusBadge = `<span class="bg-red-500/20 text-red-400 border border-red-500/30 px-3 py-1 text-[10px] font-black rounded-sm uppercase tracking-wider mr-2">${reasons.join(', ')}</span>`;
                } else {
                    statusBadge = '<span class="bg-green-500/20 text-green-400 border border-green-500/30 px-3 py-1 text-[10px] font-black rounded-sm uppercase tracking-wider mr-2">VERIFIED MATCH</span>';
                }

                const shortProdId = p.short_id;

                let rawImgsHtml = "";
                if (p.raw_images.length > 0) {
                    p.raw_images.forEach(img => {
                        const fileUrl = `http://localhost:8000/api/image?path=` + encodeURIComponent(img);
                        rawImgsHtml += `
                            <div class="raw-image-card relative border border-zinc-800 bg-[#0B0B0C] p-0.5 rounded cursor-pointer" draggable="true" data-path="${img}" onclick="event.metaKey||event.shiftKey ? handleRawCardClick(event,this,'${p.product_id}','${shortProdId}') : handleCardClick(event,'${fileUrl}')">
                                <img src="${fileUrl}" class="tile-img select-none pointer-events-none" title="${img.split('/').pop()}">
                                <input type="checkbox" class="raw-select-chk absolute bottom-1 left-1 w-3.5 h-3.5 z-10 accent-orange-500 rounded cursor-pointer" data-path="${img}" onchange="handleRawCheckboxChange(this, '${p.product_id}', '${shortProdId}', event)">
                            </div>
                        `;
                    });
                } else {
                    rawImgsHtml = '<p class="text-zinc-600 text-xs italic py-4">No raw images.</p>';
                }

                let driveImgsHtml = "";
                if (p.drive_images.length > 0) {
                    p.drive_images.forEach(img => {
                        const fileUrl = `http://localhost:8000/api/image?path=` + encodeURIComponent(img);
                        driveImgsHtml += `
                            <div class="local-image-card relative border border-zinc-800 bg-[#0B0B0C] p-0.5 rounded cursor-pointer" draggable="true" data-path="${img}" onclick="event.metaKey||event.shiftKey ? handleEditedCardClick(event,this,'${p.product_id}','${shortProdId}') : handleCardClick(event,'${fileUrl}')">
                                <img src="${fileUrl}" class="tile-img select-none pointer-events-none" title="${img.split('/').pop()}">
                                <input type="checkbox" class="local-select-chk absolute bottom-1 left-1 w-3.5 h-3.5 z-10 accent-[#C4F101] rounded cursor-pointer" data-path="${img}" onchange="handleLocalCheckboxChange(this, '${p.product_id}', '${shortProdId}', event)">
                                <button class="delete-local-btn absolute -top-1 -right-1 bg-red-600/90 hover:bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[9px] font-black border border-black shadow z-10 cursor-pointer" title="Move to Trash" onclick="deleteLocalImage(event, '${img}', this)">×</button>
                            </div>
                        `;
                    });
                } else {
                    driveImgsHtml = '<p class="text-zinc-600 text-xs italic py-4">No edited images.</p>';
                }

                let liveImgsHtml = "";
                if (p.live_images.length > 0) {
                    p.live_images.forEach(img => {
                        liveImgsHtml += `
                            <div class="image-card relative border border-zinc-800 bg-[#0B0B0C] p-0.5 rounded cursor-grab" draggable="true" data-media-id="${img.id}" onclick="handleCardClick(event, '${img.url}')">
                                <img src="${img.url}" class="tile-img select-none pointer-events-none">
                                <input type="checkbox" class="bulk-select-chk absolute bottom-1 left-1 w-3.5 h-3.5 z-10 accent-red-600 rounded cursor-pointer" data-media-id="${img.id}" onchange="handleCheckboxChange('${p.product_id}', '${shortProdId}')">
                                <button class="delete-btn absolute -top-1 -right-1 bg-red-600 hover:bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-[9px] font-black border border-black shadow z-10 cursor-pointer" title="Delete from Shopify">×</button>
                            </div>
                        `;
                    });
                } else {
                    liveImgsHtml = '<p class="text-zinc-600 text-xs italic py-4">No live images.</p>';
                }

                const item = document.createElement('section');
                item.className = `rounded-lg overflow-hidden transition-all duration-300 p-6 flex flex-col gap-4 ${cardClass}`;
                item.innerHTML = `
                    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-zinc-800/50 pb-4 gap-4">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="text-zinc-600 font-extrabold text-[9px] uppercase tracking-widest bg-zinc-950 px-2 py-0.5 border border-zinc-850 rounded-sm">${p.make}</span>
                                <h2 class="text-base font-black text-white uppercase tracking-tight">${p.name}</h2>
                                <div class="ml-4 flex items-center gap-1 bg-[#0B0B0C] border border-zinc-800 p-0.5 rounded flex-wrap">
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Unreviewed', this)" class="status-btn ${p.review_status === 'Unreviewed' ? 'bg-zinc-800 text-white border-zinc-600' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">⏳ Unreviewed</button>
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Perfect verified', this)" class="status-btn ${p.review_status === 'Perfect verified' ? 'bg-[#C4F101]/20 text-[#C4F101] border-[#C4F101]/50' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">✅ Perfect</button>
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Recheck', this)" class="status-btn ${p.review_status === 'Recheck' ? 'bg-orange-500/20 text-orange-400 border-orange-500/50' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">⚠️ Recheck</button>
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Reedits', this)" class="status-btn ${p.review_status === 'Reedits' ? 'bg-red-500/20 text-red-400 border-red-500/50' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">🔄 Need Reedits</button>
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Product missing', this)" class="status-btn ${p.review_status === 'Product missing' ? 'bg-purple-500/20 text-purple-400 border-purple-500/50' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">❌ Product missing</button>
                                    <button onclick="updateReviewStatus('${shortProdId}', 'Incorrect link', this)" class="status-btn ${p.review_status === 'Incorrect link' ? 'bg-pink-500/20 text-pink-400 border-pink-500/50' : 'text-zinc-500 hover:text-zinc-300 border-transparent'} border px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all">🔗 Incorrect link</button>
                                </div>
                            </div>
                            <span class="text-zinc-500 text-[10px] font-mono select-all block mt-1">${p.path}</span>
                        </div>
                        <div class="badge-container flex items-center gap-2.5">
                            ${statusBadge}
                            <button onclick="syncLocalToShopify('${p.product_id}', '${shortProdId}', \`${p.path}\`)" class="bg-amber-950 hover:bg-amber-900 text-amber-400 border border-amber-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all" title="Delete all Shopify images and upload all local edited images">Sync Local to Shopify</button>
                            <a href="${p.drive_url || '#'}" target="_blank" class="bg-blue-950 hover:bg-blue-900 text-blue-400 border border-blue-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all ${p.drive_url ? '' : 'pointer-events-none opacity-40'}">Drive Folder</a>
                            <a href="${p.shopify_url || '#'}" target="_blank" class="bg-emerald-950 hover:bg-emerald-900 text-[#C4F101] border border-emerald-800 font-extrabold text-[8px] uppercase tracking-wider py-2 px-3 rounded-sm transition-all ${p.shopify_url ? '' : 'pointer-events-none opacity-40'}">Shopify Live</a>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Column 1: Raw images -->
                        <div class="border-r border-zinc-800/30 pr-4">
                            <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3 flex justify-between items-center">
                                <div class="flex items-center gap-2">
                                    <span>🔴 Local Raw Folder</span>
                                    <button onclick="openInFinder(\`${p.raw_folder_path}\`)" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[8px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded transition-all" title="Open folder in Finder">Open in Finder</button>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button onclick="bulkDeleteRaw('${p.product_id}', '${shortProdId}')" class="bg-red-950 hover:bg-red-900 text-red-400 border border-red-800 text-[8px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-sm transition-all hidden" id="bulk-raw-btn-${shortProdId}">Delete Selected (0)</button>
                                    <button id="select-all-raw-btn-${shortProdId}" onclick="selectAllRawImages('${p.product_id}', '${shortProdId}', 'raw-list-${shortProdId}')" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 text-[8px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-sm transition-all">Select All</button>
                                    <span class="text-zinc-500 font-extrabold text-[10px]">${p.raw_count} Images</span>
                                </div>
                            </h3>
                            <div class="raw-images-list flex flex-wrap gap-2" id="raw-list-${shortProdId}" data-product-id="${p.product_id}">
                                ${rawImgsHtml}
                            </div>
                        </div>

                        <!-- Column 2: Edited images -->
                        <div class="border-r border-zinc-800/30 pr-4">
                            <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3 flex justify-between items-center">
                                <div class="flex items-center gap-2">
                                    <span>🟢 Local Edited Folder</span>
                                    ${p.edited_folder_path ? `<button onclick="openInFinder(\`${p.edited_folder_path}\`)" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[8px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded transition-all" title="Open folder in Finder">Open in Finder</button>` : ''}
                                </div>
                                <div class="flex items-center gap-2">
                                    <button onclick="bulkDeleteLocal('${p.product_id}', '${shortProdId}', \`${p.path}\`)" class="bulk-delete-local-btn bg-red-950 hover:bg-red-900 text-red-400 border border-red-800 text-[8px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-sm transition-all hidden" id="bulk-local-btn-${shortProdId}">Delete Selected (0)</button>
                                    <button id="select-all-local-btn-${shortProdId}" onclick="selectAllLocalImages('${p.product_id}', '${shortProdId}', 'edited-list-${shortProdId}')" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 text-[8px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-sm transition-all" title="Select all edited images">Select All</button>
                                    <span class="text-zinc-500 font-extrabold text-[10px]">${p.drive_count} Images</span>
                                </div>
                            </h3>
                            <div class="local-images-list flex flex-wrap gap-2" id="edited-list-${shortProdId}" data-product-id="${p.product_id}">
                                ${driveImgsHtml}
                            </div>
                        </div>

                         <!-- Column 3: Shopify live images (Drag-and-Drop) -->
                        <div>
                            <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-1 flex justify-between items-center">
                                <div class="flex items-center gap-2">
                                    <span>🛍️ Shopify Live CDN</span>
                                    <a href="https://admin.shopify.com/store/myeliteti/products/${shortProdId}?link_source=search" target="_blank" class="bg-[#C4F101]/10 hover:bg-[#C4F101]/20 text-[#C4F101] border border-[#C4F101]/30 text-[8px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded transition-all" title="Open Product in Shopify Admin">Store Link</a>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button onclick="bulkDelete('${p.product_id}', '${shortProdId}', \`${p.path}\`)" class="bulk-delete-btn bg-red-950 hover:bg-red-900 text-red-400 border border-red-800 text-[8px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-sm transition-all hidden" id="bulk-btn-${shortProdId}">Delete Selected (0)</button>
                                    <span id="live-count-${shortProdId}" class="text-white font-extrabold text-[10px]">${p.shopify_count} Images</span>
                                </div>
                            </h3>
                            <div class="text-[9px] font-bold text-emerald-400 uppercase tracking-tight mb-3 truncate max-w-[400px] border border-emerald-950/40 bg-emerald-950/10 px-2 py-1 rounded flex items-center justify-between" title="${p.shopify_title || 'N/A'}">
                                <div>Shopify Title: <span class="text-zinc-300 font-bold select-all">${p.shopify_title || 'Not Linked / Not Found'}</span></div>
                                <div class="flex items-center">
                                    ${p.shopify_status ? `<span class="${p.shopify_status.toLowerCase() === 'active' ? 'bg-emerald-900 text-emerald-400 border-emerald-700' : p.shopify_status.toLowerCase() === 'draft' ? 'bg-amber-900 text-amber-400 border-amber-700' : 'bg-red-900 text-red-400 border-red-700'} border px-1.5 py-0.5 rounded text-[8px] font-black tracking-widest">${p.shopify_status}</span>` : ''}
                                    ${p.shopify_status && p.shopify_status.toLowerCase() !== 'active' ? `<button onclick="makeProductActive('${p.product_id}', '${shortProdId}')" id="activate-btn-${shortProdId}" class="ml-2 bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-700 px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-extrabold transition-all shadow">Make Active</button>` : ''}
                                </div>
                            </div>
                            <div class="shopify-images-list flex flex-wrap gap-2 min-h-[130px] min-w-[200px] p-2 border border-transparent transition-all rounded-md" data-product-id="${p.product_id}">
                                ${liveImgsHtml}
                            </div>
                            ${p.shopify_count > 1 ? '<p class="text-[9px] text-zinc-600 font-semibold italic mt-2">💡 DRAG & DROP PHOTOS TO REARRANGE THEM LIVE ON THE SITE.</p>' : ''}
                        </div>
                    </div>
                `;

                container.appendChild(item);

                // Bind drag-and-drop event listeners to live images
                const liveList = item.querySelector('.shopify-images-list');
                const cards = liveList.querySelectorAll('.image-card');
                
                if (typeof Sortable !== 'undefined') {
                    // Premium SortableJS
                    cards.forEach(card => {
                        bindDeleteListeners(card);
                    });
                    new Sortable(liveList, {
                        animation: 150,
                        draggable: '.image-card',
                        ghostClass: 'opacity-40',
                        onEnd: function (evt) {
                            saveReorder(liveList, productId);
                        }
                    });
                } else {
                    // Bulletproof Native Fallback
                    cards.forEach(card => {
                        card.addEventListener('dragstart', handleDragStart, false);
                        card.addEventListener('dragover', handleDragOver, false);
                        card.addEventListener('dragenter', handleDragEnter, false);
                        card.addEventListener('dragleave', handleDragLeave, false);
                        card.addEventListener('drop', handleDrop, false);
                        card.addEventListener('dragend', handleDragEnd, false);
                        bindDeleteListeners(card);
                    });
                }

                // Add container drop zone listeners for uploading files/local images
                liveList.addEventListener('dragover', handleZoneDragOver, false);
                liveList.addEventListener('dragenter', handleZoneDragEnter, false);
                liveList.addEventListener('dragleave', handleZoneDragLeave, false);
                liveList.addEventListener('drop', handleZoneDrop, false);

                // Bind drag listeners to local raw & edited cards
                const localDragCards = item.querySelectorAll('.local-drag-card, .local-image-card, .raw-image-card');
                localDragCards.forEach(card => {
                    card.addEventListener('dragstart', handleDragStart, false);
                    card.addEventListener('dragend', handleDragEnd, false);
                });
            });
        }

        function handleCardClick(e, url) {
            if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'button') {
                return;
            }
            openLightbox(url);
        }

        function openLightbox(url) {
            document.getElementById('lightbox-img').src = url;
            document.getElementById('lightbox').classList.remove('hidden');
        }

        function closeLightbox() {
            document.getElementById('lightbox').classList.add('hidden');
        }

        // Boot
        async function init() {
            await checkServerStatus();
            initSidebar();
            renderProducts();
        }

        init();
    </script>
</body>
</html>
    """
    
    # Inject JSON representation of records
    serialized_data = json.dumps(product_records, ensure_ascii=False)
    html_content = html_content.replace("%PRODUCT_DATA%", serialized_data)
    
    with open(OUTPUT_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"🎉 Success! Generated full visual audit sheet at {OUTPUT_HTML_PATH}")

if __name__ == '__main__':
    run()
