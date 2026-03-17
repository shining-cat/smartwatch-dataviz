# Smartwatch Data Visualization Tool

Privacy-first health data visualization tool that runs entirely in your browser.

## Features

### 📊 Activity Dashboard
- **Daily Steps:** Time series visualization with weekly patterns and trend indicators
- **Workout Overview:**
  - Activity type distribution (running, cycling, swimming, etc.)
  - Workout frequency and duration trends
  - Calendar heatmap showing workout intensity over time
- **Weekly Patterns:** Weekday vs weekend activity comparisons
- **Distance & Elevation:** Total metrics with visual breakdowns

### 😴 Sleep Analysis
- **Duration Tracking:** Sleep duration trends, averages, and healthy range indicators
- **Timing Patterns:** Bedtime and wake time consistency with chronotype detection
- **Weekly Insights:** Weekday effects and recurring pattern analysis
- **Nap Filtering:** Toggle to include/exclude naps from analysis
- **Visual Indicators:** Color-coded duration charts and comparison bars

### 💡 Correlation Discovery (Insights)
- **Pattern Detection:** Analyzes 9 metric pairs to find relationships between sleep and activity
- **Smart Organization:**
  - Top 3 strongest discoveries highlighted
  - Sleep-focused insights (70% weight)
  - Activity insights (30% weight)
- **Statistical Rigor:**
  - Pearson correlation with confidence indicators
  - Percentile-based comparisons (Low/Medium/High)
  - Minimum 14 days of overlapping data required
- **Interactive Visualizations:** Expandable scatter plots with trend lines
- **Transparent Results:** Shows all calculations even when patterns are weak
- **Educational Context:** "Correlation ≠ Causation" disclaimer and research insights

### 📈 Timeline Dashboard
- Multi-metric time series with rolling averages and normalization

## Recent Enhancements

**March 2026:**
- ✨ **New: Correlation Discovery Engine** - Automatically finds patterns between sleep and activity
- ✨ **New: Activity Dashboard** - Comprehensive workout and step tracking with weekly patterns
- 🔧 **Enhanced: Sleep Analysis** - Added nap filtering, improved chronotype detection, visual indicators
- 📊 **Improved: Data Visualization** - Interactive scatter plots, calendar heatmaps, trend indicators
- 🎨 **UX: Transparent Results** - Shows analysis details even when correlations are weak

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
   - Switch between Activity, Sleep, Insights, and Timeline tabs
   - Toggle nap filtering in Sleep tab
   - Discover correlations between your metrics in Insights tab
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
