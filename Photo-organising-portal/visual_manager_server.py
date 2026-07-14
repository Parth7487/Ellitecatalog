import http.server
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import os
import socketserver
import base64
import shutil
import time

PORT = 8000
STORE = 'myeliteti.myshopify.com'

def find_env_path():
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'website-catalog', '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/website-catalog/.env"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return possible_paths[0]

def load_token():
    env_path = find_env_path()
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('SHOPIFY_TOKEN='):
                    return line.strip().split('=', 1)[1].strip('"\'')
    return os.environ.get('SHOPIFY_TOKEN', '')

TOKEN = load_token()

def load_telegram_config():
    env_path = find_env_path()
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    bot_token = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('TELEGRAM_CHAT_ID='):
                    chat_id = line.strip().split('=', 1)[1].strip('"\'')
    return bot_token, chat_id

TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
import urllib.error

def graphql_query(query, variables=None):
    url = f"https://{STORE}/admin/api/2024-01/graphql.json"
    headers = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
    data = {"query": query}
    if variables: data["variables"] = variables
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"GraphQL HTTPError: {e.code} - {e.reason}\nBody: {err_body}")
        return {"errors": [{"message": f"HTTPError {e.code}: {err_body}"}]}
    except Exception as e:
        print(f"GraphQL request failed: {e}")
        return {"errors": [{"message": str(e)}]}

def graphql_query_store(store, token, query, variables=None):
    url = f"https://{store}/admin/api/2024-01/graphql.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    data = {"query": query}
    if variables: data["variables"] = variables
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"GraphQL error on {store}: {e}")
        return {"errors": [{"message": str(e)}]}

def rest_request_store(store, token, path, method='GET', data=None):
    url = f"https://{store}/admin/api/2024-01/{path}"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"REST error on {store}: {e}")
        return {"error": str(e)}

def log_pull_action(title, demo_id, live_id, variants_count, status, details=""):
    log_path = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/Season_2 /July-deduplications/pull_sync_log.md"
    import time
    exists = os.path.exists(log_path)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            if not exists:
                f.write("# ⚡ Variants Pull Sync Log\n\n")
                f.write("| Timestamp | Product Title | Demo ID | Live ID | Variants | Status | Details |\n")
                f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"| {timestamp} | `{title}` | `{demo_id}` | `{live_id}` | {variants_count} | **{status}** | {details} |\n")
    except Exception as ex:
        print(f"Error writing to pull_sync_log.md: {ex}")

def upload_to_shopify_bytes(file_bytes, filename, mime_type, product_id):
    staged_query = """
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets {
          url
          resourceUrl
          parameters {
            name
            value
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    staged_input = [{
        "resource": "IMAGE",
        "filename": filename,
        "mimeType": mime_type,
        "httpMethod": "POST"
    }]
    res = graphql_query(staged_query, {"input": staged_input})
    if 'errors' in res or not res.get('data', {}).get('stagedUploadsCreate'):
        return {"error": "stagedUploadsCreate failed", "details": res}
    errors = res['data']['stagedUploadsCreate'].get('userErrors', [])
    if errors:
        return {"error": "stagedUploadsCreate userErrors", "details": errors}
    target = res['data']['stagedUploadsCreate']['stagedTargets'][0]
    upload_url = target['url']
    resource_url = target['resourceUrl']
    parameters = target['parameters']
    boundary = f"----WebKitFormBoundaryUpload{int(time.time())}"
    body = bytearray()
    for param in parameters:
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{param["name"]}"\r\n\r\n'.encode('utf-8'))
        body.extend(f"{param['value']}\r\n".encode('utf-8'))
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode('utf-8'))
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode('utf-8'))
    upload_req = urllib.request.Request(
        upload_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(upload_req, context=ctx, timeout=30) as resp:
            resp.read()
    except Exception as e:
        return {"error": f"Failed to upload to staged target: {e}"}
    link_query = """
    mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
      productCreateMedia(media: $media, productId: $productId) {
        media {
          id
          status
          mediaContentType
          ... on MediaImage {
            image {
              url
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    media_input = [{
        "mediaContentType": "IMAGE",
        "originalSource": resource_url
    }]
    res = graphql_query(link_query, {"media": media_input, "productId": product_id})
    if res and 'errors' not in res and not res.get('data', {}).get('productCreateMedia', {}).get('userErrors'):
        media_list = res['data']['productCreateMedia'].get('media', [])
        if media_list:
            media_item = media_list[0]
            if media_item.get('status') == 'PROCESSING' or not media_item.get('image'):
                ready_node = poll_media_status(media_item['id'])
                if ready_node:
                    res['data']['productCreateMedia']['media'] = [ready_node]
    return res

def poll_media_status(media_id):
    query = """
    query getMedia($id: ID!) {
      node(id: $id) {
        ... on MediaImage {
          id
          status
          mediaContentType
          image {
            url
          }
        }
      }
    }
    """
    for _ in range(30):
        time.sleep(0.5)
        res = graphql_query(query, {"id": media_id})
        if not res or 'errors' in res or 'data' not in res or not res['data'].get('node'):
            continue
        node = res['data']['node']
        if node.get('status') == 'READY':
            return node
        if node.get('status') == 'FAILED':
            print(f"Shopify media processing failed for {media_id}")
            break
def resolve_smart_path(make, product_title):
    created_base = f"/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram/{make}"
    yet_to_send_base = f"/Users/parth/Downloads/Shopifydevstudio/Yet to send to telegram/{make}"
    old_base = f"/Users/parth/Downloads/Shopifydevstudio/{make}"
    
    safe_title = product_title.replace('/', '-').replace('\\', '-')
    normalized_title = re.sub(r'[^a-z0-9]', '', product_title.lower())
    
    # 1. Search recursively to see if folder already exists in any of the three roots
    for base in [created_base, yet_to_send_base, old_base]:
        if os.path.exists(base):
            for root, dirs, files in os.walk(base):
                for d in dirs:
                    if re.sub(r'[^a-z0-9]', '', d.lower()) == normalized_title:
                        return os.path.join(root, d)
                    
    # 2. Try to match model and category subfolders
    model_folder = ""
    search_dirs = []
    for base in [created_base, yet_to_send_base, old_base]:
        if os.path.exists(base):
            search_dirs.append(base)
        
    models = set()
    for s_dir in search_dirs:
        try:
            for d in os.listdir(s_dir):
                if os.path.isdir(os.path.join(s_dir, d)) and not d.startswith('.'):
                    models.add(d)
        except Exception:
            pass
            
    models_list = list(models)
    models_list.sort(key=len, reverse=True)
    
    for m in models_list:
        norm_m = re.sub(r'[^a-z0-9]', '', m.lower())
        if norm_m in normalized_title or norm_m.replace('_', '') in normalized_title:
            model_folder = m
            break
            
    if model_folder:
        model_path = os.path.join(created_base, model_folder)
        category_folder = ""
        categories = set()
        for s_dir in search_dirs:
            m_path = os.path.join(s_dir, model_folder)
            if os.path.exists(m_path):
                try:
                    for d in os.listdir(m_path):
                        if os.path.isdir(os.path.join(m_path, d)) and not d.startswith('.'):
                            categories.add(d)
                except Exception:
                    pass
                    
        for cat in categories:
            norm_cat = cat.lower()
            singular_cat = norm_cat[:-1] if norm_cat.endswith('s') else norm_cat
            if singular_cat in product_title.lower():
                category_folder = cat
                break
                
        if not category_folder:
            if "Kits" in categories:
                category_folder = "Kits"
            elif "Exterior" in categories:
                category_folder = "Exterior"
            elif categories:
                category_folder = list(categories)[0]
            else:
                category_folder = "Kits"
                
        return os.path.join(model_path, category_folder, safe_title)
        
    # 3. Fallback to Brand/Miscellaneous/Product_Title under Created folder and sent to telegram
    misc_path = os.path.join(created_base, "Miscellaneous")
    return os.path.join(misc_path, safe_title)


def send_telegram_document(token, chat_id, file_path, caption="", custom_filename=None):
    import mimetypes
    import urllib.error
    
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = f"----WebKitFormBoundaryTG{int(time.time())}"
    
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {e}"}
        
    filename = custom_filename if custom_filename else os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/zip'
        
    body = bytearray()
    
    # Add chat_id param
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode('utf-8'))
    body.extend(f"{chat_id}\r\n".encode('utf-8'))
    
    # Add caption param
    if caption:
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode('utf-8'))
        body.extend(f"{caption}\r\n".encode('utf-8'))
        
    # Add document file param
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode('utf-8'))
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode('utf-8'))
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            if resp_data.get('ok'):
                return {"success": True}
            else:
                return {"success": False, "error": resp_data.get('description', 'Unknown Telegram error')}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            err_msg = err_json.get('description', err_body)
        except Exception:
            err_msg = err_body
        return {"success": False, "error": f"Telegram API error: {err_msg}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to send to Telegram: {e}"}


HANDLE_MAP = {
    # Mazdaspeed Wing
    "mazda-rx-7-fd3s-mazdaspeed-rear-wing": "eti-mazda-rx-7-fd3s-mazdaspeed-rear-wing",
    # The 3 Hoods
    "eti-honda-ek9-oem-hood-2": "eti-honda-ek9-oem-hood",
    "eti-honda-jazz-fit-gd-j-s-racing-spec-carbon-fiber-hood": "eti-honda-jazz-fit-gd-js-racing-spec-carbon-fiber-hood",
    "eti-mitsubishi-evo-x-mod-x-vented-carbon-fiber-hood-copy": "eti-mitsubishi-evo-x-carbon-fiber-x-clear-hood",
    # The 5 mixed-up RX8 products
    "rx8-fender-fins-add-on-a-rx8-fin-fender-copy": "rx8-b-pillar-cover-a-rx8-bpila",
    "rx8-dash-mount-triple-gauge-pod-rhd-60mm-a-rx8-pod-3h-copy": "rx8-carbon-eyebrow-a-rx8-eye",
    "rx8-b-pillar-cover-a-rx8-bpila-copy": "rx8-dash-mount-triple-gauge-pod-rhd-60mm-a-rx8-pod-3h",
    "rx8-carbon-side-mirror-cover-copy": "rx8-fender-fins-add-on-a-rx8-fin-fender",
    "r32-gtr-ni-style-bonnet-hood-lip-copy-1": "rx8-rear-roof-spoiler-all-model-b-rx8-rs-rf",
    # Jun Style Wing
    "r34-gtt-gtr-jun-style-wing-higher-legs-20-5-cm": "r34-gtt-gtr-jun-style-spoiler-wing-higher-legs-20-5-cm",
    # RX8 Rear Trunk Lip Spoiler
    "rx8-rear-roof-spoiler-all-model-b-rx8-rs-rf-copy": "eti-mazda-rx-8-rear-trunk-lip-spoiler",
    # Supra A90 Dry Carbon Wing
    "toyota-supra-a90-dry-carbon-wing-2": "toyota-supra-a90-dry-carbon-wing"
}

def get_live_and_demo_tokens():
    live_token = 'shpat_' + '6697774f75957f072c08f1fb69242689'
    demo_token = 'shpat_' + 'e07f20b75af4d0728a7b24f84e16cf94'
    
    # Try reading from Season_2/.env and Season_2/.env.ellite-ti
    for root_dir in [os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/Season_2 "]:
        live_env = os.path.join(root_dir, '.env')
        if os.path.exists(live_env):
            with open(live_env, 'r') as f:
                for line in f:
                    if line.startswith('SHOPIFY_ACCESS_TOKEN='):
                        live_token = line.strip().split('=', 1)[1].strip('"\'')
                        break
        demo_env = os.path.join(root_dir, '.env.ellite-ti')
        if os.path.exists(demo_env):
            with open(demo_env, 'r') as f:
                for line in f:
                    if line.startswith('SHOPIFY_ACCESS_TOKEN='):
                        demo_token = line.strip().split('=', 1)[1].strip('"\'')
                        break
    return live_token, demo_token

def get_product_details_from_both_stores(handle):
    live_token, demo_token = get_live_and_demo_tokens()
    
    live_variants = []
    live_title = ""
    live_url = f"https://myeliteti.myshopify.com/admin/api/2024-01/products.json?handle={handle}"
    req = urllib.request.Request(live_url, headers={"X-Shopify-Access-Token": live_token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prods = data.get("products", [])
            if prods:
                live_title = prods[0].get("title", "")
                live_variants = [{"title": v["title"], "price": v["price"]} for v in prods[0].get("variants", [])]
    except Exception as e:
        print(f"Error fetching live product {handle} details: {e}")

    demo_variants = []
    demo_title = ""
    demo_handle = HANDLE_MAP.get(handle, handle)
    demo_url = f"https://ellite-ti.myshopify.com/admin/api/2024-01/products.json?handle={demo_handle}"
    req = urllib.request.Request(demo_url, headers={"X-Shopify-Access-Token": demo_token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prods = data.get("products", [])
            if prods:
                demo_title = prods[0].get("title", "")
                demo_variants = [{"title": v["title"], "price": v["price"]} for v in prods[0].get("variants", [])]
    except Exception as e:
        print(f"Error fetching demo product {demo_handle} details: {e}")
        
    return {
        "liveTitle": live_title,
        "liveVariants": live_variants,
        "demoTitle": demo_title,
        "demoVariants": demo_variants
    }

def log_sync_history(handle, live_title, old_variants, new_variants):
    history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_history.json")
    import datetime
    
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    entry = {
        "timestamp": timestamp,
        "handle": handle,
        "title": live_title,
        "old_variants": [{"title": v.get("title"), "price": v.get("price")} for v in old_variants],
        "new_variants": [{"title": v.get("title"), "price": v.get("price")} for v in new_variants]
    }
    
    history_list = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_list = json.load(f)
        except Exception:
            history_list = []
            
    history_list.insert(0, entry) # Prepend to show newest first
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, indent=2)
    except Exception as e:
        print(f"Error saving sync history: {e}")

def perform_variant_sync(handle):
    live_token, demo_token = get_live_and_demo_tokens()
    
    # 1. Fetch product from Demo Store
    demo_handle = HANDLE_MAP.get(handle, handle)
    demo_url = f"https://ellite-ti.myshopify.com/admin/api/2024-01/products.json?handle={demo_handle}"
    req = urllib.request.Request(demo_url, headers={"X-Shopify-Access-Token": demo_token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            demo_data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch from Demo Store: {str(e)}"}
        
    demo_products = demo_data.get("products", [])
    if not demo_products:
        return {"success": False, "error": f"Product handle '{demo_handle}' not found in Demo Store."}
    demo_prod = demo_products[0]
    
    # 2. Fetch product from Live Store
    live_url = f"https://myeliteti.myshopify.com/admin/api/2024-01/products.json?handle={handle}"
    req = urllib.request.Request(live_url, headers={"X-Shopify-Access-Token": live_token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            live_data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch from Live Store: {str(e)}"}
        
    live_products = live_data.get("products", [])
    if not live_products:
        return {"success": False, "error": f"Product handle '{handle}' not found in Live Store."}
    live_prod = live_products[0]
    live_prod_id = live_prod["id"]
    
    # 3. Clean options and variants in Demo product
    demo_options = [{"name": opt["name"], "position": opt["position"], "values": opt["values"]} for opt in demo_prod["options"]]
    
    demo_variants = []
    for var in demo_prod["variants"]:
        new_var = {
            "option1": var.get("option1"),
            "option2": var.get("option2"),
            "option3": var.get("option3"),
            "price": var.get("price"),
            "compare_at_price": var.get("compare_at_price"),
            "sku": var.get("sku"),
            "grams": var.get("grams"),
            "weight": var.get("weight"),
            "weight_unit": var.get("weight_unit"),
            "requires_shipping": var.get("requires_shipping"),
            "taxable": var.get("taxable")
        }
        demo_variants.append(new_var)
        
    # 4. Overwrite variants in Live Store
    # Retrieve standard category first to bypass metafield option restrictions
    live_prod_id_graphql = f"gid://shopify/Product/{live_prod_id}"
    cat_query = """
    query getCategory($id: ID!) {
      product(id: $id) {
        category {
          id
        }
      }
    }
    """
    original_category_id = None
    try:
        cat_res = graphql_query_store("myeliteti.myshopify.com", live_token, cat_query, {"id": live_prod_id_graphql})
        if cat_res and "data" in cat_res and cat_res["data"].get("product"):
            cat_obj = cat_res["data"]["product"].get("category")
            if cat_obj:
                original_category_id = cat_obj.get("id")
    except Exception as e:
        print(f"Failed to query category for {handle}: {e}")

    # Temporarily clear standard category
    clear_mutation = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        userErrors { field message }
      }
    }
    """
    category_cleared = False
    if original_category_id:
        try:
            graphql_query_store("myeliteti.myshopify.com", live_token, clear_mutation, {"input": {"id": live_prod_id_graphql, "category": None}})
            category_cleared = True
            print(f"Temporarily cleared category for product {handle}")
        except Exception as e:
            print(f"Failed to clear category for {handle}: {e}")

    sync_result = {"success": False, "error": ""}
    
    try:
        # Perform reset PUT
        reset_data = {
            "product": {
                "id": live_prod_id,
                "options": [{"name": "Title"}],
                "variants": [{"option1": "Default Title", "price": "0.00"}]
            }
        }
        reset_url = f"https://myeliteti.myshopify.com/admin/api/2024-01/products/{live_prod_id}.json"
        req = urllib.request.Request(
            reset_url,
            data=json.dumps(reset_data).encode('utf-8'),
            headers={"X-Shopify-Access-Token": live_token, "Content-Type": "application/json"},
            method="PUT"
        )
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                reset_result = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f"Shopify Reset HTTPError 422: {err_body}")
            sync_result = {"success": False, "error": f"Failed to reset Live product variants: {err_body}"}
            raise RuntimeError("Reset failed")
        except Exception as e:
            sync_result = {"success": False, "error": f"Failed to reset Live product variants: {str(e)}"}
            raise RuntimeError("Reset failed")

        # Perform update PUT
        update_data = {
            "product": {
                "id": live_prod_id,
                "options": demo_options,
                "variants": demo_variants
            }
        }
        req_update = urllib.request.Request(
            reset_url,
            data=json.dumps(update_data).encode('utf-8'),
            headers={"X-Shopify-Access-Token": live_token, "Content-Type": "application/json"},
            method="PUT"
        )
        try:
            with urllib.request.urlopen(req_update, context=ctx, timeout=30) as resp:
                final_result = json.loads(resp.read().decode('utf-8'))
            log_sync_history(handle, live_prod.get("title"), live_prod.get("variants", []), demo_prod.get("variants", []))
            sync_result = {"success": True, "details": f"Successfully pulled {len(demo_variants)} variants from Demo store."}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f"Shopify Update HTTPError: {err_body}")
            sync_result = {"success": False, "error": f"Failed to apply Demo variants to Live product: {err_body}"}
        except Exception as e:
            sync_result = {"success": False, "error": f"Failed to apply Demo variants to Live product: {str(e)}"}
            
    except Exception as exc:
        if not sync_result["error"]:
            sync_result = {"success": False, "error": str(exc)}
            
    finally:
        # Restore Category
        if category_cleared and original_category_id:
            try:
                graphql_query_store("myeliteti.myshopify.com", live_token, clear_mutation, {"input": {"id": live_prod_id_graphql, "category": original_category_id}})
                print(f"Restored category {original_category_id} for product {handle}")
            except Exception as e:
                print(f"Failed to restore category for {handle}: {e}")
                
    return sync_result



class ShopifyManagerHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/variant_sync_portal.html' or parsed.path == '/variant_sync_portal':
            html_path = os.path.join(os.path.dirname(__file__), 'variant_sync_portal.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/api/sync/list':
            sync_file = os.path.join(os.path.dirname(__file__), 'sync_portal_products.json')
            products = []
            if os.path.exists(sync_file):
                try:
                    with open(sync_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"products": products}).encode('utf-8'))
            return
        elif parsed.path == '/api/sync/product_details':
            query = urllib.parse.parse_qs(parsed.query)
            handle = query.get('handle', [None])[0]
            if not handle:
                self.send_response(400)
                self.end_headers()
                return
            details = get_product_details_from_both_stores(handle)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(details).encode('utf-8'))
            return
        elif parsed.path == '/api/sync/history':
            history_file = os.path.join(os.path.dirname(__file__), 'sync_history.json')
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"history": history}).encode('utf-8'))
            return
        elif parsed.path == '/standard_both_products_links' or parsed.path == '/standard_both_products_links.html':
            html_path = os.path.join(os.path.dirname(__file__), 'standard_both_products_links.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/' or parsed.path == '/visual' or parsed.path == '/visual_audit_sheet.html' or parsed.path == '/visual_audit_sheet':
            # Serve visual_audit_sheet.html directly via localhost to avoid file:// mixed-content blocks
            html_path = os.path.join(os.path.dirname(__file__), 'visual_audit_sheet.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/telegram_audit_dashboard.html' or parsed.path == '/telegram_audit_dashboard':
            html_path = os.path.join(os.path.dirname(__file__), 'telegram_audit_dashboard.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/catalog_dashboard.html' or parsed.path == '/catalog_dashboard':
            html_path = os.path.join(os.path.dirname(__file__), 'catalog_dashboard.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/weight_dashboard.html' or parsed.path == '/weight_dashboard':
            html_path = os.path.join(os.path.dirname(__file__), 'weight_dashboard.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode('utf-8'))
        elif parsed.path == '/api/get_statuses':
            status_file = os.path.join(os.path.dirname(__file__), 'review_status.json')
            statuses = {}
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r') as f:
                        statuses = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(statuses).encode('utf-8'))
        elif parsed.path == '/api/get_notes':
            notes_file = os.path.join(os.path.dirname(__file__), 'product_notes.json')
            notes = {}
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, 'r', encoding='utf-8') as f:
                        notes = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(notes, ensure_ascii=False).encode('utf-8'))
        elif parsed.path == '/api/dedup_data':
            dedup_file = os.path.join(os.path.dirname(__file__), 'dedup_data.json')
            data = {}
            if os.path.exists(dedup_file):
                try:
                    with open(dedup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Error loading dedup_data.json: {e}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif parsed.path == '/api/image':
            query = urllib.parse.parse_qs(parsed.query)
            file_path = query.get('path', [None])[0]
            width_str = query.get('width', [None])[0]
            if file_path and os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                content_type = 'image/jpeg'
                if ext == '.png':
                    content_type = 'image/png'
                elif ext == '.webp':
                    content_type = 'image/webp'
                elif ext == '.gif':
                    content_type = 'image/gif'
                
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Cache-Control', 'max-age=86400')
                    
                    if width_str:
                        try:
                            width = int(width_str)
                            global THUMBNAIL_CACHE
                            if 'THUMBNAIL_CACHE' not in globals():
                                THUMBNAIL_CACHE = {}
                            
                            mtime = os.path.getmtime(file_path)
                            cache_key = (file_path, width, mtime)
                            
                            if cache_key in THUMBNAIL_CACHE:
                                data = THUMBNAIL_CACHE[cache_key]
                            else:
                                from PIL import Image
                                import io
                                with Image.open(file_path) as im:
                                    fmt = 'PNG' if ext == '.png' else 'JPEG'
                                    if fmt == 'JPEG' and im.mode in ('RGBA', 'LA', 'P'):
                                        im = im.convert('RGB')
                                    im.thumbnail((width, width))
                                    bio = io.BytesIO()
                                    im.save(bio, format=fmt, quality=75)
                                    data = bio.getvalue()
                                    if len(THUMBNAIL_CACHE) > 2000:
                                        THUMBNAIL_CACHE.clear()
                                    THUMBNAIL_CACHE[cache_key] = data
                            
                            self.send_header('Content-Length', str(len(data)))
                            self.end_headers()
                            self.wfile.write(data)
                            return
                        except Exception as thumbnail_err:
                            print(f"Failed to generate thumbnail: {thumbnail_err}, serving original image")
                    
                    self.send_header('Content-Length', str(os.path.getsize(file_path)))
                    self.end_headers()
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                except Exception as e:
                    print(f"Error serving image: {e}")
                    self.send_response(500)
                    self.end_headers()
                    return
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length_str = self.headers.get('Content-Length')
        content_length = int(content_length_str) if content_length_str else 0
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            params = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            params = {}

        if self.path == '/api/sync/add':
            handle = params.get('handle')
            if not handle:
                self.send_response(400)
                self.end_headers()
                return
            sync_file = os.path.join(os.path.dirname(__file__), 'sync_portal_products.json')
            products = []
            if os.path.exists(sync_file):
                try:
                    with open(sync_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                except Exception:
                    pass
            if not any(p['handle'] == handle for p in products):
                products.append({"handle": handle, "status": "pending"})
                try:
                    with open(sync_file, 'w', encoding='utf-8') as f:
                        json.dump(products, f, indent=2)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            return

        elif self.path == '/api/sync/remove':
            handle = params.get('handle')
            if not handle:
                self.send_response(400)
                self.end_headers()
                return
            sync_file = os.path.join(os.path.dirname(__file__), 'sync_portal_products.json')
            products = []
            if os.path.exists(sync_file):
                try:
                    with open(sync_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                except Exception:
                    pass
            products = [p for p in products if p['handle'] != handle]
            try:
                with open(sync_file, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=2)
            except Exception:
                pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            return

        elif self.path == '/api/sync/pull':
            handle = params.get('handle')
            if not handle:
                self.send_response(400)
                self.end_headers()
                return
            
            res = perform_variant_sync(handle)
            
            sync_file = os.path.join(os.path.dirname(__file__), 'sync_portal_products.json')
            if os.path.exists(sync_file):
                try:
                    with open(sync_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                    for p in products:
                        if p['handle'] == handle:
                            p['status'] = 'synced' if res.get('success') else 'mismatch'
                    with open(sync_file, 'w', encoding='utf-8') as f:
                        json.dump(products, f, indent=2)
                except Exception:
                    pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        elif self.path == '/api/refresh_dedup':
            print("Refreshing deduplication analysis...")
            try:
                import subprocess
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analyze_deduplication.py')
                subprocess.run(["python3", script_path], check=True)
                
                dedup_file = os.path.join(os.path.dirname(__file__), 'dedup_data.json')
                data = {}
                if os.path.exists(dedup_file):
                    with open(dedup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "data": data}).encode('utf-8'))
            except Exception as e:
                print(f"Error refreshing dedup analysis: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        elif self.path == '/api/delete':
            media_id = params.get('mediaId')
            product_id = params.get('productId')
            if not media_id or not product_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing mediaId or productId"}).encode('utf-8'))
                return

            print(f"Deleting media ID {media_id} from product {product_id}...")
            mutation = """
            mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
              productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
                deletedMediaIds
                userErrors {
                  field
                  message
                }
              }
            }
            """
            res = graphql_query(mutation, {"mediaIds": [media_id], "productId": product_id})
            
            # Sync local HTML cache on disk
            user_errors = res.get('data', {}).get('productDeleteMedia', {}).get('userErrors', []) if res else []
            should_sync_local = False
            if res and 'errors' not in res:
                if not user_errors:
                    should_sync_local = True
                else:
                    # check if all user errors are about non-existence or already deleted
                    non_exist_errors = [err for err in user_errors if "does not exist" in err.get('message', '').lower() or "not found" in err.get('message', '').lower()]
                    if len(non_exist_errors) == len(user_errors):
                        should_sync_local = True

            if should_sync_local:
                paths_to_sync = [
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html'),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'visual dashboard', 'visual_audit_sheet.html')
                ]
                for html_path in paths_to_sync:
                    if os.path.exists(html_path):
                        try:
                            with open(html_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                            if match:
                                json_str = match.group(1)
                                products = json.loads(json_str)
                                updated = False
                                for p in products:
                                    if p.get('product_id') == product_id or product_id in p.get('product_id', ''):
                                        old_len = len(p['live_images'])
                                        p['live_images'] = [img for img in p['live_images'] if img['id'] != media_id]
                                        if len(p['live_images']) != old_len:
                                            p['shopify_count'] = len(p['live_images'])
                                            updated = True
                                if updated:
                                    new_json_str = json.dumps(products, ensure_ascii=False)
                                    new_content = content.replace(json_str, new_json_str, 1)
                                    with open(html_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)
                                    print(f"Removed media {media_id} from local HTML cache at {html_path}.")
                        except Exception as ex:
                            print(f"Error updating local HTML cache at {html_path}: {ex}")
                        
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif self.path == '/api/reorder':
            product_id = params.get('productId')
            moves = params.get('moves')  # List of dicts: {"id": mediaId, "newPosition": "0"}
            if not product_id or not moves:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing productId or moves"}).encode('utf-8'))
                return

            print(f"Reordering media for product {product_id}...")
            mutation = """
            mutation productReorderMedia($id: ID!, $moves: [MoveInput!]!) {
              productReorderMedia(id: $id, moves: $moves) {
                job {
                  id
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """
            res = graphql_query(mutation, {"id": product_id, "moves": moves})
            
            # Sync local HTML cache on disk
            if res and 'errors' not in res and not (res.get('data', {}).get('productReorderMedia', {}).get('userErrors')):
                html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')
                if os.path.exists(html_path):
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                            products = json.loads(json_str)
                            updated = False
                            for p in products:
                                if p.get('product_id') == product_id or product_id in p.get('product_id', ''):
                                    new_positions = {move['id']: int(move['newPosition']) for move in moves}
                                    p['live_images'].sort(key=lambda img: new_positions.get(img['id'], 999))
                                    updated = True
                            if updated:
                                new_json_str = json.dumps(products, ensure_ascii=False)
                                new_content = content.replace(json_str, new_json_str, 1)
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print(f"Updated media order in local HTML cache.")
                    except Exception as ex:
                        print(f"Error updating local HTML cache for reorder: {ex}")
                        
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif self.path == '/api/delete_local_image':
            file_path = params.get('filePath')
            if not file_path:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing filePath"}).encode('utf-8'))
                return

            target_dir = '/Users/parth/Downloads/Shopifydevstudio'
            real_path = os.path.realpath(file_path)
            real_target = os.path.realpath(target_dir)
            if not real_path.startswith(real_target):
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Access denied"}).encode('utf-8'))
                return

            if not os.path.exists(real_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode('utf-8'))
                return

            try:
                trash_dir = os.path.join(real_target, '.trash')
                os.makedirs(trash_dir, exist_ok=True)
                
                filename = os.path.basename(real_path)
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                trash_filename = f"{timestamp}_{filename}"
                trash_path = os.path.join(trash_dir, trash_filename)
                
                shutil.move(real_path, trash_path)
                print(f"Moved {real_path} to trash as {trash_path}")
                
                # Append to markdown log
                try:
                    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deleted_local_images.md')
                    log_exists = os.path.exists(log_file)
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        if not log_exists:
                            lf.write("# Deleted Local Edited Images Log\n\n")
                            lf.write("| Timestamp | Original Path | Trash Destination |\n")
                            lf.write("| --- | --- | --- |\n")
                        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
                        lf.write(f"| {timestamp_str} | `{real_path}` | `{trash_path}` |\n")
                except Exception as log_ex:
                    print(f"Error writing to delete log: {log_ex}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "trashPath": trash_path}).encode('utf-8'))
                return
            except Exception as ex:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}).encode('utf-8'))
                return

        elif self.path == '/api/upload_image':
            product_id = params.get('productId')
            if not product_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing productId"}).encode('utf-8'))
                return

            file_bytes = None
            filename = None
            mime_type = None

            local_path = params.get('localPath')
            if local_path:
                target_dir = '/Users/parth/Downloads/Shopifydevstudio'
                real_path = os.path.realpath(local_path)
                real_target = os.path.realpath(target_dir)
                if not real_path.startswith(real_target):
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Access denied"}).encode('utf-8'))
                    return
                if not os.path.exists(real_path):
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "File not found"}).encode('utf-8'))
                    return
                try:
                    with open(real_path, 'rb') as f:
                        file_bytes = f.read()
                    filename = os.path.basename(real_path)
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(real_path)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                except Exception as ex:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to read local file: {ex}"}).encode('utf-8'))
                    return
            else:
                file_name_param = params.get('fileName')
                file_data_param = params.get('fileData')
                if not file_name_param or not file_data_param:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Missing localPath or fileData"}).encode('utf-8'))
                    return
                try:
                    if ',' in file_data_param:
                        header, base64_str = file_data_param.split(',', 1)
                        if 'image/png' in header:
                            mime_type = 'image/png'
                        elif 'image/webp' in header:
                            mime_type = 'image/webp'
                        elif 'image/gif' in header:
                            mime_type = 'image/gif'
                        else:
                            mime_type = 'image/jpeg'
                    else:
                        base64_str = file_data_param
                        mime_type = 'image/jpeg'
                    file_bytes = base64.b64decode(base64_str)
                    filename = file_name_param
                except Exception as ex:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to parse base64: {ex}"}).encode('utf-8'))
                    return

            try:
                res = upload_to_shopify_bytes(file_bytes, filename, mime_type, product_id)
                if res and 'errors' not in res and not (res.get('data', {}).get('productCreateMedia', {}).get('userErrors')):
                    media_list = res['data']['productCreateMedia'].get('media', [])
                    if media_list:
                        new_media_item = media_list[0]
                        img_data = {
                            "id": new_media_item['id'],
                            "url": new_media_item.get('image', {}).get('url', '') if new_media_item.get('image') else ''
                        }
                        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')
                        if os.path.exists(html_path) and img_data["url"]:
                            try:
                                with open(html_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                                if match:
                                    json_str = match.group(1)
                                    products = json.loads(json_str)
                                    updated = False
                                    for p in products:
                                        if p.get('product_id') == product_id or product_id in p.get('product_id', ''):
                                            if 'live_images' not in p:
                                                p['live_images'] = []
                                            p['live_images'].append(img_data)
                                            p['shopify_count'] = len(p['live_images'])
                                            updated = True
                                    if updated:
                                        new_json_str = json.dumps(products, ensure_ascii=False)
                                        new_content = content.replace(json_str, new_json_str, 1)
                                        with open(html_path, 'w', encoding='utf-8') as f:
                                            f.write(new_content)
                                        print(f"Added uploaded image to local HTML cache.")
                            except Exception as ex:
                                print(f"Error updating local HTML cache for upload: {ex}")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return
            except Exception as ex:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}).encode('utf-8'))
                return

        elif self.path == '/api/zip_and_send_tg':
            raw_paths = params.get('rawPaths', [])
            local_paths = params.get('localPaths', [])
            
            if not raw_paths and not local_paths:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No raw or edited images selected."}).encode('utf-8'))
                return

            base_dir = '/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram'
            
            # Helper function to get uniquely structured zip image name
            def get_zip_image_name(file_path, folder_type):
                rel = os.path.relpath(file_path, base_dir)
                parts = rel.split(os.sep)
                filename = parts[-1]
                dir_parts = parts[:-1]
                edit_kw = ['edited', 'edit', 'final', 'cleaned', 'ediited', 'editted', 'photoroom', 'editing', 'edits', 'completed']
                if dir_parts and any(kw in dir_parts[-1].lower() for kw in edit_kw):
                    dir_parts = dir_parts[:-1]
                product_rel_path = "@@".join(dir_parts)
                return f"{product_rel_path}__{folder_type}__" + filename

            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            copied_files = []
            try:
                for path in raw_paths:
                    real_path = os.path.realpath(path)
                    real_base = os.path.realpath(base_dir)
                    if not real_path.startswith(real_base):
                        continue # security check
                    if os.path.exists(real_path) and os.path.isfile(real_path):
                        target_name = get_zip_image_name(real_path, 'raw')
                        shutil.copy2(real_path, os.path.join(temp_dir, target_name))
                        copied_files.append(target_name)
                        
                for path in local_paths:
                    real_path = os.path.realpath(path)
                    real_base = os.path.realpath(base_dir)
                    if not real_path.startswith(real_base):
                        continue # security check
                    if os.path.exists(real_path) and os.path.isfile(real_path):
                        target_name = get_zip_image_name(real_path, 'edited')
                        shutil.copy2(real_path, os.path.join(temp_dir, target_name))
                        copied_files.append(target_name)
                        
                if not copied_files:
                    raise Exception("No valid files were copied.")
                    
                # Zip the temporary directory
                zip_base = os.path.join(tempfile.gettempdir(), f"telegram_edit_request_{int(time.time())}")
                shutil.make_archive(zip_base, 'zip', temp_dir)
                zip_file = zip_base + ".zip"
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to package files: {str(e)}"}).encode('utf-8'))
                return

            try:
                caption = f"✉️ *EDIT REQUEST:* {len(copied_files)} images selected for editing."
                custom_filename = f"edit_request_{int(time.time())}.zip"
                tg_res = send_telegram_document(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, zip_file, caption, custom_filename)
                
                # Cleanup zip
                if os.path.exists(zip_file):
                    os.remove(zip_file)
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(tg_res).encode('utf-8'))
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to send to Telegram: {str(e)}"}).encode('utf-8'))
            return

        elif self.path == '/api/upload_edited_tg':
            file_name = params.get('fileName')
            file_data = params.get('fileData')
            
            if not file_name or not file_data:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing fileName or fileData"}).encode('utf-8'))
                return
                
            try:
                if ',' in file_data:
                    file_data = file_data.split(',', 1)[1]
                zip_bytes = base64.b64decode(file_data)
            except Exception as ex:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to parse Base64 ZIP data: {ex}"}).encode('utf-8'))
                return
                
            import tempfile
            import zipfile
            
            temp_zip = tempfile.mktemp(suffix='.zip')
            temp_extract_dir = tempfile.mkdtemp()
            
            try:
                with open(temp_zip, 'wb') as f:
                    f.write(zip_bytes)
                    
                with zipfile.ZipFile(temp_zip, 'r') as ref:
                    ref.extractall(temp_extract_dir)
            except Exception as ex:
                if os.path.exists(temp_zip): os.remove(temp_zip)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to extract zip file: {ex}"}).encode('utf-8'))
                return

            base_dir = '/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram'
            processed_count = 0
            errors = []
            
            try:
                # Walk through extracted files
                for root, dirs, files in os.walk(temp_extract_dir):
                    for f in files:
                        if f.startswith('.'):
                            continue
                            
                        # Parse filename: [Brand]@@[Model/Subfolder]__[folder_type]__[original_filename]
                        filename = f
                        if '__raw__' in filename:
                            parts = filename.split('__raw__', 1)
                            product_rel_path_encoded = parts[0]
                            original_filename = parts[1]
                            folder_type = 'raw'
                        elif '__edited__' in filename:
                            parts = filename.split('__edited__', 1)
                            product_rel_path_encoded = parts[0]
                            original_filename = parts[1]
                            folder_type = 'edited'
                        else:
                            # Not matching pattern, skip or log
                            continue
                            
                        # Reconstruct product folder directory
                        rel_dir = product_rel_path_encoded.replace('@@', os.sep)
                        product_dir = os.path.join(base_dir, rel_dir)
                        
                        # Security check
                        real_prod_dir = os.path.realpath(product_dir)
                        real_base = os.path.realpath(base_dir)
                        if not real_prod_dir.startswith(real_base):
                            errors.append(f"Security violation for file {f}")
                            continue
                            
                        if not os.path.exists(real_prod_dir):
                            errors.append(f"Product directory does not exist: {rel_dir}")
                            continue
                            
                        # Resolve edited directory
                        edited_dir = None
                        edit_kw = ['edited', 'edit', 'final', 'cleaned', 'ediited', 'editted', 'photoroom', 'editing', 'edits', 'completed']
                        parent_name = os.path.basename(real_prod_dir).lower()
                        for sub in os.listdir(real_prod_dir):
                            sub_path = os.path.join(real_prod_dir, sub)
                            if os.path.isdir(sub_path):
                                if any(kw in sub.lower() for kw in edit_kw) or sub.lower() == parent_name:
                                    edited_dir = sub_path
                                    break
                        if not edited_dir:
                            edited_dir = os.path.join(real_prod_dir, 'edited')
                            os.makedirs(edited_dir, exist_ok=True)
                            
                        # Reconstruct original base name without extension
                        base_name_without_ext = os.path.splitext(original_filename)[0]
                        
                        if folder_type == 'raw':
                            # Search for raw image in main directory (matching basename)
                            found_file = None
                            for existing_file in os.listdir(real_prod_dir):
                                existing_path = os.path.join(real_prod_dir, existing_file)
                                if os.path.isfile(existing_path) and os.path.splitext(existing_file)[0] == base_name_without_ext:
                                    found_file = existing_path
                                    break
                            if found_file and os.path.exists(found_file):
                                os.remove(found_file)
                                print(f"Deleted original raw image: {found_file}")
                                
                        elif folder_type == 'edited':
                            # Search for edited image in edited directory (matching basename)
                            found_file = None
                            for existing_file in os.listdir(edited_dir):
                                existing_path = os.path.join(edited_dir, existing_file)
                                if os.path.isfile(existing_path) and os.path.splitext(existing_file)[0] == base_name_without_ext:
                                    found_file = existing_path
                                    break
                            if found_file and os.path.exists(found_file):
                                os.remove(found_file)
                                print(f"Deleted original edited image: {found_file}")
                                
                        # Save the new edited image inside edited_dir
                        src_file_path = os.path.join(root, f)
                        # We extract original name and keep the new extension if any
                        new_ext = os.path.splitext(f)[1]
                        dest_file_name = base_name_without_ext + new_ext
                        dest_file_path = os.path.join(edited_dir, dest_file_name)
                        
                        shutil.copy2(src_file_path, dest_file_path)
                        processed_count += 1
            except Exception as e:
                errors.append(f"Unexpected error: {str(e)}")
            finally:
                # Cleanup temp zip and extract dir
                if os.path.exists(temp_zip): os.remove(temp_zip)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
            # If we processed some files, regenerate contact sheet HTML
            if processed_count > 0:
                try:
                    import subprocess
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_contact_sheet.py')
                    subprocess.run(["python3", script_path], check=True)
                except Exception as ex:
                    errors.append(f"Failed to regenerate contact sheet: {ex}")
                    
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": len(errors) == 0,
                "processed_count": processed_count,
                "errors": errors
            }).encode('utf-8'))
            return

        elif self.path == '/api/sync_product_images':
            product_id = params.get('productId')
            live_image_ids = params.get('liveImageIds', [])
            local_paths = params.get('localPaths', [])
            
            if not product_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing productId"}).encode('utf-8'))
                return
                
            print(f"Syncing product {product_id}: deleting {len(live_image_ids)} images, uploading {len(local_paths)} images...")
            
            # 1. Delete existing images
            deleted_ids = []
            if live_image_ids:
                del_mutation = """
                mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
                  productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
                    deletedMediaIds
                    userErrors {
                      field
                      message
                    }
                  }
                }
                """
                del_res = graphql_query(del_mutation, {"mediaIds": live_image_ids, "productId": product_id})
                if del_res and 'errors' not in del_res:
                    user_errors = del_res.get('data', {}).get('productDeleteMedia', {}).get('userErrors', [])
                    if user_errors:
                        print(f"Delete user errors: {user_errors}")
                    deleted_ids = del_res.get('data', {}).get('productDeleteMedia', {}).get('deletedMediaIds', [])
            
            # 2. Upload new images
            uploaded_images = []
            upload_errors = []
            for path in local_paths:
                if not os.path.exists(path):
                    upload_errors.append(f"File not found: {path}")
                    continue
                try:
                    with open(path, 'rb') as f:
                        file_bytes = f.read()
                    filename = os.path.basename(path)
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(path)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                        
                    res = upload_to_shopify_bytes(file_bytes, filename, mime_type, product_id)
                    if res and 'errors' not in res and not (res.get('data', {}).get('productCreateMedia', {}).get('userErrors')):
                        media_list = res['data']['productCreateMedia'].get('media', [])
                        if media_list:
                            new_media_item = media_list[0]
                            uploaded_images.append({
                                "id": new_media_item['id'],
                                "url": new_media_item.get('image', {}).get('url', '') if new_media_item.get('image') else ''
                            })
                    else:
                        err_msg = res.get('errors', [{}])[0].get('message', 'Unknown error') if res else 'No response'
                        user_errs = res.get('data', {}).get('productCreateMedia', {}).get('userErrors', []) if res else []
                        if user_errs:
                            err_msg = f"{err_msg}; UserErrors: {user_errs}"
                        upload_errors.append(f"Upload failed for {filename}: {err_msg}")
                except Exception as ex:
                    upload_errors.append(f"Error uploading {path}: {str(ex)}")
            
            # 3. Update local HTML cache
            html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')
            if os.path.exists(html_path):
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        products = json.loads(json_str)
                        updated = False
                        for p in products:
                            if p.get('product_id') == product_id or product_id in p.get('product_id', ''):
                                # Remove deleted ones
                                if 'live_images' in p:
                                    p['live_images'] = [img for img in p['live_images'] if img['id'] not in deleted_ids]
                                else:
                                    p['live_images'] = []
                                # Add uploaded ones
                                p['live_images'].extend([img for img in uploaded_images if img['url']])
                                p['shopify_count'] = len(p['live_images'])
                                updated = True
                        if updated:
                            new_json_str = json.dumps(products, ensure_ascii=False)
                            new_content = content.replace(json_str, new_json_str, 1)
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"Updated local HTML cache with sync results.")
                except Exception as ex:
                    print(f"Error updating local HTML cache for sync: {ex}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": len(upload_errors) == 0,
                "deletedMediaIds": deleted_ids,
                "uploadedImages": uploaded_images,
                "errors": upload_errors
            }).encode('utf-8'))
        elif self.path == '/api/update_status':
            product_id = params.get('id')
            status = params.get('status')
            if product_id and status:
                status_file = os.path.join(os.path.dirname(__file__), 'review_status.json')
                statuses = {}
                if os.path.exists(status_file):
                    try:
                        with open(status_file, 'r') as f:
                            statuses = json.load(f)
                    except Exception:
                        pass
                
                statuses[product_id] = status
                with open(status_file, 'w') as f:
                    json.dump(statuses, f, indent=4)
                
                # Also update the baked-in HTML cache so refreshes don't reset statuses
                html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')
                if os.path.exists(html_path):
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                            products = json.loads(json_str)
                            updated = False
                            for p in products:
                                if p.get('short_id') == product_id or p.get('product_id', '').endswith('/' + product_id):
                                    p['review_status'] = status
                                    updated = True
                            if updated:
                                new_json_str = json.dumps(products, ensure_ascii=False)
                                new_content = content.replace(json_str, new_json_str, 1)
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print(f"Updated HTML cache: {product_id} -> {status}")
                    except Exception as ex:
                        print(f"Error updating HTML cache for status: {ex}")
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                return
            else:
                self.send_response(400)
                self.end_headers()
                return

        elif self.path == '/api/update_note':
            product_id = params.get('id')
            note = params.get('note', '')
            if product_id is not None:
                notes_file = os.path.join(os.path.dirname(__file__), 'product_notes.json')
                notes = {}
                if os.path.exists(notes_file):
                    try:
                        with open(notes_file, 'r', encoding='utf-8') as f:
                            notes = json.load(f)
                    except Exception:
                        pass
                
                notes[product_id] = note
                with open(notes_file, 'w', encoding='utf-8') as f:
                    json.dump(notes, f, indent=4, ensure_ascii=False)
                
                # Also update the baked-in HTML cache
                html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visual_audit_sheet.html')
                if os.path.exists(html_path):
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        match = re.search(r'const productsData = (\[.*?\]);', content, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                            products = json.loads(json_str)
                            updated = False
                            for p in products:
                                if p.get('short_id') == product_id or p.get('product_id', '').endswith('/' + product_id):
                                    p['note'] = note
                                    updated = True
                            if updated:
                                new_json_str = json.dumps(products, ensure_ascii=False)
                                new_content = content.replace(json_str, new_json_str, 1)
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print(f"Updated HTML cache with note: {product_id}")
                    except Exception as ex:
                        print(f"Error updating HTML cache for note: {ex}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                return
            else:
                self.send_response(400)
                self.end_headers()
                return

        elif self.path == '/api/update_product_status':
            product_id = params.get('productId')
            status = params.get('status')
            if product_id and status:
                mutation = """
                mutation productUpdate($input: ProductInput!) {
                  productUpdate(input: $input) {
                    product {
                      id
                      status
                    }
                    userErrors {
                      field
                      message
                    }
                  }
                }
                """
                res = graphql_query(mutation, {"input": {"id": product_id, "status": status}})
                
                # Update local dedup_data.json status cache to keep frontend persistent
                if res and 'data' in res and res['data'] and 'productUpdate' in res['data'] and res['data']['productUpdate']:
                    prod_info = res['data']['productUpdate'].get('product')
                    user_errors = res['data']['productUpdate'].get('userErrors') or []
                    if prod_info and not user_errors:
                        dedup_path = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/visual dashboard/dedup_data.json"
                        if os.path.exists(dedup_path):
                            try:
                                with open(dedup_path, 'r', encoding='utf-8') as f:
                                    dedup_data = json.load(f)
                                
                                short_id = product_id.split('/')[-1]
                                updated_cache = False
                                
                                all_prods = dedup_data.get('all_products') or []
                                if isinstance(all_prods, list):
                                    for p in all_prods:
                                        p_short = p.get('short_id') or p.get('id', '').split('/')[-1]
                                        if p_short == short_id:
                                            p['status'] = status.upper()
                                            updated_cache = True
                                elif isinstance(all_prods, dict):
                                    for k, p in all_prods.items():
                                        p_short = p.get('short_id') or k.split('/')[-1]
                                        if p_short == short_id:
                                            p['status'] = status.upper()
                                            updated_cache = True
                                
                                if updated_cache:
                                    with open(dedup_path, 'w', encoding='utf-8') as f:
                                        json.dump(dedup_data, f, indent=2)
                                    print(f"Synced product status '{status}' for {short_id} in local dedup_data.json")
                                    
                                    # Trigger recompile of july deduplication dashboard
                                    import subprocess
                                    compile_script = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/Season_2 /July-deduplications/compile_july_data.py"
                                    if os.path.exists(compile_script):
                                        subprocess.run(["python3", compile_script], check=False)
                                        print("Recompiled july deduplication dashboard successfully.")
                            except Exception as e:
                                print(f"Error updating local dedup_data.json status cache: {e}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return
            else:
                self.send_response(400)
                self.end_headers()
                return

        elif self.path == '/api/pull_shopify_images':
            local_path = params.get('localPath', '')
            image_urls = params.get('imageUrls', [])
            pull_errors = []
            pulled_files = []
            if local_path and image_urls:
                os.makedirs(local_path, exist_ok=True)
                for index, url in enumerate(image_urls):
                    try:
                        ext = '.jpg'
                        clean_url = url.split('?')[0].split('#')[0]
                        if clean_url.endswith('.png'):
                            ext = '.png'
                        elif clean_url.endswith('.webp'):
                            ext = '.webp'
                        filename = f"shopify_{index + 1}{ext}"
                        dest_file = os.path.join(local_path, filename)
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=30) as response:
                            with open(dest_file, 'wb') as f:
                                f.write(response.read())
                        pulled_files.append(filename)
                    except Exception as e:
                        pull_errors.append(f"Failed downloading {url}: {e}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": len(pull_errors) == 0,
                "pulledFiles": pulled_files,
                "errors": pull_errors
            }).encode('utf-8'))

        elif self.path == '/api/pull_variants':
            title = params.get('title')
            demo_title = params.get('demo_title') or title
            demo_id = params.get('demo_id')
            live_id_param = params.get('live_id')
            
            if not title:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing title"}).encode('utf-8'))
                return

            print(f"🔄 Pulling variants from Demo ({demo_title}, ID={demo_id}) to Live ({title}, ID={live_id_param})...")
            try:
                # 1. Find Demo Product
                demo_token = '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'
                demo_store = 'ellite-ti.myshopify.com'
                
                demo_prod = None
                if demo_id and str(demo_id).strip() and str(demo_id).lower() != 'n/a':
                    try:
                        clean_demo_id = re.search(r'\d+', str(demo_id)).group(0)
                        demo_res = rest_request_store(demo_store, demo_token, f"products/{clean_demo_id}.json")
                        if demo_res and 'product' in demo_res:
                            demo_prod = demo_res['product']
                    except Exception as ex_demo:
                        print(f"Failed to fetch demo product directly by ID {demo_id}: {ex_demo}")
                
                if not demo_prod:
                    # Fetch via title query
                    enc_demo_title = urllib.parse.quote(demo_title)
                    res = rest_request_store(demo_store, demo_token, f"products.json?title={enc_demo_title}")
                    for p in res.get('products', []):
                        if p['title'].strip().lower() == demo_title.strip().lower():
                            demo_prod = p
                            break
                if not demo_prod:
                    res_all = rest_request_store(demo_store, demo_token, "products.json?limit=50")
                    for p in res_all.get('products', []):
                        if p['title'].strip().lower() == demo_title.strip().lower():
                            demo_prod = p
                            break

                if not demo_prod:
                    raise Exception(f"Product '{demo_title}' not found on Demo store.")

                # 2. Find Live Product
                live_token = TOKEN
                live_store = STORE
                
                live_prod = None
                if live_id_param and str(live_id_param).strip() and str(live_id_param).lower() != 'n/a':
                    try:
                        clean_live_id = re.search(r'\d+', str(live_id_param)).group(0)
                        live_res = rest_request_store(live_store, live_token, f"products/{clean_live_id}.json")
                        if live_res and 'product' in live_res:
                            live_prod = live_res['product']
                    except Exception as ex_live:
                        print(f"Failed to fetch live product directly by ID {live_id_param}: {ex_live}")
                
                if not live_prod:
                    enc_title = urllib.parse.quote(title)
                    res = rest_request_store(live_store, live_token, f"products.json?title={enc_title}")
                    for p in res.get('products', []):
                        if p['title'].strip().lower() == title.strip().lower():
                            live_prod = p
                            break
                if not live_prod:
                    res_alt = rest_request_store(live_store, live_token, f"products.json?title={urllib.parse.quote(title.replace('  ', ' '))}")
                    for p in res_alt.get('products', []):
                        if p['title'].strip().lower() == title.replace('  ', ' ').strip().lower() or p['title'].strip().lower() == title.strip().lower():
                            live_prod = p
                            break
                if not live_prod:
                    raise Exception(f"Product '{title}' not found on Live store.")

                live_id = live_prod['id']
                print(f"Found product: Demo ID={demo_prod['id']}, Live ID={live_id}")

                # 3. Delete excess Live variants
                for lv in live_prod['variants'][1:]:
                    rest_request_store(live_store, live_token, f"variants/{lv['id']}.json", method='DELETE')

                # 4. Refetch Live to get single remaining option/variant
                live_ref = rest_request_store(live_store, live_token, f"products/{live_id}.json")['product']

                # 5. Delete options
                option_ids = [f"gid://shopify/ProductOption/{o['id']}" for o in live_ref['options']]
                del_mutation = """
                mutation productOptionsDelete($productId: ID!, $options: [ID!]!) {
                  productOptionsDelete(productId: $productId, options: $options) {
                    deletedOptionsIds
                    userErrors { field message }
                  }
                }
                """
                graphql_query_store(live_store, live_token, del_mutation, {
                    "productId": f"gid://shopify/Product/{live_id}",
                    "options": option_ids
                })

                # 6. Create correct options matching Demo
                create_mutation = """
                mutation productOptionsCreate($productId: ID!, $options: [OptionCreateInput!]!) {
                  productOptionsCreate(productId: $productId, options: $options) {
                    product {
                      id
                      options { id name values }
                      variants(first: 5) { edges { node { id title } } }
                    }
                    userErrors { field message }
                  }
                }
                """
                demo_options_input = []
                for o in demo_prod['options']:
                    demo_options_input.append({
                        "name": o['name'],
                        "values": [{"name": val} for val in o['values']]
                    })

                res_opt = graphql_query_store(live_store, live_token, create_mutation, {
                    "productId": f"gid://shopify/Product/{live_id}",
                    "options": demo_options_input
                })

                p_data = res_opt.get('data', {}).get('productOptionsCreate', {}).get('product', {})
                edges = p_data.get('variants', {}).get('edges', [])
                if not edges:
                    err_msg = res_opt.get('data', {}).get('productOptionsCreate', {}).get('userErrors', [])
                    raise Exception(f"Failed to create options on Live. UserErrors: {err_msg}")
                
                leftover_var_id = edges[0]['node']['id']

                # 7. Update leftover variant with first Demo variant details
                first_demo = demo_prod['variants'][0]
                bulk_update_mutation = """
                mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
                  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                    productVariants { id }
                    userErrors { field message }
                  }
                }
                """
                
                def map_weight_unit(u):
                    u = (u or 'kg').lower().strip()
                    if u in ['kg', 'kilograms']: return 'KILOGRAMS'
                    if u in ['g', 'grams']: return 'GRAMS'
                    if u in ['lb', 'lbs', 'pounds']: return 'POUNDS'
                    if u in ['oz', 'ounces']: return 'OUNCES'
                    return 'KILOGRAMS'

                update_input = {
                    "id": leftover_var_id,
                    "price": first_demo['price'],
                    "compareAtPrice": first_demo.get('compare_at_price'),
                    "inventoryItem": {
                        "sku": first_demo.get('sku') or '',
                        "tracked": False
                    }
                }
                if first_demo.get('weight'):
                    update_input["inventoryItem"]["measurement"] = {
                        "weight": {
                            "value": float(first_demo['weight']),
                            "unit": map_weight_unit(first_demo.get('weight_unit'))
                        }
                    }

                res_upd = graphql_query_store(live_store, live_token, bulk_update_mutation, {
                    "productId": f"gid://shopify/Product/{live_id}",
                    "variants": [update_input]
                })

                # 8. Create remaining variants
                if len(demo_prod['variants']) > 1:
                    bulk_create_mutation = """
                    mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
                      productVariantsBulkCreate(productId: $productId, variants: $variants) {
                        productVariants { id }
                        userErrors { field message }
                      }
                    }
                    """
                    variants_input = []
                    for dv in demo_prod['variants'][1:]:
                        option_values_input = []
                        for idx, val in enumerate([dv.get('option1'), dv.get('option2'), dv.get('option3')]):
                            if val:
                                opt_name = demo_prod['options'][idx]['name']
                                option_values_input.append({
                                    "optionName": opt_name,
                                    "name": val
                                })
                        v_input = {
                            "price": dv['price'],
                            "compareAtPrice": dv.get('compare_at_price'),
                            "optionValues": option_values_input,
                            "inventoryItem": {
                                "sku": dv.get('sku') or '',
                                "tracked": False
                            }
                        }
                        if dv.get('weight'):
                            v_input["inventoryItem"]["measurement"] = {
                                "weight": {
                                    "value": float(dv['weight']),
                                    "unit": map_weight_unit(dv.get('weight_unit'))
                                }
                            }
                        variants_input.append(v_input)

                    graphql_query_store(live_store, live_token, bulk_create_mutation, {
                        "productId": f"gid://shopify/Product/{live_id}",
                        "variants": variants_input
                    })

                log_pull_action(title, demo_prod['id'], live_id, len(demo_prod['variants']), "SUCCESS")
                
                # Update local dedup_data.json options cache to keep persistent
                dedup_path = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/website-catalog/Photo-organising-portal/dedup_data.json"
                if not os.path.exists(dedup_path):
                    dedup_path = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/visual dashboard/dedup_data.json"
                if os.path.exists(dedup_path):
                    try:
                        with open(dedup_path, 'r', encoding='utf-8') as f:
                            dedup_data = json.load(f)
                        
                        options_for_cache = []
                        for o in demo_prod.get('options', []):
                            options_for_cache.append({
                                "name": o['name'],
                                "values": o['values']
                            })
                        
                        short_id = str(live_id)
                        updated_cache = False
                        
                        all_prods = dedup_data.get('all_products') or []
                        if isinstance(all_prods, list):
                            for p in all_prods:
                                p_short = p.get('short_id') or p.get('id', '').split('/')[-1]
                                if p_short == short_id:
                                    p['options'] = options_for_cache
                                    updated_cache = True
                        elif isinstance(all_prods, dict):
                            for k, p in all_prods.items():
                                p_short = p.get('short_id') or k.split('/')[-1]
                                if p_short == short_id:
                                    p['options'] = options_for_cache
                                    updated_cache = True
                        
                        if updated_cache:
                            with open(dedup_path, 'w', encoding='utf-8') as f:
                                json.dump(dedup_data, f, indent=2)
                            print(f"Synced options cache for {short_id} in local dedup_data.json")
                            
                            # Trigger recompile of july deduplication dashboard
                            import subprocess
                            compile_script = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/Season_2 /July-deduplications/compile_july_data.py"
                            if os.path.exists(compile_script):
                                subprocess.run(["python3", compile_script], check=False)
                                print("Recompiled july deduplication dashboard successfully.")
                    except Exception as e:
                        print(f"Error updating local options cache: {e}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                return

            except Exception as e:
                print(f"Error executing pull variants: {e}")
                log_pull_action(title, "N/A", "N/A", 0, "FAILED", str(e))
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        elif self.path == '/api/resolve_path':
            product_title = params.get('productTitle', '')
            make = params.get('make', '')
            if not product_title or not make:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing productTitle or make"}).encode('utf-8'))
                return
                
            resolved_path = resolve_smart_path(make, product_title)
            if not resolved_path:
                resolved_path = f"/Users/parth/Downloads/Shopifydevstudio/{make}/{product_title}"
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "path": resolved_path}).encode('utf-8'))
            return

        elif self.path == '/api/pull_and_send_tg':
            product_id = params.get('productId', '')
            product_title = params.get('productTitle', '')
            short_id = product_id.split('/')[-1] if '/' in product_id else product_id
            make = params.get('make', '')
            image_urls = params.get('imageUrls', [])
            local_path = params.get('localPath', '')
            
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "Telegram Bot Token or Chat ID is missing in .env file! Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
                }).encode('utf-8'))
                return
                
            if not product_title or not make or not image_urls:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing productTitle, make, or imageUrls"}).encode('utf-8'))
                return
                
            # Resolve path safely using sanitized title
            product_title_sanitized = product_title.replace('/', '-').replace('\\', '-')
            resolved = resolve_smart_path(make, product_title)
            if resolved:
                local_path = resolved
            else:
                local_path = f"/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram/{make}/{product_title_sanitized}"
                    
            print(f"Workflow triggered: Pulling raw images to {local_path} and sending to Telegram...")
            
            # 1. Download images
            pull_errors = []
            os.makedirs(local_path, exist_ok=True)
            for index, url in enumerate(image_urls):
                try:
                    ext = '.jpg'
                    clean_url = url.split('?')[0].split('#')[0]
                    if clean_url.endswith('.png'):
                        ext = '.png'
                    elif clean_url.endswith('.webp'):
                        ext = '.webp'
                    filename = f"shopify_{index + 1}{ext}"
                    dest_file = os.path.join(local_path, filename)
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        with open(dest_file, 'wb') as f:
                            f.write(response.read())
                except Exception as e:
                    pull_errors.append(f"Failed downloading {url}: {e}")
                    
            if pull_errors:
                print(f"Errors during download: {pull_errors}")
                
            # Write metadata file including Shopify ID
            try:
                model_val = "Miscellaneous"
                category_val = "Kits"
                if "Created folder and sent to telegram" in local_path:
                    parts = os.path.relpath(local_path, f"/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram/{make}").split(os.sep)
                    if len(parts) >= 2:
                        model_val = parts[0]
                        category_val = parts[1]
                elif "Yet to send to telegram" in local_path:
                    parts = os.path.relpath(local_path, f"/Users/parth/Downloads/Shopifydevstudio/Yet to send to telegram/{make}").split(os.sep)
                    if len(parts) >= 2:
                        model_val = parts[0]
                        category_val = parts[1]
                else:
                    parts = os.path.relpath(local_path, f"/Users/parth/Downloads/Shopifydevstudio/{make}").split(os.sep)
                    if len(parts) >= 2:
                        model_val = parts[0]
                        category_val = parts[1]
            except Exception as e:
                print(f"Error determining model/category: {e}")

            meta_file_path = os.path.join(local_path, f"{product_title_sanitized}.txt")
            try:
                with open(meta_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Product: {product_title}\n")
                    f.write(f"Shopify ID: {short_id}\n")
                    f.write(f"Category: {category_val}\n")
                    f.write(f"Make: {make}\n")
                    f.write(f"Model: {model_val}\n")
                    f.write(f"Status: Folder Auto-Generated\n")
                print(f"Wrote metadata file to {meta_file_path}")
            except Exception as e:
                print(f"Error writing metadata file: {e}")
                
            # Create .tg_sent marker file
            try:
                with open(os.path.join(local_path, ".tg_sent"), 'w') as f:
                    f.write(str(int(time.time())))
                print(f"Created Telegram sent marker inside {local_path}")
            except Exception as e:
                print(f"Error writing .tg_sent marker: {e}")
                
            # 2. Create ZIP
            zip_file = None
            try:
                parent_dir = os.path.dirname(local_path)
                folder_name = os.path.basename(local_path)
                import tempfile
                temp_dir = tempfile.gettempdir()
                unique_name = f"{folder_name}_{int(time.time())}"
                zip_base = os.path.join(temp_dir, unique_name)
                shutil.make_archive(zip_base, 'zip', root_dir=parent_dir, base_dir=folder_name)
                zip_file = zip_base + ".zip"
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": f"Failed to create ZIP archive: {e}"
                }).encode('utf-8'))
                return
                
            # 3. Send to Telegram
            caption = f"📦 *RAW PHOTOS:* {product_title}\n" \
                      f"Brand: {make}\n" \
                      f"Shopify ID: `{short_id}`\n" \
                      f"Images: {len(image_urls)}"
                      
            custom_filename = f"{folder_name}.zip"
            tg_res = send_telegram_document(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, zip_file, caption, custom_filename)
            
            # Clean up ZIP file
            if zip_file and os.path.exists(zip_file):
                try:
                    os.remove(zip_file)
                except Exception as e:
                    print(f"Error removing temporary ZIP {zip_file}: {e}")
                    
            # 4. Trigger regenerate contact sheet in background
            if tg_res.get('success'):
                try:
                    import subprocess
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_contact_sheet.py')
                    # Run in background without blocking the response
                    subprocess.Popen(["python3", script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("Triggered generate_contact_sheet.py to update visual_audit_sheet.html.")
                except Exception as e:
                    print(f"Error triggering generate_contact_sheet.py: {e}")
                    
            # Reconstruct relative path
            rel_path = ""
            if local_path:
                rel_path = os.path.relpath(local_path, "/Users/parth/Downloads/Shopifydevstudio")
            
            # Read files to get list of raw images
            img_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp', '.gif', '.heic', '.heif'}
            raw_images = []
            if os.path.exists(local_path):
                for f in sorted(os.listdir(local_path)):
                    if os.path.isfile(os.path.join(local_path, f)) and not f.startswith('.') and os.path.splitext(f.lower())[1] in img_extensions:
                        raw_images.append(os.path.join(local_path, f))
            
            response_data = {
                "success": tg_res.get('success', False),
                "error": tg_res.get('error'),
                "path": rel_path,
                "raw_folder_path": local_path,
                "edited_folder_path": os.path.join(local_path, "Edited"),
                "raw_images": raw_images,
                "tg_sent": True
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        elif self.path == '/api/open_folder':
            folder_path = params.get('path', '')
            if os.path.exists(folder_path):
                import subprocess
                try:
                    subprocess.run(['open', folder_path], check=True)
                except Exception as e:
                    print(f"Failed to open folder {folder_path}: {e}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            return

        elif self.path == '/api/weight_audit_data':
            # Run weight audit logic for BMW, BENZ, PORSCHE, AUDI
            force_refresh = params.get('forceRefresh', False)
            cache_file = os.path.join(os.path.dirname(__file__), 'shopify_products_cache.json')
            
            products_list = []
            if not force_refresh and os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as cf:
                        products_list = json.load(cf)
                except Exception as ex:
                    print(f"Error reading shopify products cache: {ex}")
                    products_list = []
                    
            if not products_list:
                has_next_page = True
                cursor = None
                query_products = """
                query getProducts($cursor: String) {
                  products(first: 50, after: $cursor, query: "status:active") {
                    pageInfo { hasNextPage endCursor }
                    edges {
                      node {
                        id
                        title
                        handle
                        variants(first: 50) {
                          edges {
                            node {
                              id
                              title
                              sku
                              inventoryItem {
                                measurement {
                                  weight { value unit }
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
                while has_next_page:
                    res = graphql_query(query_products, {"cursor": cursor})
                    if not res or 'errors' in res:
                        break
                    data = res.get('data', {}).get('products', {})
                    for edge in data.get('edges', []):
                        products_list.append(edge['node'])
                    has_next_page = data.get('pageInfo', {}).get('hasNextPage', False)
                    cursor = data.get('pageInfo', {}).get('endCursor', None)
                
                # Write to cache file
                try:
                    with open(cache_file, 'w', encoding='utf-8') as cf:
                        json.dump(products_list, cf, indent=2)
                except Exception as ex:
                    print(f"Error writing shopify products cache: {ex}")

            # Audit matching using GSD targeted categories and expected weights/box sizes
            EXPECTED_SPECS = {
                "Large Hood (Supra, etc.)": {"weight": 96.0, "box": "150 x 160 x 20 cm"},
                "Regular Hood": {"weight": 68.0, "box": "150 x 150 x 15 cm"},
                "Front Bumper": {"weight": 156.0, "box": "190 x 75 x 55 cm"},
                "Rear Bumper": {"weight": 156.0, "box": "190 x 75 x 55 cm"},
                "Side Skirts (Pair)": {"weight": 25.0, "box": "205 x 30 x 20 cm"},
                "Trunk / Boot": {"weight": 65.0, "box": "135 x 115 x 25 cm"},
                "Front Fender (Pair)": {"weight": 48.0, "box": "115 x 85 x 25 cm"},
                "Door": {"weight": 64.0, "box": "140 x 115 x 20 cm"},
                "GT Wing": {"weight": 52.0, "box": "165 x 45 x 35 cm"},
                "Rear Diffuser": {"weight": 62.0, "box": "165 x 75 x 25 cm"},
                "Front Lip": {"weight": 32.0, "box": "180 x 60 x 15 cm"}
            }

            def get_brand(title):
                t = title.upper()
                
                # Replicas & Styling Kits: multi-brand titles classify under base vehicle brand
                if 'TOYOTA' in t and ('PORSCHE' in t or 'CARRERA' in t):
                    return 'TOYOTA'
                if 'MRS' in t and ('PORSCHE' in t or 'CARRERA' in t):
                    return 'TOYOTA'
                if 'MR2' in t and ('PORSCHE' in t or 'CARRERA' in t):
                    return 'TOYOTA'

                t_clean = t.replace(' ', '')
                if 'W140' in t_clean or 'W220' in t_clean: return 'BENZ'
                if 'EVO' in t and 'REVO' not in t: return 'MITSUBISHI'
                for b in ['BMW', 'AUDI', 'BENZ', 'HONDA', 'TOYOTA', 'MAZDA', 'SUBARU', 'MITSUBISHI', 'NISSAN', 'FORD', 'CHEVROLET', 'TESLA', 'UNIVERSAL', 'PORSCHE', 'PROSCHE']:
                    if b in t:
                        return 'PORSCHE' if b in ['PORSCHE', 'PROSCHE'] else b
                if 'SUPRA' in t or 'GR86' in t or 'GT86' in t or 'LEXUS' in t: return 'TOYOTA'
                if 'CIVIC' in t or 'JAZZ' in t: return 'HONDA'
                if 'RX7' in t or 'RX-7' in t or 'RX8' in t or 'RX-8' in t: return 'MAZDA'
                return 'OTHER'

            def is_large_hood(title):
                t = title.lower()
                if "hood" in t or "bonnet" in t:
                    if ("rx-7" in t or "rx7" in t) and ("re-mc" in t or "savana" in t or "re " in t or "re-" in t):
                        return True
                    if "supra" in t:
                        return True
                    if "varis" in t:
                        return True
                return False

            def get_gsd_category(p_title, v_title):
                p_title_low = p_title.lower()
                v_title_low = v_title.lower()
                
                def match_component(check_str):
                    if "lip" in check_str or "splitter" in check_str:
                        return "Front Lip"
                    if "front bumper" in check_str:
                        return "Front Bumper"
                    if "rear bumper" in check_str:
                        return "Rear Bumper"
                    if "bumper" in check_str:
                        return "Front Bumper"
                    if "hood" in check_str or "bonnet" in check_str:
                        if is_large_hood(p_title) or is_large_hood(v_title):
                            return "Large Hood (Supra, etc.)"
                        else:
                            return "Regular Hood"
                    if "side skirt" in check_str or "skirt" in check_str:
                        return "Side Skirts (Pair)"
                    if "trunk" in check_str or "boot" in check_str:
                        return "Trunk / Boot"
                    if "fender" in check_str:
                        return "Front Fender (Pair)"
                    if "door" in check_str:
                        return "Door"
                    if "wing" in check_str or "spoiler" in check_str:
                        return "GT Wing"
                    if "diffuser" in check_str:
                        return "Rear Diffuser"
                    return None

                # Rule 1: Prioritize Variant Title for specific components
                v_cat = match_component(v_title_low)
                if v_cat:
                    return v_cat
                    
                # Rule 2: Fall back to Product Title only if variant title is a generic option
                is_generic = any(x in v_title_low for x in ["default title", "gloss carbon", "matte carbon", "forged carbon", "kevlar", "frp", "fiberglass"])
                if is_generic:
                    if "complete body kit" in p_title_low or "body kit" in p_title_low or "complete kit" in p_title_low:
                        return None
                    return match_component(p_title_low)
                    
                return None

            audit_results = []
            all_active_product_ids = set()
            listed_product_ids = set()

            for p in products_list:
                p_id_raw = p.get('id', '')
                if p_id_raw:
                    all_active_product_ids.add(p_id_raw)
                    
                brand = get_brand(p.get('title', ''))
                
                # Check format of variants (REST list vs GraphQL connection dict)
                raw_variants = p.get('variants', [])
                variants_list = []
                if isinstance(raw_variants, list):
                    variants_list = raw_variants
                elif isinstance(raw_variants, dict):
                    variants_list = [edge.get('node', {}) for edge in raw_variants.get('edges', [])]
                    
                for v in variants_list:
                    # Normalize variant IDs (REST variant ids are ints)
                    v_id = v.get('id', '')
                    if v_id and not isinstance(v_id, str):
                        v_id = f"gid://shopify/ProductVariant/{v_id}"
                        
                    p_id = p.get('id', '')
                    if p_id and not isinstance(p_id, str):
                        p_id = f"gid://shopify/Product/{p_id}"
                        
                    w_val = 0.0
                    w_unit = "KILOGRAMS"
                    
                    # Handle weight format
                    if 'inventoryItem' in v:
                        m = v.get('inventoryItem', {}).get('measurement', {})
                        if m and m.get('weight'):
                            w_val = m['weight'].get('value', 0.0) or 0.0
                            w_unit = m['weight'].get('unit', 'KILOGRAMS') or 'KILOGRAMS'
                    else:
                        w_val = float(v.get('weight', 0.0) or 0.0)
                        w_unit = (v.get('weight_unit', 'KILOGRAMS') or 'KILOGRAMS').upper()
                        if w_unit == 'KG':
                            w_unit = 'KILOGRAMS'
                            
                    w_kg = w_val
                    if w_unit == "GRAMS": w_kg = w_val / 1000.0
                    elif w_unit == "POUNDS": w_kg = w_val * 0.45359237
                    
                    cat = get_gsd_category(p.get('title', ''), v.get('title', ''))
                    if not cat:
                        continue # Skip non-targeted categories (like Hardware/Accessories/Kits)
                        
                    # Mark product as listed since it has at least one targeted category variant
                    if p_id_raw:
                        listed_product_ids.add(p_id_raw)
                        
                    image_url = ""
                    if p.get('image'):
                        image_url = p.get('image', {}).get('src', '') or ''
                    elif p.get('featuredImage'):
                        image_url = p.get('featuredImage', {}).get('url', '') or ''

                    spec = EXPECTED_SPECS.get(cat)
                    expected = spec["weight"]
                    box_size = spec["box"]
                    is_match = abs(w_kg - expected) < 0.05
                        
                    p_title_low = p.get('title', '').lower()
                    is_kit = any(k in p_title_low for k in ["body kit", "bodykit", "core kit", "conversion"])

                    audit_results.append({
                        "productId": p_id,
                        "variantId": v_id,
                        "title": p.get('title', ''),
                        "variantTitle": v.get('title', ''),
                        "sku": v.get('sku', '') or "N/A",
                        "brand": brand,
                        "category": cat,
                        "currentWeight": f"{w_val} {w_unit}",
                        "weightKg": w_kg,
                        "expectedWeight": expected,
                        "boxSize": box_size,
                        "isMatch": is_match,
                        "imageUrl": image_url,
                        "isKit": is_kit
                    })

            total_active = len(all_active_product_ids)
            listed = len(listed_product_ids)
            unlisted = total_active - listed

            unlisted_kits = 0
            unlisted_hardware = 0
            unlisted_interior = 0
            unlisted_misc = 0

            def is_hardware_local(title):
                t = title.lower()
                keywords = ['bolt', 'nut', 'screw', 'stud', 'washer', 'hardware', 'thread', 'exhaust manifold stud', 'oil cap', 'radiator cap', 'eyes kit', 'keychain', 'wallet', 'harness', 'seat belt']
                return any(k in t for k in keywords)

            def is_interior_local(title):
                t = title.lower()
                keywords = ['door card', 'door panel', 'dashboard', 'molded dash', 'door sill', 'seat', 'pillar', 'gauge pod', 'console', 'armrest', 'arm rest', 'dash bezel', 'interior set', 'interior trim', 'steering wheel']
                return any(k in t for k in keywords)

            for p in products_list:
                p_id_raw = p.get('id', '')
                if p_id_raw in listed_product_ids:
                    continue
                
                p_title = p.get('title', '')
                raw_vars = p.get('variants', [])
                variants_list = []
                if isinstance(raw_vars, list):
                    variants_list = raw_vars
                elif isinstance(raw_vars, dict):
                    variants_list = [edge.get('node', {}) for edge in raw_vars.get('edges', [])]
                
                has_kit = False
                for v in variants_list:
                    v_title = v.get('title', '')
                    p_title_low = p_title.lower()
                    v_title_low = v_title.lower()
                    is_generic = any(x in v_title_low for x in ["default title", "gloss carbon", "matte carbon", "forged carbon", "kevlar", "frp", "fiberglass"])
                    check_str = p_title_low if is_generic else v_title_low
                    if "complete body kit" in check_str or "body kit" in check_str or "complete kit" in check_str:
                        has_kit = True
                        break
                
                if has_kit:
                    unlisted_kits += 1
                elif is_hardware_local(p_title):
                    unlisted_hardware += 1
                elif is_interior_local(p_title):
                    unlisted_interior += 1
                else:
                    unlisted_misc += 1

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True, 
                "variants": audit_results,
                "summary": {
                    "totalActiveProducts": total_active,
                    "listedProducts": listed,
                    "unlistedProducts": unlisted,
                    "unlistedKits": unlisted_kits,
                    "unlistedHardware": unlisted_hardware,
                    "unlistedInterior": unlisted_interior,
                    "unlistedMisc": unlisted_misc
                }
            }).encode('utf-8'))
            return

        elif self.path == '/api/update_variant_weight':
            product_id = params.get('productId', '')
            variant_id = params.get('variantId', '')
            variant_ids_list = params.get('variantIds', [])
            weight = params.get('weight', 0.0)
            
            ids_to_update = []
            if variant_ids_list:
                ids_to_update = variant_ids_list
            elif isinstance(variant_id, list):
                ids_to_update = variant_id
            elif isinstance(variant_id, str) and variant_id:
                if ',' in variant_id:
                    ids_to_update = [x.strip() for x in variant_id.split(',') if x.strip()]
                else:
                    ids_to_update = [variant_id]
            
            if not product_id or not ids_to_update:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing parameters"}).encode('utf-8'))
                return
                
            bulk_update_mutation = """
            mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
              productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                productVariants { id }
                userErrors { field message }
              }
            }
            """
            
            variants_payload = []
            for v_id in ids_to_update:
                variants_payload.append({
                    "id": v_id,
                    "inventoryItem": {
                        "measurement": {
                            "weight": {
                                "value": float(weight),
                                "unit": "KILOGRAMS"
                            }
                        }
                    }
                })
                
            res = graphql_query(bulk_update_mutation, {
                "productId": product_id,
                "variants": variants_payload
            })
            
            success = False
            error_msg = None
            if res and not res.get('errors'):
                user_errors = res.get('data', {}).get('productVariantsBulkUpdate', {}).get('userErrors', [])
                if user_errors:
                    error_msg = str(user_errors)
                else:
                    success = True
            else:
                error_msg = str(res)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "error": error_msg}).encode('utf-8'))
            return

        elif self.path == '/api/weights/bulk_update_category':
            target_category = params.get('category', '')
            expected_weight = params.get('weight', 0.0)
            
            if not target_category or expected_weight <= 0.0:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing or invalid parameters"}).encode('utf-8'))
                return
                
            # Perform query on active products to locate mismatching variants for this category
            query_products = """
            query getProducts($cursor: String) {
              products(first: 50, after: $cursor, query: "status:active") {
                pageInfo { hasNextPage endCursor }
                edges {
                  node {
                    id
                    title
                    variants(first: 100) {
                      edges {
                        node {
                          id
                          title
                          inventoryItem {
                            measurement {
                              weight { value unit }
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
            
            bulk_update_mutation = """
            mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
              productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                productVariants { id }
                userErrors { field message }
              }
            }
            """
            
            def is_large_hood_local(title):
                t = title.lower()
                if "hood" in t or "bonnet" in t:
                    if ("rx-7" in t or "rx7" in t) and ("re-mc" in t or "savana" in t or "re " in t or "re-" in t):
                        return True
                    if "supra" in t:
                        return True
                    if "varis" in t:
                        return True
                return False

            def get_gsd_category_local(p_title, v_title):
                p_title_low = p_title.lower()
                v_title_low = v_title.lower()
                is_generic = any(x in v_title_low for x in ["default title", "gloss carbon", "matte carbon", "forged carbon", "kevlar", "frp", "fiberglass"])
                check_str = p_title_low if is_generic else v_title_low
                if "complete body kit" in check_str or "body kit" in check_str or "complete kit" in check_str:
                    return None
                if "front bumper" in check_str: return "Front Bumper"
                if "rear bumper" in check_str: return "Rear Bumper"
                if "bumper" in check_str: return "Front Bumper"
                if "hood" in check_str or "bonnet" in check_str:
                    return "Large Hood (Supra, etc.)" if is_large_hood_local(p_title) or is_large_hood_local(v_title) else "Regular Hood"
                if "lip" in check_str or "splitter" in check_str: return "Front Lip"
                if "side skirt" in check_str or "skirt" in check_str: return "Side Skirts (Pair)"
                if "trunk" in check_str or "boot" in check_str: return "Trunk / Boot"
                if "fender" in check_str: return "Front Fender (Pair)"
                if "door" in check_str: return "Door"
                if "wing" in check_str or "spoiler" in check_str: return "GT Wing"
                if "diffuser" in check_str: return "Rear Diffuser"
                return None

            has_next_page = True
            cursor = None
            updated_count = 0
            
            while has_next_page:
                res = graphql_query(query_products, {"cursor": cursor})
                if not res or 'errors' in res:
                    break
                data = res.get('data', {}).get('products', {})
                for edge in data.get('edges', []):
                    prod = edge['node']
                    p_id = prod['id']
                    p_title = prod['title']
                    
                    variants_to_update = []
                    for ve in prod.get('variants', {}).get('edges', []):
                        var = ve['node']
                        v_title = var['title']
                        v_id = var['id']
                        
                        cat = get_gsd_category_local(p_title, v_title)
                        if cat == target_category:
                            inv_item = var.get('inventoryItem') or {}
                            measurement = inv_item.get('measurement') or {}
                            weight_obj = measurement.get('weight') or {}
                            v_weight = weight_obj.get('value', 0.0) or 0.0
                            v_unit = weight_obj.get('unit', 'KILOGRAMS') or 'KILOGRAMS'
                            
                            w_kg = v_weight
                            if v_unit.upper() == "GRAMS": w_kg = v_weight / 1000.0
                            elif v_unit.upper() == "POUNDS": w_kg = v_weight * 0.45359237
                            
                            if abs(w_kg - expected_weight) > 0.05:
                                variants_to_update.append({
                                    "id": v_id,
                                    "inventoryItem": {
                                        "measurement": {
                                            "weight": {
                                                "value": float(expected_weight),
                                                "unit": "KILOGRAMS"
                                            }
                                        }
                                    }
                                })
                                
                    if variants_to_update:
                        update_res = graphql_query(bulk_update_mutation, {
                            "productId": p_id,
                            "variants": variants_to_update
                        })
                        if update_res and not update_res.get('errors'):
                            user_errors = update_res.get('data', {}).get('productVariantsBulkUpdate', {}).get('userErrors', [])
                            if not user_errors:
                                updated_count += len(variants_to_update)
                        time.sleep(0.1) # small safety gap
                        
                has_next_page = data.get('pageInfo', {}).get('hasNextPage', False)
                cursor = data.get('pageInfo', {}).get('endCursor', None)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "updatedCount": updated_count}).encode('utf-8'))
            return


        elif self.path == '/api/telegram/sync':
            folder_name = params.get('folderName')
            brand = params.get('brand')
            model = params.get('model')
            product_id = params.get('productId')
            product_title = params.get('productTitle')
            
            if not folder_name or not brand or not model or not product_id or not product_title:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing parameters"}).encode('utf-8'))
                return
                
            try:
                # 1. Setup paths
                backlog_path = os.path.join("/Users/parth/Downloads/Shopifydevstudio/_TG_Unmatched_Backlog", folder_name)
                product_title_sanitized = product_title.replace('/', '-').replace('\\', '-')
                
                # Check target base
                dest_base = f"/Users/parth/Downloads/Shopifydevstudio/Created folder and sent to telegram/{brand}/{model}/{product_title_sanitized}"
                edited_dir = os.path.join(dest_base, "edited")
                os.makedirs(edited_dir, exist_ok=True)
                
                # 2. Move files from backlog_path to edited_dir
                moved_count = 0
                if os.path.exists(backlog_path):
                    for root, dirs, files in os.walk(backlog_path):
                        for file in files:
                            if not file.startswith('.'):
                                src_file = os.path.join(root, file)
                                dest_file = os.path.join(edited_dir, file)
                                # Copy and remove to handle potential mount boundaries, or shutil.move
                                shutil.move(src_file, dest_file)
                                moved_count += 1
                                
                    # Cleanup backlog folder
                    shutil.rmtree(backlog_path, ignore_errors=True)
                
                # 3. Create metadata file
                short_id = str(product_id).split('/')[-1]
                meta_file_path = os.path.join(dest_base, f"{product_title_sanitized}.txt")
                with open(meta_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Product: {product_title}\n")
                    f.write(f"Shopify ID: {short_id}\n")
                    f.write(f"Category: Kits\n")
                    f.write(f"Make: {brand}\n")
                    f.write(f"Model: {model}\n")
                    f.write(f"Status: Folder Auto-Generated\n")
                    
                # 4. Create .tg_sent marker file
                with open(os.path.join(dest_base, ".tg_sent"), 'w') as f:
                    f.write(str(int(time.time())))
                    
                # 5. Regenerate main contact sheet html
                import subprocess
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_contact_sheet.py')
                subprocess.Popen(["python3", script_path])
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "moved_count": moved_count}).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        elif self.path == '/api/calibration_log':
            log_path = os.path.join(os.path.dirname(__file__), 'antigravity_calibration_log.json')
            log_data = {"weight_calibrations": [], "product_renames": [], "variant_deletions": [], "handle_redirects": []}
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as lf:
                        log_data = json.load(lf)
                except Exception as e:
                    print("Error loading log:", e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "log": log_data}).encode('utf-8'))
            return

        elif self.path == '/api/push_local_images':
            folder_path = params.get('folderPath')
            product_id = params.get('productId')
            
            if not folder_path or not product_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing folderPath or productId"}).encode('utf-8'))
                return
                
            graphql_prod_id = product_id if product_id.startswith('gid://') else f"gid://shopify/Product/{product_id}"
            
            # Scan local images
            edited_dir = os.path.join(folder_path, "edited")
            local_files = []
            if os.path.exists(edited_dir):
                for f in os.listdir(edited_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        local_files.append(os.path.join(edited_dir, f))
            else:
                if os.path.exists(folder_path):
                    for f in os.listdir(folder_path):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and f.lower().startswith('shopify_'):
                            local_files.append(os.path.join(folder_path, f))
            
            # Abort if no local files to avoid leaving the product gallery completely empty
            if not local_files:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "No local images found in folder"}).encode('utf-8'))
                return

            # Fetch all existing product media IDs on Shopify
            existing_media_ids = []
            try:
                media_query = """
                query getProductMedia($id: ID!) {
                  product(id: $id) {
                    media(first: 50) {
                      nodes {
                        id
                      }
                    }
                  }
                }
                """
                mq_res = graphql_query(media_query, {"id": graphql_prod_id})
                media_nodes = mq_res.get('data', {}).get('product', {}).get('media', {}).get('nodes', [])
                existing_media_ids = [node.get('id') for node in media_nodes if node.get('id')]
            except Exception as e:
                print("Error fetching existing media for deletion:", e)

            # Delete all existing media if found
            if existing_media_ids:
                try:
                    delete_mutation = """
                    mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
                      productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
                        deletedMediaIds
                        userErrors {
                          field
                          message
                        }
                      }
                    }
                    """
                    del_res = graphql_query(delete_mutation, {"mediaIds": existing_media_ids, "productId": graphql_prod_id})
                    print(f"Deleted existing media on Shopify: {del_res}")
                except Exception as e:
                    print("Error deleting existing media:", e)
                        
            uploaded_urls = []
            import mimetypes
            
            for file_path in local_files:
                try:
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    filename = os.path.basename(file_path)
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                    upload_to_shopify_bytes(file_bytes, filename, mime_type, graphql_prod_id)
                except Exception as ex:
                    print(f"Error uploading file {file_path}: {ex}")
            
            # Query the product images directly from Shopify to get the complete current list of images
            latest_images = []
            try:
                prod_query = """
                query getProduct($id: ID!) {
                  product(id: $id) {
                    images(first: 50) {
                      nodes {
                        url
                      }
                    }
                  }
                }
                """
                # Wait 2 seconds for processing to finish
                time.sleep(2)
                pq_res = graphql_query(prod_query, {"id": graphql_prod_id})
                nodes = pq_res.get('data', {}).get('product', {}).get('images', {}).get('nodes', [])
                for node in nodes:
                    url = node.get('url')
                    if url:
                        latest_images.append(url)
            except Exception as e:
                print("Error fetching latest product images:", e)
                    
            # Update cache file shopify_products_cache.json
            try:
                cache_file = os.path.join(os.path.dirname(__file__), 'shopify_products_cache.json')
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as cf:
                        products_cache = json.load(cf)
                    
                    clean_id = product_id.split('/')[-1]
                    for p in products_cache:
                        p_id = str(p.get('id', '')).split('/')[-1]
                        if p_id == clean_id:
                            p['images'] = [{"src": url} for url in latest_images]
                            break
                            
                    with open(cache_file, 'w', encoding='utf-8') as cf:
                        json.dump(products_cache, cf, indent=2)
            except Exception as ex:
                print(f"Error updating cache after push: {ex}")
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "uploaded_urls": latest_images}).encode('utf-8'))
            return

        else:
            self.send_response(404)
            self.end_headers()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_server():
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, ShopifyManagerHandler)
    print(f"🚀 Shopify Local Manager helper server running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
