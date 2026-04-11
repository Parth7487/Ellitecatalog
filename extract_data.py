import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

excel_path = 'Wholesale_GreenActive_Merged_Master_Revised_v2.0.xlsx'
output_json = 'data.json'

os.makedirs('public', exist_ok=True)

xl = pd.ExcelFile(excel_path)

COMMON_BRANDS = {'AUDI', 'ASTON MARTIN', 'BMW', 'BENZ', 'HONDA', 'TOYOTA', 'MAZDA', 'SUBARU', 'MITSUBISHI', 'NISSAN', 'FORD', 'HYUNDAI', 'KIA', 'LEXUS', 'PORSCHE', 'VOLKSWAGEN', 'VW', 'SUZUKI', 'CHEVROLET', 'FERRARI', 'LAMBORGHINI', 'MCLAREN'}

import re

BRAND_MAPPING = {
    # NISSAN
    "350Z": "NISSAN", "35OZ": "NISSAN", "370Z": "NISSAN", 
    "R32": "NISSAN", "R33": "NISSAN", "R34": "NISSAN", "R35": "NISSAN", "GTR": "NISSAN",
    "GTR R35": "NISSAN", "SKYLINE": "NISSAN", "S13": "NISSAN", "S14": "NISSAN", 
    "S15": "NISSAN", "200SX": "NISSAN", "180SX": "NISSAN", "SILVIA": "NISSAN", "A31": "NISSAN",
    "CEFIRO": "NISSAN", "NAVARA": "NISSAN", "JUKE": "NISSAN", "MARCH": "NISSAN",
    
    # MAZDA
    "RX8": "MAZDA", "RX-8": "MAZDA", "RX7": "MAZDA", "RX-7": "MAZDA", 
    "MAZDA3": "MAZDA", "MAZDA 3": "MAZDA", "MAZDA2": "MAZDA", "MAZDA 2": "MAZDA", "MX5": "MAZDA",
    
    # HONDA
    "JAZZ": "HONDA", "CIVIC": "HONDA", "CITY": "HONDA", "ACCORD": "HONDA", 
    "S2000": "HONDA", "S 2000": "HONDA", "PRELUDE": "HONDA", "CRV": "HONDA", 
    "CRZ": "HONDA", "BRIO": "HONDA", "DC5": "HONDA", "DC2": "HONDA", "DIMENTION": "HONDA",
    "EK9": "HONDA", "EK99": "HONDA", "EG": "HONDA", "EP3": "HONDA", "FD": "HONDA", "FB": "HONDA", "FC": "HONDA", "FK": "HONDA",
    
    # TOYOTA
    "SUPRA": "TOYOTA", "86": "TOYOTA", "FT86": "TOYOTA", "GT86": "TOYOTA", "YARIS": "TOYOTA",
    "VIOS": "TOYOTA", "CAMRY": "TOYOTA", "ALTIS": "TOYOTA", "FORTUNER": "TOYOTA", "VIGO": "TOYOTA",
    "REVO": "TOYOTA", "ALPHARD": "TOYOTA", "VEILFIRE": "TOYOTA", "MAJESTY": "TOYOTA",
    "MR2": "TOYOTA", "MRS": "TOYOTA", "CELICA": "TOYOTA", "CELIGA": "TOYOTA", "ARISTO": "TOYOTA",
    "CHASER": "TOYOTA", "CHAISER": "TOYOTA", "MARK 2": "TOYOTA", "SOARER": "TOYOTA", "ALTEZZA": "TOYOTA",
    "LAND CRUISER": "TOYOTA", "LANDCRUESER": "TOYOTA",

    # MITSUBISHI
    "EVO": "MITSUBISHI", "EVO6": "MITSUBISHI", "EVO7": "MITSUBISHI", "EVO8": "MITSUBISHI", "EVO9": "MITSUBISHI", "EVO10": "MITSUBISHI",
    "LANCER": "MITSUBISHI", "GTO": "MITSUBISHI", "FTO": "MITSUBISHI",
    "TRITON": "MITSUBISHI", "SPACE WAGON": "MITSUBISHI", "SPACEWAGON": "MITSUBISHI", "COLT": "MITSUBISHI",

    # SUBARU
    "WRX": "SUBARU", "STI": "SUBARU", "BRZ": "SUBARU", "GC8": "SUBARU", "GDB": "SUBARU", "LEGACY": "SUBARU",

    # FORD
    "FIESTA": "FORD", "FISTA": "FORD", "MUSTANG": "FORD", "RANGER": "FORD",

    # CHEVROLET
    "COLORADO": "CHEVROLET", "COROLADO": "CHEVROLET", "OPTRA": "CHEVROLET", "AVEO": "CHEVROLET", "CORVETTE": "CHEVROLET",

    # PORSCHE
    "911": "PORSCHE", "718": "PORSCHE", "981": "PORSCHE", "997": "PORSCHE", "996": "PORSCHE", 
    "991": "PORSCHE", "CAYANNE": "PORSCHE", "CAYENNE": "PORSCHE", "BOXSTER": "PORSCHE", "CAYMAN": "PORSCHE",
    "MACAN": "PORSCHE", "TAYCAN": "PORSCHE", "PANAMERA": "PORSCHE", "GT2": "PORSCHE", "GT3": "PORSCHE",

    # BENTLEY
    "BENTLEY": "BENTLEY", "CONTINENTAL": "BENTLEY", "CONTINETAL": "BENTLEY",

    # BMW
    "E30": "BMW", "E36": "BMW", "E46": "BMW", "E90": "BMW", "E92": "BMW", "E93": "BMW",
    "F30": "BMW", "F32": "BMW", "F10": "BMW", "F12": "BMW", "G30": "BMW", "I8": "BMW",
    "Z4": "BMW", "E89": "BMW", "M3": "BMW", "M4": "BMW", "M5": "BMW",
    
    # MERCEDES
    "W140": "BENZ", "W129": "BENZ", "W205": "BENZ", "W209": "BENZ", "W211": "BENZ",
    "W212": "BENZ", "W220": "BENZ", "SL": "BENZ", "SLR": "BENZ", "CLS": "BENZ", "C-CLASS": "BENZ", "S-CLASS": "BENZ",

    # FERRARI
    "488": "FERRARI", "599": "FERRARI", "F430": "FERRARI",

    # LAMBORGHINI
    "AVENTADOR": "LAMBORGHINI", "HURACAN": "LAMBORGHINI", "HULACAN": "LAMBORGHINI", "GALLARDO": "LAMBORGHINI", "GALLADOR": "LAMBORGHINI", 
    "GALLARDOR": "LAMBORGHINI", "SUPERLEGA": "LAMBORGHINI",

    # MCLAREN
    "720S": "MCLAREN", "650S": "MCLAREN",

    # ASTON MARTIN
    "VANTAGE": "ASTON MARTIN", "VANTENGE": "ASTON MARTIN",

    # MINI
    "R53": "MINI", "R56": "MINI", "F55": "MINI", "F56": "MINI", "COOPER": "MINI"
}

def resolve_brand(brand, model):
    if not model: return brand
    m = str(model).upper()
    for key, correct_brand in BRAND_MAPPING.items():
        if re.search(r'\b' + re.escape(key) + r'\b', m) or key == m:
            return correct_brand
    return brand

MODEL_NORMS = {
    "RX-8": "RX8",
    "RX-7": "RX7",
    "CONTINETAL GT": "CONTINENTAL GT",
    "CONTINETAL GTC": "CONTINENTAL GTC",
    "LANDCRUESER": "LAND CRUISER",
    "CHAISER JP 95-00": "CHASER JP 95-00",
    "GT-WING E36": "E36",
    "R8 (WING E36)": "E36"
}

def normalize_model(model):
    if not model or pd.isna(model): return model
    m_str = str(model).strip()
    # Replace if exact match (case insensitive map check)
    for k, v in MODEL_NORMS.items():
        if m_str.upper() == k.upper():
            return v
    return m_str

def clean_val(v):
    if pd.isna(v) or v is None: return None
    try:
        if np.isnan(v) or np.isinf(v): return None
    except: pass
    return v

def extract_kits(xl):
    df = xl.parse('Changes Kits', header=None)
    header_idx = 5
    data_df = xl.parse('Changes Kits', skiprows=header_idx + 1, header=None)
    data_df.columns = ['Brand', 'Model', 'Style', 'Part', 'SKU', 'Price', 'Dims']
    
    data_df['Brand'] = data_df['Brand'].ffill()
    data_df['Model'] = data_df['Model'].ffill()
    data_df['Style'] = data_df['Style'].ffill()
    
    def heal_row(row):
        price = row['Price']
        sku = row['SKU']
        if (pd.isna(price) or str(price).strip().lower() == 'nan') and pd.notna(sku):
            try:
                float_val = float(sku)
                row['Price'] = float_val
                row['SKU'] = None
            except: pass
        return row

    data_df = data_df.apply(heal_row, axis=1)
    data_df = data_df.dropna(subset=['Part', 'Price'], how='all')
    data_df = data_df[data_df['Part'].notnull()]
    
    # Strict NaN to None convert
    records = []
    for r in data_df.to_dict(orient='records'):
        # Normalize the model string before proceeding
        normalized_mod = normalize_model(r.get('Model'))
        r['Model'] = normalized_mod
        
        brand = resolve_brand(r.get('Brand'), normalized_mod)
        r['Brand'] = clean_val(brand)
        records.append({k: clean_val(v) for k, v in r.items()})
    return records

def extract_hoods(xl):
    df = xl.parse('Changes HOODS ETC', header=None)
    rows = []
    current_brand = "OTHER"
    current_cat = "HOOD"
    
    for i, row in df.iterrows():
        if i < 3: continue
        r_list = list(row.values)
        r0 = str(r_list[0]).strip().upper() if pd.notna(r_list[0]) else ""
        r1 = str(r_list[1]).strip().upper() if pd.notna(r_list[1]) else ""
        
        if r0 in COMMON_BRANDS: current_brand = r0
        elif r1 in COMMON_BRANDS: current_brand = r1
            
        if r0 in ["HOOD", "SPOILER", "MIRROR", "ACC", "FENDER", "BONNET", "LIP", "DIFFUSER"]:
            current_cat = r0
            
        if i >= 1000:
            # Secondary Schema
            model = r_list[1]
            if pd.notna(model) and str(model).strip() != "":
                sku = None
                style = r_list[2]
                current_cat = r_list[3] if pd.notna(r_list[3]) else r_list[2]
                price = r_list[4]
                
                rows.append({
                    "Brand": current_brand,
                    "Model": model,
                    "Style": style,
                    "Part": current_cat,
                    "SKU": sku,
                    "Price": price
                })
        else:
            # Primary Schema
            model = r_list[3]
            if pd.notna(model) and str(model).strip() != "":
                sku = r_list[6]
                price = r_list[9]
                
                # Heal zero or missing prices based on Wholesale (Col 8) or Retail (Col 7) THB prices
                if pd.isna(price) or str(price).strip().lower() == 'nan' or price == 0:
                    if pd.notna(r_list[8]) and r_list[8] != 0:
                        try: price = float(r_list[8]) / 33.0
                        except: pass
                    elif pd.notna(r_list[7]) and r_list[7] != 0:
                        try: price = (float(r_list[7]) * 0.7) / 33.0
                        except: pass
                
                # Further healing on SKU column if still no price
                if (pd.isna(price) or str(price).strip().lower() == 'nan' or price == 0) and pd.notna(sku):
                     try: 
                         price = float(sku)
                         sku = None
                     except: pass
                
                rows.append({
                    "Brand": current_brand,
                    "Model": model,
                    "Style": r_list[4],
                    "Part": current_cat,
                    "SKU": sku,
                    "Price": price
                })
            
    df_res = pd.DataFrame(rows)
    df_res['Model'] = df_res['Model'].ffill()
    
    records = []
    for r in df_res.to_dict(orient='records'):
        normalized_mod = normalize_model(r.get('Model'))
        r['Model'] = normalized_mod
        
        brand = resolve_brand(r.get('Brand'), normalized_mod)
        r['Brand'] = clean_val(brand)
        records.append({k: clean_val(v) for k, v in r.items()})
    return records

kits_data = extract_kits(xl)
hoods_data = extract_hoods(xl)

final_data = {
    "kits": kits_data,
    "hoods": hoods_data,
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "counts": {"kits": len(kits_data), "hoods": len(hoods_data)}
    }
}

with open(output_json, 'w', encoding='utf-8') as f:
    # Use allow_nan=False to force error in python if NaN sneaks in, 
    # ensuring we never push a broken file
    json.dump(final_data, f, ensure_ascii=False, indent=2, default=str, allow_nan=False)

print(f"Success! Cleaned and exported {len(kits_data)} kits and {len(hoods_data)} hoods.")
