# Smartwatch Data Visualization Tool

Privacy-first health data visualization tool that runs entirely in your browser.

## Features

- **Timeline Dashboard:** Multi-metric time series with rolling averages and normalization
- **Weekly Seasonality:** Calendar heatmap and weekday pattern analysis
- **Sleep Deep Dive:** Comprehensive sleep analysis with three components:
  - **Duration Analysis:** Sleep duration distribution, averages, consistency scoring, and healthy range highlighting
  - **Timing Patterns:** Bedtime/wake time consistency, chronotype detection (early-bird/night-owl/intermediate)
  - **Weekly Patterns:** Weekday effects, weekend vs weekday comparison, recurring pattern insights

## How to Use

1. **Place your health data export** in `data/raw/` directory
   - The ZIP file from your smartwatch health export
   - This folder is gitignored - data never leaves your machine

2. **Open the app**
   - Double-click `index.html` to open in browser
   - No server needed, no installation required

3. **Load your data**
   - Drag and drop your ZIP file into the browser window
   - Or click "Choose ZIP" to select the file

4. **Explore your health data**
   - Switch between Timeline, Seasonality, and Sleep tabs
   - Select metrics to visualize
   - All processing happens locally in your browser

## Privacy & Data Safety

- **100% client-side:** All data processing happens in your browser
- **No uploads:** Your health data never leaves your machine
- **No tracking:** No analytics, no external requests (except CDN libraries)
- **Git-safe:** The `data/` folder is gitignored - health data never committed

## Portability

Works on macOS, Windows, and Linux - just needs a modern browser (Chrome, Firefox, Safari, Edge).

## Development

See `docs/plans/` for design documents and implementation plans.

### Git Setup

This project uses PERSO git configuration:
- Email: shiva.bernhard@shining-cat.fr
- All health data in `data/` is gitignored

### Project Structure

```
smartwatch-dataviz/
├── index.html          # Single-file app
├── data/               # .gitignored - your health data
│   └── raw/
│       └── health-export.zip
├── docs/               # Documentation and plans
│   └── plans/
└── README.md
```

## Tech Stack

- HTML5, JavaScript (ES6+)
- ECharts (visualization)
- PapaParse (CSV parsing)
- JSZip (ZIP extraction)
- Dexie (IndexedDB storage)

## License

Personal project - not licensed for distribution.
