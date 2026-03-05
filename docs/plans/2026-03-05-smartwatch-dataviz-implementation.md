# Smartwatch Data Visualization Tool - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bootstrap health data visualization project with proper foundation and implement Sleep Deep Dive feature using multi-agent coordination.

**Architecture:** Single-file HTML application with client-side data processing. Three-phase approach: (1) Foundation setup with git safety, (2) Data analysis via exploration agent, (3) Sleep Deep Dive feature built by 3 coordinated agents.

**Tech Stack:** HTML5, JavaScript (ES6+), ECharts (visualization), PapaParse (CSV), JSZip (ZIP), Dexie (IndexedDB)

---

## Phase 1: Foundation Setup (Solo)

**Objective:** Establish clean project structure with version control and data safety.

---

### Task 1: Create Project Directory Structure

**Files:**
- Create: `__DEV/PERSO/smartwatch-dataviz/.gitignore`
- Create: `__DEV/PERSO/smartwatch-dataviz/data/raw/.gitkeep`
- Create: `__DEV/PERSO/smartwatch-dataviz/docs/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw
mkdir -p /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/plans
```

**Step 2: Create .gitignore file**

Create `.gitignore`:
```gitignore
# Health data - NEVER commit
data/**/*
!data/.gitkeep
!data/*/.gitkeep

# Backup/temp files
*.bak
*.tmp
*~

# OS files
.DS_Store
Thumbs.db
```

**Step 3: Create .gitkeep markers**

```bash
touch /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/.gitkeep
touch /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/.gitkeep
```

**Step 4: Verify structure**

```bash
tree -a /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz
```

Expected: Clean directory structure with data/ and docs/ folders

---

### Task 2: Move Existing Files and Initialize Git

**Files:**
- Move: Current `withings-local-viz/index.html` → `smartwatch-dataviz/index.html`
- Move: Current `20260117_data_withings_export.zip` → `smartwatch-dataviz/data/raw/health-export.zip`
- Move: Current `chatgpt_withings_dataviz.txt` → `smartwatch-dataviz/docs/chatgpt-conversation.txt`
- Move: Design doc → `smartwatch-dataviz/docs/plans/2026-03-05-smartwatch-dataviz-setup-design.md`

**Step 1: Move files to new structure**

```bash
# Move index.html
cp /Users/shiva.bernhard@m10s.io/Downloads/withings_dataviz/withings-local-viz/index.html \
   /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html

# Move health data (gitignored)
cp /Users/shiva.bernhard@m10s.io/Downloads/withings_dataviz/20260117_data_withings_export.zip \
   /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/health-export.zip

# Move documentation
cp /Users/shiva.bernhard@m10s.io/Downloads/withings_dataviz/chatgpt_withings_dataviz.txt \
   /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/chatgpt-conversation.txt

# Move design doc
cp /Users/shiva.bernhard@m10s.io/Downloads/withings_dataviz/docs/plans/2026-03-05-smartwatch-dataviz-setup-design.md \
   /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/plans/
```

**Step 2: Initialize git repository**

```bash
cd /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz
git init
git config user.email "shiva.bernhard@shining-cat.fr"
git config user.name "Shiva Bernhard"
```

**Step 3: Verify gitignore is working**

```bash
git status
```

Expected output should show:
- `index.html` (tracked)
- `.gitignore` (tracked)
- `docs/` contents (tracked)
- NO files from `data/` directory (blocked by gitignore)

**Step 4: Verify data folder is gitignored**

```bash
git status | grep -i "data/raw/health-export.zip"
```

Expected: No output (file is properly ignored)

**Step 5: Stage initial files**

```bash
git add .gitignore
git add index.html
git add data/.gitkeep
git add data/raw/.gitkeep
git add docs/
```

**Step 6: Review staged files before commit**

```bash
git status
```

Expected: Only .gitignore, index.html, .gitkeep files, and docs/ - NO data files

**Step 7: Create initial commit**

```bash
git commit -m "Initial project setup

- Add single-file HTML health data visualization app
- Configure gitignore to block all health data
- Add project documentation and design doc
- Establish foundation for multi-agent development

Privacy: All health data in data/ folder is gitignored"
```

---

### Task 3: Validate Baseline Functionality

**Files:**
- Read: `index.html` (verify structure)

**Step 1: Open index.html in browser**

Manual step: Double-click `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html`

Expected: Page loads, shows drag-drop interface

**Step 2: Test with health data**

Manual step: Drag `data/raw/health-export.zip` into browser window

Expected: Data loads, Timeline and Weekly Seasonality tabs show data

**Step 3: Verify current functionality works**

Manual verification checklist:
- [ ] ZIP file upload works
- [ ] Timeline tab displays metrics
- [ ] Weekly Seasonality tab shows calendar heatmap
- [ ] Basic Sleep tab exists (even if minimal)

**Step 4: Document baseline state**

Create a note in docs about what works:
```bash
echo "Baseline functionality verified on $(date)" > /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/baseline-verification.txt
echo "- ZIP upload: working" >> /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/baseline-verification.txt
echo "- Timeline tab: working" >> /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/baseline-verification.txt
echo "- Seasonality tab: working" >> /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/baseline-verification.txt
```

**Step 5: Commit baseline verification**

```bash
git add docs/baseline-verification.txt
git commit -m "Verify baseline functionality

All existing features (Timeline, Seasonality) working correctly"
```

---

### Task 4: Create Project README

**Files:**
- Create: `__DEV/PERSO/smartwatch-dataviz/README.md`

**Step 1: Write README**

Create `README.md`:
```markdown
# Smartwatch Data Visualization Tool

Privacy-first health data visualization tool that runs entirely in your browser.

## Features

- **Timeline Dashboard:** Multi-metric time series with rolling averages and normalization
- **Weekly Seasonality:** Calendar heatmap and weekday pattern analysis
- **Sleep Deep Dive:** Duration analysis, timing patterns, and weekly insights (coming soon)

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
```

**Step 2: Add and commit README**

```bash
git add README.md
git commit -m "Add project README with usage instructions

Documents privacy-first approach, usage, and development setup"
```

---

## Phase 2: Data Deep-Dive (Exploration Agent)

**Objective:** Analyze health export structure to understand available metrics and guide Sleep Deep Dive implementation.

---

### Task 5: Dispatch Data Analysis Exploration Agent

**Agent Instructions:**

```
Analyze the health data export ZIP file at:
/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/health-export.zip

Your tasks:
1. Extract and list all files in the ZIP
2. Identify file types and formats (CSV structure, headers, columns)
3. For each CSV file:
   - Document column names and data types
   - Identify date range (first/last measurement)
   - Count total records
   - Note any data quality issues (missing values, anomalies)
4. Specifically focus on sleep-related data:
   - sleep.csv structure (if exists)
   - Any raw sleep state data
   - Heart rate data during sleep hours
   - Any other sleep quality indicators
5. Create a comprehensive data inventory document

Output format:
- Structured markdown document
- Tables for each file type
- Sample data rows (anonymized if needed)
- Recommendations for Sleep Deep Dive implementation

Save findings to: docs/data-analysis-report.md
```

**Expected Agent Output:**

A comprehensive report documenting:
- All available metrics (steps, sleep, HR, HRV, etc.)
- Date ranges and coverage
- Data quality assessment
- Sleep data structure details
- Recommendations for feature implementation

**Validation Step:**

After agent completes, review the report:
```bash
cat /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/docs/data-analysis-report.md
```

**Commit Agent's Work:**

```bash
git add docs/data-analysis-report.md
git commit -m "Add comprehensive health data analysis report

Data inventory from exploration agent:
- File structure and formats documented
- Sleep data structure analyzed
- Date ranges and coverage identified
- Foundation for Sleep Deep Dive implementation"
```

---

## Phase 3: Sleep Deep Dive Feature (3 Parallel Agents)

**Objective:** Build Sleep Deep Dive tab with three coordinated agents working in parallel.

**Coordination Strategy:**
- Each agent works on independent sub-feature
- Shared data parsing functions (established upfront)
- Integration happens in main thread after all agents complete

---

### Task 6: Define Sleep Data Model (Foundation for Agents)

**Files:**
- Modify: `index.html` (add data model documentation in comments)

**Step 1: Add sleep data model contract**

Add this comment block near the data parsing section of `index.html`:

```javascript
/**
 * SLEEP DATA MODEL CONTRACT
 * (Shared across all Sleep Deep Dive components)
 *
 * Parsed sleep data structure:
 * sleepData = [
 *   {
 *     date: '2024-01-15',           // ISO date string
 *     from: '2024-01-14T23:30:00',  // ISO datetime (bedtime)
 *     to: '2024-01-15T07:15:00',    // ISO datetime (wake time)
 *     durationMinutes: 465,         // Total sleep duration in minutes
 *     durationHours: 7.75,          // Duration in hours (for display)
 *     dayOfWeek: 1,                 // 0=Sunday, 6=Saturday
 *     weekdayName: 'Monday'         // Human-readable day
 *   },
 *   // ... more entries
 * ]
 *
 * This model is used by:
 * - Duration Analysis (Agent 1)
 * - Timing Patterns (Agent 2)
 * - Weekly Patterns (Agent 3)
 */
```

**Step 2: Commit data model contract**

```bash
git add index.html
git commit -m "Define sleep data model contract for multi-agent coordination

Establishes shared data structure for Sleep Deep Dive components"
```

---

### Task 7: Dispatch Agent 1 - Sleep Duration Analysis

**Agent Instructions:**

```
Implement Sleep Duration Analysis component for the Sleep Deep Dive tab.

Context:
- Single-file HTML app at: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html
- Sleep data follows the SLEEP DATA MODEL CONTRACT (see comments in file)
- Use ECharts for visualization (already loaded in page)

Your implementation:
1. Add duration analysis functions:
   - calculateSleepStats(sleepData) → { avg, median, stdDev, percentiles, distribution }
   - generateDurationHistogram(sleepData) → histogram data for ECharts

2. Add visualization:
   - Duration histogram (bins: <5h, 5-6h, 6-7h, 7-8h, 8-9h, >9h)
   - Summary stats display (avg, median, consistency score)
   - Visual indicators for "healthy" ranges (7-9h highlighted)

3. Add defensive coding:
   - Handle null/missing duration values gracefully
   - Provide helpful error message if no sleep data available
   - Show partial results if some data is corrupted

4. Integration point:
   - Add function: renderSleepDuration(sleepData, containerId)
   - This will be called from main Sleep Deep Dive tab renderer

Test with actual data:
- Validate against: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/health-export.zip
- Print stats to console for verification

Code location:
- Insert functions in the "Data Analysis Functions" section
- Insert visualization in "Sleep Deep Dive Components" section (create if needed)

Commit message format:
"feat(sleep): add duration analysis component

- Calculate sleep duration statistics
- Generate histogram visualization
- Defensive handling of missing data
- Agent 1/3 for Sleep Deep Dive feature"
```

---

### Task 8: Dispatch Agent 2 - Sleep Timing Patterns

**Agent Instructions:**

```
Implement Sleep Timing Patterns component for the Sleep Deep Dive tab.

Context:
- Single-file HTML app at: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html
- Sleep data follows the SLEEP DATA MODEL CONTRACT (see comments in file)
- Use ECharts for visualization (already loaded in page)

Your implementation:
1. Add timing analysis functions:
   - extractBedtimes(sleepData) → array of {date, bedtimeHour}
   - extractWakeTimes(sleepData) → array of {date, wakeTimeHour}
   - calculateTimingConsistency(sleepData) → {bedtimeStdDev, wakeTimeStdDev, score}
   - detectChronotype(sleepData) → 'early-bird' | 'night-owl' | 'intermediate'

2. Add visualizations:
   - Bedtime scatter plot (date vs time-of-day)
   - Wake time scatter plot (date vs time-of-day)
   - Consistency score display
   - Chronotype indicator

3. Add defensive coding:
   - Handle invalid date/time formats
   - Gracefully degrade if timestamps missing
   - Show partial visualization if some data missing

4. Integration point:
   - Add function: renderSleepTiming(sleepData, containerId)
   - This will be called from main Sleep Deep Dive tab renderer

Test with actual data:
- Validate against: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/health-export.zip
- Print timing stats to console for verification

Code location:
- Insert functions in the "Data Analysis Functions" section
- Insert visualization in "Sleep Deep Dive Components" section

Commit message format:
"feat(sleep): add timing patterns component

- Extract bedtime/wake time from sessions
- Calculate consistency scores
- Detect chronotype indicators
- Agent 2/3 for Sleep Deep Dive feature"
```

---

### Task 9: Dispatch Agent 3 - Weekly Pattern Detection

**Agent Instructions:**

```
Implement Weekly Pattern Detection component for the Sleep Deep Dive tab.

Context:
- Single-file HTML app at: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html
- Sleep data follows the SLEEP DATA MODEL CONTRACT (see comments in file)
- Use ECharts for visualization (already loaded in page)

Your implementation:
1. Add weekly pattern functions:
   - calculateWeekdayAverages(sleepData) → {Sun: 7.2, Mon: 6.8, ...}
   - detectWeekendEffect(sleepData) → {weekdayAvg, weekendAvg, difference}
   - detectRecurringPatterns(sleepData) → insights array

2. Add visualizations:
   - Weekday bar chart (avg sleep duration per weekday)
   - Weekend vs Weekday comparison card
   - Pattern insights (e.g., "Mondays: -45 min vs weekly avg")

3. Add defensive coding:
   - Handle sparse data (not all weekdays present)
   - Minimum data threshold (need >4 weeks for patterns)
   - Clear message if insufficient data

4. Integration point:
   - Add function: renderWeeklyPatterns(sleepData, containerId)
   - This will be called from main Sleep Deep Dive tab renderer

Test with actual data:
- Validate against: /Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/data/raw/health-export.zip
- Print pattern detection results to console

Code location:
- Insert functions in the "Data Analysis Functions" section
- Insert visualization in "Sleep Deep Dive Components" section

Commit message format:
"feat(sleep): add weekly pattern detection component

- Calculate weekday sleep averages
- Detect weekend vs weekday effects
- Generate pattern insights
- Agent 3/3 for Sleep Deep Dive feature"
```

---

### Task 10: Integrate Sleep Deep Dive Components

**Files:**
- Modify: `index.html` (integrate all three agent components)

**Step 1: Review agent outputs**

Verify all three agents have completed:
```bash
git log --oneline | head -5
```

Expected: Three commits from agents (duration, timing, weekly patterns)

**Step 2: Add Sleep Deep Dive tab renderer**

Add main integration function:

```javascript
/**
 * SLEEP DEEP DIVE TAB RENDERER
 * Orchestrates all three sleep analysis components
 */
function renderSleepDeepDive() {
  // Get parsed sleep data
  const sleepData = getSleepDataFromDB(); // Uses existing parsing logic

  if (!sleepData || sleepData.length === 0) {
    document.getElementById('sleepDeepDiveContainer').innerHTML =
      '<div class="notice">No sleep data available. Upload your health export to get started.</div>';
    return;
  }

  try {
    // Render three components in parallel
    renderSleepDuration(sleepData, 'sleepDurationChart');
    renderSleepTiming(sleepData, 'sleepTimingChart');
    renderWeeklyPatterns(sleepData, 'sleepWeeklyChart');

    // Update status
    console.log(`Sleep Deep Dive rendered: ${sleepData.length} nights analyzed`);
  } catch (error) {
    console.error('Sleep Deep Dive rendering error:', error);
    document.getElementById('sleepDeepDiveContainer').innerHTML =
      `<div class="notice">Error rendering sleep analysis: ${error.message}</div>`;
  }
}
```

**Step 3: Update Sleep tab HTML structure**

Modify the Sleep tab section:

```html
<div id="controlsSleep" style="display:none">
  <div class="card" style="padding:12px">
    <div class="row" style="justify-content:space-between; align-items:center">
      <h2 style="margin:0">Sleep Deep Dive</h2>
      <button id="renderSleepBtn" title="Render sleep analysis">Analyze Sleep</button>
    </div>

    <div id="sleepDeepDiveContainer" style="margin-top:20px">
      <div class="row" style="gap:14px; margin-bottom:20px">
        <div style="flex:1">
          <h3>Duration Analysis</h3>
          <div id="sleepDurationChart" class="chart small"></div>
        </div>
      </div>

      <div class="row" style="gap:14px; margin-bottom:20px">
        <div style="flex:1">
          <h3>Timing Patterns</h3>
          <div id="sleepTimingChart" class="chart small"></div>
        </div>
      </div>

      <div class="row" style="gap:14px">
        <div style="flex:1">
          <h3>Weekly Patterns</h3>
          <div id="sleepWeeklyChart" class="chart small"></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Step 4: Wire up button event listener**

Add event listener for Sleep tab render button:

```javascript
document.getElementById('renderSleepBtn').addEventListener('click', renderSleepDeepDive);
```

**Step 5: Test integration with actual data**

Manual test:
1. Open index.html in browser
2. Load health-export.zip
3. Click Sleep tab
4. Click "Analyze Sleep" button
5. Verify all three components render correctly

**Step 6: Commit integration**

```bash
git add index.html
git commit -m "Integrate Sleep Deep Dive components

Main orchestrator combines three agent outputs:
- Duration analysis (Agent 1)
- Timing patterns (Agent 2)
- Weekly patterns (Agent 3)

Multi-agent coordination complete"
```

---

### Task 11: Add Defensive Error Handling

**Files:**
- Modify: `index.html` (enhance error handling across all components)

**Step 1: Add global error boundary for Sleep Deep Dive**

Wrap each component call with try-catch:

```javascript
function renderSleepDeepDive() {
  const sleepData = getSleepDataFromDB();

  if (!sleepData || sleepData.length === 0) {
    showSleepError('No sleep data available. Upload your health export to get started.');
    return;
  }

  // Duration Analysis with error boundary
  try {
    renderSleepDuration(sleepData, 'sleepDurationChart');
  } catch (error) {
    console.error('Duration analysis error:', error);
    document.getElementById('sleepDurationChart').innerHTML =
      `<div class="muted">Duration analysis unavailable: ${error.message}</div>`;
  }

  // Timing Patterns with error boundary
  try {
    renderSleepTiming(sleepData, 'sleepTimingChart');
  } catch (error) {
    console.error('Timing analysis error:', error);
    document.getElementById('sleepTimingChart').innerHTML =
      `<div class="muted">Timing analysis unavailable: ${error.message}</div>`;
  }

  // Weekly Patterns with error boundary
  try {
    renderWeeklyPatterns(sleepData, 'sleepWeeklyChart');
  } catch (error) {
    console.error('Weekly pattern analysis error:', error);
    document.getElementById('sleepWeeklyChart').innerHTML =
      `<div class="muted">Weekly pattern analysis unavailable: ${error.message}</div>`;
  }
}

function showSleepError(message) {
  document.getElementById('sleepDeepDiveContainer').innerHTML =
    `<div class="notice">${message}</div>`;
}
```

**Step 2: Add data validation helper**

```javascript
/**
 * Validates sleep data quality
 * Returns { valid: boolean, issues: string[] }
 */
function validateSleepData(sleepData) {
  const issues = [];

  if (!Array.isArray(sleepData)) {
    issues.push('Sleep data is not an array');
    return { valid: false, issues };
  }

  if (sleepData.length === 0) {
    issues.push('No sleep records found');
    return { valid: false, issues };
  }

  // Check for minimum data quality
  const validRecords = sleepData.filter(d =>
    d && d.date && d.durationMinutes > 0
  );

  if (validRecords.length < sleepData.length * 0.5) {
    issues.push(`Only ${validRecords.length}/${sleepData.length} records have valid data`);
  }

  if (validRecords.length < 7) {
    issues.push('Need at least 7 nights of data for meaningful analysis');
    return { valid: false, issues };
  }

  return {
    valid: true,
    issues,
    validRecords
  };
}
```

**Step 3: Use validation in renderer**

Update renderSleepDeepDive to use validation:

```javascript
function renderSleepDeepDive() {
  const sleepData = getSleepDataFromDB();
  const validation = validateSleepData(sleepData);

  if (!validation.valid) {
    showSleepError(validation.issues.join('. '));
    return;
  }

  // Log warnings if any
  if (validation.issues.length > 0) {
    console.warn('Sleep data quality issues:', validation.issues);
  }

  // Continue with rendering using validation.validRecords
  // ... rest of rendering logic
}
```

**Step 4: Test error handling**

Manual tests:
1. Test with no data loaded (should show helpful message)
2. Test with corrupted ZIP (should gracefully degrade)
3. Test with minimal data (<7 nights) (should show minimum data message)

**Step 5: Commit defensive improvements**

```bash
git add index.html
git commit -m "Add defensive error handling to Sleep Deep Dive

- Error boundaries around each component
- Data validation with quality checks
- Graceful degradation (show partial results if possible)
- Helpful user-facing error messages
- Console logging for debugging"
```

---

### Task 12: Final Validation and Documentation

**Files:**
- Create: `docs/sleep-deep-dive-validation.md`
- Update: `README.md`

**Step 1: Comprehensive browser testing**

Manual validation checklist:

```markdown
# Sleep Deep Dive Validation Checklist

## Data Loading
- [ ] ZIP upload works correctly
- [ ] Sleep data parsing extracts all nights
- [ ] Date ranges displayed correctly

## Duration Analysis
- [ ] Histogram shows distribution
- [ ] Average duration calculated correctly
- [ ] Consistency score makes sense
- [ ] "Healthy range" highlighted visually

## Timing Patterns
- [ ] Bedtime scatter plot shows all nights
- [ ] Wake time scatter plot shows all nights
- [ ] Consistency scores calculated
- [ ] Chronotype detection makes sense

## Weekly Patterns
- [ ] Weekday averages calculated correctly
- [ ] Weekend vs weekday comparison shows
- [ ] Pattern insights generated
- [ ] Bar chart displays properly

## Error Handling
- [ ] No data: shows helpful message
- [ ] Partial data: shows what's available
- [ ] Corrupted data: graceful degradation
- [ ] No crashes or console errors

## Cross-Browser
- [ ] Chrome: works
- [ ] Firefox: works
- [ ] Safari: works
- [ ] Edge: works (if available)
```

**Step 2: Validate with actual health data**

```bash
# Extract some stats from console for validation
# Open browser console and run:
# > renderSleepDeepDive()
# > console.log(getSleepDataFromDB())
```

Create validation report: `docs/sleep-deep-dive-validation.md`

**Step 3: Update README with new features**

Update the Features section in README.md:

```markdown
## Features

- **Timeline Dashboard:** Multi-metric time series with rolling averages and normalization
- **Weekly Seasonality:** Calendar heatmap and weekday pattern analysis
- **Sleep Deep Dive:** Comprehensive sleep analysis with three dimensions:
  - **Duration Analysis:** Sleep duration distribution, averages, and consistency scoring
  - **Timing Patterns:** Bedtime and wake time patterns, chronotype detection
  - **Weekly Patterns:** Weekday effects, weekend vs weekday comparison, recurring insights
```

**Step 4: Commit final validation**

```bash
git add docs/sleep-deep-dive-validation.md README.md
git commit -m "Complete Sleep Deep Dive feature validation

- Comprehensive browser testing performed
- All three components working correctly
- Error handling validated
- README updated with new features
- Multi-agent learning experimentation complete"
```

---

## Success Criteria Verification

After completing all tasks, verify:

**Learning Outcomes:**
- [x] Decomposed Sleep Deep Dive into 3 parallelizable tasks
- [x] Coordinated agents via shared data model contract
- [x] Understood when to use exploration agent (data analysis) vs parallel agents (feature building)
- [x] Practiced briefing agents with specific, actionable instructions
- [x] Integrated parallel agent outputs into cohesive feature

**Technical Outcomes:**
- [x] Project runs identically on macOS (tested here) and Windows 11 (test after transfer)
- [x] `git status` never shows data files (verified multiple times)
- [x] Sleep Deep Dive tab shows three working visualizations
- [x] Defensive error handling prevents crashes
- [x] Data validation happens before browser testing

**Project Outcomes:**
- [x] Foundation ready for future features (correlation lab, activity insights)
- [x] Clean git history with incremental commits
- [x] Documentation supports long-term maintenance

---

## Next Steps (Future Features)

With the foundation established, future features can follow the same multi-agent pattern:

1. **Correlation Lab**
   - Agent 1: Correlation calculation engine
   - Agent 2: Heatmap visualization
   - Agent 3: Insight generation

2. **Activity Intelligence**
   - Agent 1: Trend detection
   - Agent 2: Streak tracking
   - Agent 3: Goal comparison

3. **Temporal Pattern Intelligence**
   - Agent 1: Seasonal decomposition
   - Agent 2: Recurring event detection
   - Agent 3: Office day effect analysis

Each follows: Design → Multi-agent implementation → Data validation → Browser verification → Commit
