import os
import re
import json

base_reports_path = "/Users/parth/Library/CloudStorage/GoogleDrive-shopifydevstudioo@gmail.com/.shortcut-targets-by-id/1-CcnV0dMYSWOgUsYXSlMff4iCNY5XYDH/Elite Ti Photos/Shopifydevstudio/Reports/Folders_Health"
output_file = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN/website-catalog/health_data.json"

makes_files = {
    "BMW": "bmw_health_report.md",
    "Honda": "honda_health_report.md",
    "Mazda": "mazda_health_report.md",
    "Mercedes-Benz": "mercedes-benz_health_report.md",
    "Mitsubishi": "mitsubishi_health_report.md",
    "Nissan": "nissan_health_report.md",
    "Porsche": "porsche_health_report.md",
    "Toyota": "toyota_health_report.md"
}

def parse_report(filepath, make_name):
    if not os.path.exists(filepath):
        print(f"⚠️ Report file not found: {filepath}")
        return None
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Regex for stats
    total_match = re.search(r"Total Product Folders Found.*?[\`\']?(\d+)[\`\']?\s*folders", content, re.IGNORECASE)
    raw_imgs_match = re.search(r"Total Raw Images \(excluding.*?[\`\']?([\d,]+)[\`\']?\s*images", content, re.IGNORECASE)
    edited_imgs_match = re.search(r"Total Edited Images \(inside.*?[\`\']?([\d,]+)[\`\']?\s*images", content, re.IGNORECASE)
    folders_edited_match = re.search(r"Folders WITH Edited Images.*?[\`\']?(\d+)[\`\']?\s*folders", content, re.IGNORECASE)
    folders_raw_match = re.search(r"Folders WITH ONLY Raw Images.*?[\`\']?(\d+)[\`\']?\s*folders", content, re.IGNORECASE)
    folders_empty_match = re.search(r"Empty Placeholder Folders.*?[\`\']?(\d+)[\`\']?\s*folders", content, re.IGNORECASE)
    
    stats = {
        "make": make_name,
        "total_folders": int(total_match.group(1)) if total_match else 0,
        "raw_images": int(raw_imgs_match.group(1).replace(",", "")) if raw_imgs_match else 0,
        "edited_images": int(edited_imgs_match.group(1).replace(",", "")) if edited_imgs_match else 0,
        "folders_with_edited": int(folders_edited_match.group(1)) if folders_edited_match else 0,
        "folders_with_only_raw": int(folders_raw_match.group(1)) if folders_raw_match else 0,
        "folders_empty": int(folders_empty_match.group(1)) if folders_empty_match else 0,
        "folders": []
    }
    
    # Let's parse tables section by section
    # Section 1: Folders with Edited Images
    # Look for table after the header
    edited_section = re.search(r"## \S+ 1\. Folders with Edited Images.*?\n(.*?)(?=\n## \S+ 2\.|\Z)", content, re.DOTALL | re.IGNORECASE)
    if edited_section:
        table_text = edited_section.group(1)
        for line in table_text.splitlines():
            # Match | 1 | `911/Kits/Porsche 911 GT3 Body Kit` | 20 | 21 | `2026-05-18` |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6 and parts[1].isdigit():
                folder_path = parts[2].replace("`", "")
                raw_count = int(parts[3]) if parts[3].isdigit() else 0
                edited_count = int(parts[4]) if parts[4].isdigit() else 0
                upload_date = parts[5].replace("`", "")
                stats["folders"].append({
                    "path": folder_path,
                    "raw_count": raw_count,
                    "edited_count": edited_count,
                    "status": "edited",
                    "upload_date": upload_date
                })
                
    # Section 2: Folders with Only Raw Images
    raw_section = re.search(r"## \S+ 2\. Folders with Only Raw Images.*?\n(.*?)(?=\n## \S+ 3\.|\Z)", content, re.DOTALL | re.IGNORECASE)
    if raw_section:
        table_text = raw_section.group(1)
        for line in table_text.splitlines():
            # Match | 1 | `GT86/Exterior/BRZ ZC6...` | 6 | `2026-05-18` |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].isdigit():
                folder_path = parts[2].replace("`", "")
                raw_count = int(parts[3]) if parts[3].isdigit() else 0
                upload_date = parts[4].replace("`", "") if len(parts) >= 5 and parts[4] else "N/A"
                stats["folders"].append({
                    "path": folder_path,
                    "raw_count": raw_count,
                    "edited_count": 0,
                    "status": "raw_only",
                    "upload_date": upload_date
                })
                
    # Section 3: Empty Placeholder Folders
    empty_section = re.search(r"## \S+ 3\. Empty Placeholder Folders.*?\n(.*?)(?=\n---|\Z)", content, re.DOTALL | re.IGNORECASE)
    if empty_section:
        table_text = empty_section.group(1)
        for line in table_text.splitlines():
            # Match | 1 | `718/Kits/PORSCHE 718 AYA Body Kit` |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[1].isdigit():
                folder_path = parts[2].replace("`", "")
                stats["folders"].append({
                    "path": folder_path,
                    "raw_count": 0,
                    "edited_count": 0,
                    "status": "empty",
                    "upload_date": "N/A"
                })
                
    return stats

def main():
    print("⏳ Scanning Google Drive Folder Health Reports...")
    data = []
    
    for make, filename in makes_files.items():
        filepath = os.path.join(base_reports_path, filename)
        stats = parse_report(filepath, make)
        if stats:
            data.append(stats)
            print(f"✅ Parsed {make}: {stats['folders_with_edited']} completed folders out of {stats['total_folders']}.")
            
    # Calculate totals
    grand_total_folders = sum(d["total_folders"] for d in data)
    grand_folders_edited = sum(d["folders_with_edited"] for d in data)
    grand_folders_raw = sum(d["folders_with_only_raw"] for d in data)
    grand_folders_empty = sum(d["folders_empty"] for d in data)
    grand_total_edited_imgs = sum(d["edited_images"] for d in data)
    grand_total_raw_imgs = sum(d["raw_images"] for d in data)
    
    summary = {
        "brands": data,
        "totals": {
            "total_folders": grand_total_folders,
            "folders_with_edited": grand_folders_edited,
            "folders_with_only_raw": grand_folders_raw,
            "folders_empty": grand_folders_empty,
            "total_edited_images": grand_total_edited_imgs,
            "total_raw_images": grand_total_raw_imgs,
            "completion_percentage": round((grand_folders_edited / grand_total_folders * 100), 1) if grand_total_folders > 0 else 0.0
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"🎉 Success! Extracted and wrote health data to {output_file}")

if __name__ == "__main__":
    main()
