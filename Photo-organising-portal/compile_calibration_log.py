import json
import os

PORTAL_DIR = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/website-catalog/Photo-organising-portal"
MEMORY_DIR = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/Memory"

log_data = {
    "weight_calibrations": [],
    "product_renames": [
        {
            "old_title": "BMW W 140 2DOOR FAB DESIGN Body Kit",
            "new_title": "Mercedes-Benz W 140 2DOOR FAB DESIGN Body Kit",
            "timestamp": "2026-07-10T12:43:46Z"
        },
        {
            "old_title": "BMW W220 WALD Body Kit",
            "new_title": "Mercedes-Benz W220 WALD Body Kit",
            "timestamp": "2026-07-10T12:43:50Z"
        }
    ],
    "variant_deletions": [],
    "handle_redirects": []
}

# 1. Parse Weight Calibrations
weight_path = os.path.join(PORTAL_DIR, "bbp_updated_weight_rollback.json")
if os.path.exists(weight_path):
    with open(weight_path, "r", encoding="utf-8") as f:
        weights = json.load(f)
    for vid, w in weights.items():
        log_data["weight_calibrations"].append({
            "product": w["product"],
            "variant": w["variant"],
            "sku": w["sku"] or "N/A",
            "old_weight": f"{w['old_weight']} {w['old_unit'].lower()}",
            "new_weight": f"{w['new_weight']} kg",
            "timestamp": "2026-07-10T11:10:59Z"
        })

# 2. Parse variant deletions (FRP Hood deletions)
deletions_path = "/Users/parth/.gemini/antigravity-ide/brain/1a1a4474-1f5d-44ba-8287-24836312151c/scratch/frp_deletion_targets.json"
if os.path.exists(deletions_path):
    with open(deletions_path, "r", encoding="utf-8") as f:
        deletions = json.load(f)
    for d in deletions:
        log_data["variant_deletions"].append({
            "product": d["product_title"],
            "variant": "FRP / Fiberglass",
            "reason": "Duplicate FRP Option Removal",
            "timestamp": "2026-07-09T23:46:53Z"
        })

# 3. Parse handle redirects
redirects_path = os.path.join(MEMORY_DIR, "2026-07-09_handle_changes_rollback.json")
if os.path.exists(redirects_path):
    with open(redirects_path, "r", encoding="utf-8") as f:
        redirects = json.load(f)
    for title, r in redirects.items():
        log_data["handle_redirects"].append({
            "title": title,
            "old_handle": r["old_handle"],
            "new_handle": r["new_handle"],
            "timestamp": "2026-07-09T00:48:38Z"
        })

# Save log
output_path = os.path.join(PORTAL_DIR, "antigravity_calibration_log.json")
with open(output_path, "w", encoding="utf-8") as out:
    json.dump(log_data, out, indent=2)

print(f"Compiled unified calibration log at: {output_path}")
print(f"  - Weight Calibrations: {len(log_data['weight_calibrations'])}")
print(f"  - Product Renames: {len(log_data['product_renames'])}")
print(f"  - Variant Deletions: {len(log_data['variant_deletions'])}")
print(f"  - Handle Redirects: {len(log_data['handle_redirects'])}")
