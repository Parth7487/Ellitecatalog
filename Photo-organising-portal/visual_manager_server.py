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

def load_token():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('SHOPIFY_TOKEN='):
                    return line.strip().split('=', 1)[1].strip('"\'')
    return os.environ.get('SHOPIFY_TOKEN', '')

TOKEN = load_token()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def graphql_query(query, variables=None):
    url = f"https://{STORE}/admin/api/2024-01/graphql.json"
    headers = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
    data = {"query": query}
    if variables: data["variables"] = variables
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"GraphQL request failed: {e}")
        return {"errors": [{"message": str(e)}]}

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
    return None


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
        if parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode('utf-8'))
        elif parsed.path == '/api/image':
            query = urllib.parse.parse_qs(parsed.query)
            file_path = query.get('path', [None])[0]
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
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            params = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
            return

        if self.path == '/api/delete':
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
            if res and 'errors' not in res and not (res.get('data', {}).get('productDeleteMedia', {}).get('userErrors')):
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
                                    old_len = len(p['live_images'])
                                    p['live_images'] = [img for img in p['live_images'] if img['id'] != media_id]
                                    if len(p['live_images']) != old_len:
                                        p['shopify_count'] = len(p['live_images'])
                                        updated = True
                                        break
                            if updated:
                                new_json_str = json.dumps(products, ensure_ascii=False)
                                new_content = content.replace(json_str, new_json_str, 1)
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                print(f"Removed media {media_id} from local HTML cache.")
                    except Exception as ex:
                        print(f"Error updating local HTML cache: {ex}")
                        
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
                                    break
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
                                            break
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
                                break
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
            return

        else:
            self.send_response(404)
            self.end_headers()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

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
