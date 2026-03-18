# Smartwatch Data Visualization

**Understand your health data without compromising your privacy.**

A browser-based tool that analyzes your smartwatch health export (sleep, activity, workouts) to uncover patterns and insights. All processing happens locally on your machine - your health data never leaves your computer.

## What You Get

**📊 Activity Insights**
- Step count trends and weekly patterns
- Workout analysis by type (running, cycling, swimming, etc.)
- Calendar heatmap showing your most active periods
- Distance and elevation tracking

**😴 Sleep Analysis**
- Duration trends with healthy range indicators
- Bedtime and wake time consistency tracking
- Chronotype detection (are you an early bird or night owl?)
- Weekly pattern comparison (weekdays vs weekends)
- Nap filtering option

**💡 Pattern Discovery**
- Automatically finds correlations between sleep, activity, and heart rate metrics
- Detects weekend vs weekday patterns and day-of-week trends
- Shows how relationships vary by context (e.g., "Steps → Sleep stronger on weekdays")
- Statistical analysis with easy-to-understand visualizations
- Transparent results - shows what was analyzed even when no patterns are found

**📈 Timeline View**
- Multi-metric time series with rolling averages
- Compare different health metrics over time

## Privacy First

🔒 **Your health data stays on your computer. Period.**

- **No uploads:** Data never leaves your machine
- **No tracking:** No analytics, no external requests
- **100% local processing:** Everything runs in your browser
- **Open source:** Single HTML file - you can inspect exactly what it does

The only external requests are for JavaScript libraries (ECharts, etc.) loaded from CDN. Your health data is never transmitted anywhere.

## How to Use

### 1. Get Your Health Data Export

Export your health data from your smartwatch as a ZIP file. Place it anywhere on your computer (or use the `data/raw/` folder in this project).

### 2. Run a Local Web Server

**Why?** Modern browsers block local file access for security. You need a simple web server.

**Easiest option - Python (built into macOS/Linux):**
```bash
# Navigate to this project folder
cd /path/to/smartwatch-dataviz

# Start a web server
python3 -m http.server 8000

# Or if you have Python 2:
python -m SimpleHTTPServer 8000
```

**Other options:**
- **Node.js:** `npx http-server`
- **VS Code:** Install "Live Server" extension and click "Go Live"
- **Any other local web server** works fine

### 3. Open the App

Open your browser and go to:
```
http://localhost:8000
```

### 4. Load Your Data

1. Click **"Choose ZIP"** or drag-and-drop your health export ZIP file
2. Wait for processing (first load takes a moment to parse and store data)
3. Explore your dashboards:
   - **Activity** - Steps, workouts, calendar heatmap
   - **Sleep** - Duration, timing, patterns (toggle nap filtering)
   - **Insights** - Discover correlations between metrics
   - **Timeline** - Multi-metric time series

**Note:** Your data is stored in browser IndexedDB. It persists between sessions but stays local to your machine.

## Technical Details

**Single-file architecture:** Everything is in `index.html` - no build process, no dependencies to install.

**Tech stack:**
- HTML5 + JavaScript (ES6+)
- ECharts (interactive charts)
- PapaParse (CSV parsing)
- JSZip (ZIP extraction)
- Dexie (IndexedDB wrapper)

**Browser requirements:** Modern browser (Chrome, Firefox, Safari, Edge) with JavaScript enabled.

## Project Structure

```
smartwatch-dataviz/
├── index.html          # Single-file app (all code here)
├── data/               # .gitignored - place your health export here
│   └── raw/
├── docs/               # Design documents and implementation plans
└── README.md
```

## Troubleshooting

**"Failed to load data"**
- Make sure you're running through a web server (not opening `index.html` directly)
- Check browser console for errors

**"No patterns found" in Insights tab**
- You need at least 14 days of overlapping sleep and activity data
- If you have enough data but correlations are weak, the tool will show what was analyzed

**Data not persisting**
- Browser IndexedDB might be cleared if you clear browser data
- Keep your original ZIP export as backup

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You are free to use, modify, and distribute this software under the terms of the GPL-3.0.
See the [LICENSE](LICENSE) file for details, or visit https://www.gnu.org/licenses/gpl-3.0.html
