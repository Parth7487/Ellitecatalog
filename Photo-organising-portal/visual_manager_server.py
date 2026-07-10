import http.server
import json
import urllib.request
import urllib.parse
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
        if parsed.path == '/' or parsed.path == '/visual' or parsed.path == '/visual_audit_sheet.html' or parsed.path == '/visual_audit_sheet':
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

        if self.path == '/api/refresh_dedup':
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

            # Audit matching
            MATRIX = {
                "bumper":        {"S": 105, "M": 140, "L": 170, "XL": 185},
                "body_kit":      {"S": 156, "M": 200, "L": 220, "XL": 260},
                "hood":          {"S": 55,  "M": 74,  "L": 98,  "XL": 112},
                "roof":          {"S": 45,  "M": 55,  "L": 72,  "XL": 90},
                "trunk":         {"S": 52,  "M": 67,  "L": 88,  "XL": 107},
                "front_fender":  {"S": 46,  "M": 66,  "L": 78,  "XL": 90},
                "rear_fender":   {"S": 30,  "M": 41,  "L": 62,  "XL": 70},
                "door":          {"S": 40,  "M": 51,  "L": 64,  "XL": 84},
                "front_lip":     {"S": 12,  "M": 32,  "L": 46,  "XL": 52},
                "side_skirt":    {"S": 15,  "M": 28,  "L": 37,  "XL": 41},
                "rear_diffuser": {"S": 12,  "M": 30,  "L": 48,  "XL": 62},
                "spoiler":       {"S": 10,  "M": 17,  "L": 30,  "XL": 35},
                "gt_wing":       {"S": 52,  "M": 52,  "L": 60,  "XL": 70},
                "canards":       {"S": 2,   "M": 4,   "L": 7,   "XL": 8},
                "mirror_cover":  {"S": 6,   "M": 6,   "L": 6,   "XL": 6},
                "hood_vent":     {"S": 2,   "M": 4,   "L": 8,   "XL": 10},
                "fog_cover":     {"S": 5,   "M": 5,   "L": 5,   "XL": 5},
                "small_panel":   {"S": 5,   "M": 10,  "L": 15,  "XL": 20},
                "interior_small":{"S": 3,   "M": 4,   "L": 5,   "XL": 6},
                "interior_pod":  {"S": 3,   "M": 5,   "L": 8,   "XL": 13},
                "interior_console":{"S":3,  "M": 10,  "L": 16,  "XL": 16},
                "interior_dash": {"S": 7,   "M": 12,  "L": 20,  "XL": 25},
                "interior_full_dash":{"S":85,"M": 95, "L": 110, "XL": 125},
                "door_card":     {"S": 31,  "M": 38,  "L": 50,  "XL": 64},
                "interior_kit":  {"S": 15,  "M": 25,  "L": 35,  "XL": 45},
                "pillar_trim":   {"S": 4,   "M": 8,   "L": 12,  "XL": 16},
                "door_sill":     {"S": 5,   "M": 8,   "L": 11,  "XL": 14},
                "seat":          {"S": 33,  "M": 37,  "L": 45,  "XL": 55}
            }

            CHASSIS_MAP = {
                r'\branger\b': 'XL', r'\bfortuner\b': 'XL', r'\brevo\b': 'XL', r'\bvigo\b': 'XL', r'\bhilux\b': 'XL', r'\bt7\b': 'XL', r'\bt6\b': 'XL',
                r'\bsupra\b': 'L', r'\bskyline\b': 'L', r'\bgtr\b': 'L', r'\br32\b': 'L', r'\br33\b': 'L', r'\br34\b': 'L', r'\br35\b': 'L', 
                r'\b350z\b': 'L', r'\b370z\b': 'L', r'\bcorvette\b': 'L', r'\bc8\b': 'L', r'\blexus\b': 'L', r'\bls430\b': 'L', r'\bls 430\b': 'L',
                r'\brx7\b': 'M', r'\brx-7\b': 'M', r'\brx8\b': 'M', r'\brx-8\b': 'M', r'\bs13\b': 'M', r'\bs14\b': 'M', r'\bs15\b': 'M', r'\bsilvia\b': 'M',
                r'\bevo\b': 'M', r'\blancer\b': 'M', r'\bgr86\b': 'M', r'\bbrz\b': 'M', r'\bft86\b': 'M', r'\bgt86\b': 'M', 
                r'\be30\b': 'M', r'\be36\b': 'M', r'\be46\b': 'M', r'\be60\b': 'M', r'\be90\b': 'M', r'\be92\b': 'M', r'\be93\b': 'M', r'\bf30\b': 'M', r'\bf32\b': 'M',
                r'\bcivic\b': 'S', r'\bek9\b': 'S', r'\beg\b': 'S', r'\bfk\b': 'S', r'\bfc\b': 'S', r'\bjazz\b': 'S', r'\bfit\b': 'S', r'\bmr2\b': 'S', r'\bmrs\b': 'S', r'\bmr-s\b': 'S'
            }

            def get_chassis_class(title):
                title_lower = title.lower()
                for pattern, cls in CHASSIS_MAP.items():
                    if re.search(pattern, title_lower):
                        return cls
                return "M"

            def get_category(title):
                t = title.lower()
                if any(k in t for k in ['bolt', 'nut', 'screw', 'stud', 'washer', 'hardware', 'thread', 'exhaust manifold stud', 'seat belt', 'harness']):
                    return "hardware"
                if any(k in t for k in ['oil cap', 'radiator cap', 'eyes kit', 'keychain', 'wallet']):
                    return "hardware"
                if 'body kit' in t or 'bodykit' in t:
                    return "body_kit"
                if 'front bumper' in t or 'rear bumper' in t:
                    return "bumper"
                if any(k in t for k in ['hood', 'bonnet']):
                    return "hood"
                if 'roof' in t:
                    return "roof"
                if 'trunk' in t or 'hatch' in t or 'bootlid' in t:
                    return "trunk"
                if 'front fender' in t:
                    return "front_fender"
                if 'rear fender' in t or 'fender flare' in t:
                    return "rear_fender"
                if 'door' in t and not 'door card' in t and not 'door sill' in t:
                    return "door"
                if 'front lip' in t or 'front splitter' in t or 'front diffuser' in t or 'pro lip' in t:
                    return "front_lip"
                if 'side skirt' in t or 'side diffuser' in t or 'door blades' in t:
                    return "side_skirt"
                if 'rear diffuser' in t or 'rear splitter' in t:
                    return "rear_diffuser"
                if 'gt wing' in t or 'gt spoiler' in t:
                    return "gt_wing"
                if 'spoiler' in t or 'wing' in t:
                    return "spoiler"
                if 'canard' in t:
                    return "canards"
                if 'mirror' in t:
                    return "mirror_cover"
                if 'hood vent' in t or 'bonnet vent' in t:
                    return "hood_vent"
                if 'fog' in t or 'light cover' in t:
                    return "fog_cover"
                if any(k in t for k in ['cooling panel', 'slam panel', 'heat shield', 'vent cover', 'radiator', 'air filter cover', 'fluid cover']):
                    return "small_panel"
                if 'door card' in t or 'door panel' in t:
                    return "door_card"
                if 'dashboard' in t or 'molded dash' in t:
                    return "interior_full_dash"
                if 'door sill' in t:
                    return "door_sill"
                if 'seat' in t:
                    return "seat"
                if 'pillar' in t:
                    return "pillar_trim"
                if 'gauge pod' in t:
                    return "interior_pod"
                if 'console' in t or 'armrest' in t or 'arm rest' in t:
                    return "interior_console"
                if 'dash' in t or 'bezel' in t or 'interior set' in t or 'interior trim' in t:
                    return "interior_dash"
                return "unknown"

            def get_brand(title):
                t = title.upper()
                if 'W140' in t or 'W220' in t: return 'BENZ'
                if 'BMW' in t or 'BMC' in t: return 'BMW'
                if 'BENZ' in t or 'MERCEDES' in t: return 'BENZ'
                if 'PORSCHE' in t or 'PROSCHE' in t: return 'PORSCHE'
                if 'AUDI' in t: return 'AUDI'
                return None

            audit_results = []
            for p in products_list:
                brand = get_brand(p['title'])
                if not brand: continue
                
                chassis_class = get_chassis_class(p['title'])
                prod_cat = get_category(p['title'])
                
                for ve in p.get('variants', {}).get('edges', []):
                    v = ve['node']
                    w_val = 0.0
                    w_unit = "KILOGRAMS"
                    m = v.get('inventoryItem', {}).get('measurement', {})
                    if m and m.get('weight'):
                        w_val = m['weight'].get('value', 0.0)
                        w_unit = m['weight'].get('unit', 'KILOGRAMS')
                    
                    w_kg = w_val
                    if w_unit == "GRAMS": w_kg = w_val / 1000.0
                    elif w_unit == "POUNDS": w_kg = w_val * 0.45359237
                    
                    v_cat = get_category(v['title'])
                    final_cat = v_cat if v_cat != "unknown" else prod_cat
                    
                    expected = None
                    is_match = False
                    if final_cat == "hardware":
                        expected = 0.5
                        is_match = (w_kg < 2.0)
                    elif final_cat != "unknown":
                        row = MATRIX.get(final_cat)
                        if row:
                            expected = row.get(chassis_class)
                            is_match = abs(w_kg - expected) < 0.05
                    else:
                        is_match = True
                        
                    audit_results.append({
                        "productId": p['id'],
                        "variantId": v['id'],
                        "title": p['title'],
                        "variantTitle": v['title'],
                        "sku": v['sku'],
                        "brand": brand,
                        "category": final_cat,
                        "chassisClass": chassis_class,
                        "currentWeight": f"{w_val} {w_unit}",
                        "weightKg": w_kg,
                        "expectedWeight": expected,
                        "isMatch": is_match
                    })

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "variants": audit_results}).encode('utf-8'))
            return

        elif self.path == '/api/update_variant_weight':
            product_id = params.get('productId', '')
            variant_id = params.get('variantId', '')
            weight = params.get('weight', 0.0)
            
            if not product_id or not variant_id:
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
            res = graphql_query(bulk_update_mutation, {
                "productId": product_id,
                "variants": [{
                    "id": variant_id,
                    "inventoryItem": {
                        "measurement": {
                            "weight": {
                                "value": float(weight),
                                "unit": "KILOGRAMS"
                            }
                        }
                    }
                }]
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
