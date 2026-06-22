# 📸 Photo Organising Portal

A local visual manager and sync portal that matches your local product photos (Raw & Edited) against your live Shopify store catalog.

---

## 🚀 How to Run the Portal

### 1. Start the Helper Server
This server handles local file operations (loading local images, direct drag-and-drop uploads, and moving deleted files to the `.trash` folder).
In your terminal, run:
```bash
python3 website-catalog/Photo-organising-portal/visual_manager_server.py
```
*Keep this terminal window open while using the portal.*

### 2. Open the Portal
Open the following file in your browser (Brave, Chrome, Safari, etc.):
👉 **[visual_audit_sheet.html](visual_audit_sheet.html)**

---

## 🛠️ Features & Usage Guide

### 1. Drag & Drop Uploads
* **From OS (Finder / Desktop)**: Drag image files from your computer and drop them anywhere inside the **Shopify Live CDN** zone of the product to instantly upload them to Shopify.
* **Internally on Portal**: Drag images from the **Local Raw Folder** or **Local Edited Folder** columns and drop them into the **Shopify Live CDN** zone to upload them directly.

### 2. Move Local Images to Trash
* Hover over any image under **Local Edited Folder** and click the red **`×`** button.
* Confirm the prompt. The file will be moved into the safe `.trash/` recycle directory.

### 3. Deletion Tracking
Every local deletion is tracked automatically in the markdown report file:
👉 **[deleted_local_images.md](deleted_local_images.md)**

---

## 🔄 When & How to Re-generate (Sync / Refresh)
`visual_audit_sheet.html` is a snapshot of your folders and products.

### When should I re-generate?
Run the sync script **only** when you:
1. Create/add new product folders locally on your drive.
2. Add brand-new products to your Shopify store.

### How to re-generate:
In your terminal, run:
```bash
python3 website-catalog/Photo-organising-portal/generate_contact_sheet.py
```
This will automatically scan all folders, query Shopify, and rebuild `visual_audit_sheet.html` with the latest products and image mappings.
