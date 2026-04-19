# Bugs & Proposed Fixes: Elite Ti Catalog

This document outlines the identified issues in the current data extraction and frontend implementation, along with recommended technical solutions.

## 1. Data Accuracy (High Priority)

### [BUG] Hardcoded Exchange Rate
- **Issue**: Prices converted from THB are hardcoded using a `/ 33.0` factor in `extract_data.py`.
- **Impact**: Prices are currently undervalued by ~5-8% compared to real-time rates.
- **Proposed Fix**: 
    - Move `EXCHANGE_RATE` to a constant at the top of the file.
    - (Optional) Use a simple API fetch to get the current THB/USD rate during extraction.

### [BUG] Brittle forward-fill logic (`ffill`)
- **Issue**: The script relies on Pandas `ffill()` to propagate Brands and Models across rows.
- **Impact**: Misaligned or blank rows in Excel cause products to be assigned to the wrong manufacturer.
- **Proposed Fix**: 
    - Implement a validation step in `extract_data.py` that cross-references the Style/Model against a known brand database.
    - Log a warning when a "resolved brand" differs from an "ffilled brand".

---

## 2. Technical Stability (Medium Priority)

### [BUG] Zero-Price Records
- **Issue**: 9+ records discovered with `"Price": 0`.
- **Impact**: Products appear as "Free" in the catalog, which is incorrect for wholesale.
- **Proposed Fix**: 
    - Update `extract_data.py` to flag price-less rows as `null` or filter them out.
    - Add a "Price on Request" fallback in `app.js` for items with price `0` or `null`.

### [BUG] Potential Layout Thrashing (Performance)
- **Issue**: The entire table (1000+ rows) is re-rendered on every keystroke in the search bar.
- **Impact**: Laggy experience on mobile devices.
- **Proposed Fix**: 
    - Implement a **Debounce** function (250ms delay) in `app.js` so filtering only triggers after the user pauses typing.

---

## 3. UI/UX Improvements (Low Priority)

### [ISSUE] Accessibility & Readability
- **Issue**: Base font size is `11px` and `10px` for headers.
- **Impact**: Not compliant with mobile accessibility standards; hard to read on phones.
- **Proposed Fix**: 
    - Update `index.html` CSS to use `12px` or `13px` for body text and `11px` bold for headers.

### [ISSUE] XSS Vulnerability
- **Issue**: Data from JSON is injected via `.innerHTML`.
- **Impact**: Security risk if source data is compromised.
- **Proposed Fix**: 
    - Replace template literals with a more secure DOM construction method or sanitization helper.

---

## Next Steps
Please review these items. Once confirmed, I can apply these fixes to:
1. `extract_data.py` (Price logic and brand validation)
2. `index.html` (Styling and accessibility)
3. `app.js` (Debouncing and security)
