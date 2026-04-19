# project Analysis: Elite Ti - Wholesale Catalog

## Overview
The **Elite Ti Wholesale Catalog** is a high-performance, responsive web application designed to showcase automotive product data (Body Kits, Hoods, and Accessories) extracted from master inventory records. It features a premium "dark mode" aesthetic with advanced search and filtering capabilities.

## Architecture & Components

### 1. Data Processing Engine (`extract_data.py`)
- **Source**: Processes `Wholesale_GreenActive_Merged_Master_Revised_v2.0.xlsx`.
- **Logic**: 
    - Uses **Pandas** and **NumPy** for data manipulation.
    - Implements complex **Brand Resolution** logic: uses regex to identify car makes (e.g., NISSAN, BMW, TOYOTA) from model strings.
    - **Normalization**: Standardizes model names (e.g., "RX-8" to "RX8") and heals missing price data by converting from THB or extracting from other columns.
    - **Output**: Generates a unified `data.json` containing two main categories: `kits` and `hoods`.

### 2. Frontend Interface (`index.html` & `app.js`)
- **Tech Stack**: Vanilla Javascript, Tailwind CSS (via CDN), Google Fonts (Inter).
- **Design Philosophy**: 
    - **Glassmorphism & Micro-animations**: Modern, premium feel with sticky navigation and search bars.
    - **Responsive Design**: Mobile-optimized views using data-labels for table rows.
- **Key Features**:
    - **Dynamic Filtering**: Real-time filtering by Brand, Model, Style, Part, SKU, and Price Range.
    - **Global Search**: High-speed keyword matching across all product fields.
    - **State Management**: Handles category switching between "Body Kits" and "Hoods & Carbon" with automatic filter resets.

### 3. Data Structure (`data.json`)
The catalog is powered by a structured JSON file:
- **`kits`**: Contains records with fields: `Brand`, `Model`, `Style`, `Part`, `SKU`, `Price`, and `Dims`.
- **`hoods`**: Contains similar fields but extracted from a secondary worksheet with varying schemas.
- **Metadata**: Includes generation timestamps and count summaries.

## Workflow for Updates
To update the catalog when the master Excel file changes:
1. Replace the existing `.xlsx` file in the root directory.
2. Run the extraction script:
   ```bash
   python3 extract_data.py
   ```
3. Commit and deploy the updated `data.json`.

## Deployment
The project is architected as a static site, making it perfectly suited for:
- **GitHub Pages**
- **Vercel**
- **Netlify**

---
*Analysis generated on April 19, 2026.*
