import pandas as pd
import json
import os
from datetime import datetime

excel_path = 'Wholesale_GreenActive_Merged_Master_Revised_v2.0.xlsx'
output_json = 'data.json'

os.makedirs('public', exist_ok=True)

xl = pd.ExcelFile(excel_path)

def extract_kits(xl):
    df = xl.parse('Changes Kits', header=None)
    # Header was found at index 5
    header_idx = 5
    data_df = xl.parse('Changes Kits', skiprows=header_idx + 1, header=None)
    data_df.columns = ['Brand', 'Model', 'Style', 'Part', 'SKU', 'Price', 'Dims']
    
    # Clean data
    data_df['Brand'] = data_df['Brand'].ffill()
    data_df['Model'] = data_df['Model'].ffill()
    data_df['Style'] = data_df['Style'].ffill()
    
    # Drop where Part or SKU is missing (actual data rows)
    # But some might be brand-only rows, we want to skip those
    data_df = data_df.dropna(subset=['Part', 'SKU'], how='all')
    data_df = data_df[data_df['Part'].notnull()]
    
    return data_df.where(pd.notnull(data_df), None).to_dict(orient='records')

def extract_hoods(xl):
    df = xl.parse('Changes HOODS ETC', header=None)
    # Header was found at index 2
    header_idx = 2
    data_df = xl.parse('Changes HOODS ETC', skiprows=header_idx + 1, header=None)
    
    # We only take the columns we care about
    # Col 0: Cat, Col 3: Model, Col 4: Style, Col 5: Size, Col 6: SKU, Col 9: Price (Cost USD)
    data_df = data_df.iloc[:, [0, 3, 4, 5, 6, 9]]
    data_df.columns = ['Category', 'Model', 'Style', 'Size', 'SKU', 'Price']
    
    # Ffill
    data_df['Category'] = data_df['Category'].ffill()
    data_df['Model'] = data_df['Model'].ffill()
    
    # Drop empty SKU/Style rows
    data_df = data_df.dropna(subset=['SKU', 'Style'], how='all')
    data_df = data_df[data_df['SKU'].notnull()]
    
    return data_df.where(pd.notnull(data_df), None).to_dict(orient='records')

kits_data = extract_kits(xl)
hoods_data = extract_hoods(xl)

final_data = {
    "kits": kits_data,
    "hoods": hoods_data,
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "counts": {
            "kits": len(kits_data),
            "hoods": len(hoods_data)
        }
    }
}

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2, default=str)

print(f'Successfully exported {len(kits_data)} kits and {len(hoods_data)} hoods items.')
