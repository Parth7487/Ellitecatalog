# Elite Ti - Wholesale Catalog

A functional, responsive catalog for Elite Ti wholesale pricing, extracted from master Excel records.

## Features
- **Live Search**: Search by Part, SKU, Model, or Brand.
- **Filtering**: Category-specific filtering (Changes Kits vs HOODS & ACC).
- **Brand Filtering**: Easily navigate by Car Brand or Component Category.
- **Wholesale Sorting**: Sort by price or model name.
- **Premium Design**: Dark mode aesthetic with glassmorphism and micro-animations.

## Tech Stack
- **Frontend**: Vanilla JS, Tailwind CSS (CDN), HTML5.
- **Data Engine**: Python (Pandas) for Excel extraction to JSON.
- **Hosting**: Optimized for Vercel / GitHub Pages.

## Deployment
This project is ready to be pushed to GitHub and deployed on Vercel:
1. Initialize git: `git init`
2. Add files: `git add .`
3. Commit: `git commit -m "Initial catalog commit"`
4. Push to your GitHub repo.
5. Import into Vercel as a **Static Project**.

## Updating Data
If the master Excel file is updated:
1. Replace `Wholesale_GreenActive_Merged_Master_Revised_v2.0.xlsx` in the root.
2. Run `python3 extract_data.py`.
3. Commit the updated `data.json`.
