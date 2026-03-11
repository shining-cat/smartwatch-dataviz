# Sleep Tab Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add nap filtering, Y-axis reorientation, and color-coded duration to Sleep tab bedtime chart

**Architecture:** Add skip naps checkbox to sleep controls, implement nap filtering in data pipeline, transform bedtime chart with 12:00-11:59 Y-axis and duration-based dot colors, remove render button for auto-render UX

**Tech Stack:** Vanilla JavaScript, ECharts (scatter chart), IndexedDB (Dexie), single-file HTML app

---

## Task 1: Add Skip Naps Checkbox to HTML

**Files:**
- Modify: `index.html` (sleep controls section, ~lines 113-133)

**Step 1: Locate sleep controls section**

Find the sleep controls div (around line 113):
```html
<div id="controlsSleep" style="display:none">
  <div class="card" style="padding:12px">
    <div class="row" style="justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px">
      <h2 style="margin:0">Sleep dashboard</h2>
      <div class="row" style="gap:10px; align-items:center">
        <label for="sleepRangeSelect" ...>Date Range:</label>
        <select id="sleepRangeSelect" ...>...</select>
        <button id="renderSleepBtn" ...>Render sleep</button>
      </div>
    </div>
  </div>
</div>
```

**Step 2: Add skip naps checkbox**

Add checkbox AFTER date range select, BEFORE render button:

```html
<div class="row" style="gap:10px; align-items:center">
  <label for="sleepRangeSelect" style="margin:0" title="Filter all sleep data by date range. All charts and stats will update.">Date Range:</label>
  <select id="sleepRangeSelect" style="width:150px">
    <option value="1m">Last month</option>
    <option value="3m">Last 3 months</option>
    <option value="6m">Last 6 months</option>
    <option value="1y">Last 1 year</option>
    <option value="2y">Last 2 years</option>
    <option value="all" selected>All time</option>
  </select>
  <input type="checkbox" id="sleepSkipNaps" />
  <label for="sleepSkipNaps" style="margin:0" title="Suspected naps are periods of sleep <2h, starting between 10:00 and 17:00">Skip naps</label>
  <button id="renderSleepBtn" title="Render sleep charts">Render sleep</button>
</div>
```

**Step 3: Verify HTML**

Open `index.html` in browser, navigate to Sleep tab.
Expected: Checkbox appears in controls row, tooltip shows on hover.

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add skip naps checkbox to sleep controls"
```

---

## Task 2: Implement filterNaps Function

**Files:**
- Modify: `index.html` (JavaScript section, add function near sleep helper functions ~line 1900)

**Step 1: Find sleep helper functions location**

Search for existing sleep functions like `fetchSleepRecords` or `validateSleepData` (around line 800-900).

**Step 2: Add filterNaps function**

Insert after `fetchSleepRecords` function:

```javascript
function filterNaps(sleepRecords, skipNaps) {
  if (!skipNaps) return sleepRecords;

  return sleepRecords.filter(record => {
    const duration = record.durationMinutes || 0;
    const fromDate = new Date(record.from);
    const startHour = fromDate.getHours();

    // Keep if duration >= 120 min OR starts outside 10:00-17:00 window
    return duration >= 120 || startHour < 10 || startHour >= 17;
  });
}
```

**Step 3: Test in browser console**

Open browser console, create test data:
```javascript
const testRecords = [
  { durationMinutes: 480, from: "2026-03-10T23:00:00" }, // Night sleep - keep
  { durationMinutes: 90, from: "2026-03-10T13:00:00" },  // Nap - filter
  { durationMinutes: 420, from: "2026-03-10T14:00:00" }, // Long afternoon - keep (>120min)
  { durationMinutes: 60, from: "2026-03-10T09:00:00" }   // Morning nap - keep (before 10:00)
];

console.log(filterNaps(testRecords, true));
// Expected: 3 records (excludes 90min @ 13:00)
console.log(filterNaps(testRecords, false));
// Expected: 4 records (no filtering)
```

**Step 4: Commit**

```bash
git add index.html
git commit -m "Implement filterNaps function"
```

---

## Task 3: Integrate Nap Filter into renderSleepDashboard

**Files:**
- Modify: `index.html` (~line 3450, in `renderSleepDashboard` function)

**Step 1: Find renderSleepDashboard function**

Search for `async function renderSleepDashboard()` (around line 3450).

**Step 2: Add nap filter after fetching sleep records**

Find the section that fetches sleep records (around line 3500-3520):

```javascript
async function renderSleepDashboard(){
  setProgress(0, "Loading sleep data…");

  // ... existing code ...

  // Fetch sleep records for duration/bedtime charts
  let allSleepRecords = await db.sleepRecords.toArray();

  // NEW: Apply nap filter
  const skipNaps = $("sleepSkipNaps") ? $("sleepSkipNaps").checked : false;
  allSleepRecords = filterNaps(allSleepRecords, skipNaps);

  // Existing: Apply date range filter
  const selectedRange = $("sleepRangeSelect") ? $("sleepRangeSelect").value : "all";
  const cutoffDate = getRangeCutoffDate(selectedRange);
  // ... rest of function ...
}
```

**Step 3: Handle empty results case**

After nap filter, add validation:

```javascript
// NEW: Apply nap filter
const skipNaps = $("sleepSkipNaps") ? $("sleepSkipNaps").checked : false;
allSleepRecords = filterNaps(allSleepRecords, skipNaps);

// NEW: Check if all records were filtered out
if (skipNaps && allSleepRecords.length === 0) {
  const noticeHTML = '<div class="notice">All sleep records appear to be naps. Uncheck "Skip naps" to see data.</div>';
  const containers = ["sleepInsightCards", "sleepDeepDiveDuration", "sleepDeepDiveTiming", "weeklyPatternInsights"];
  containers.forEach(id => {
    const el = $(id);
    if (el) el.innerHTML = noticeHTML;
  });
  setProgress(100, "No sleep data after nap filtering");
  return;
}
```

**Step 4: Test in browser**

1. Load app, navigate to Sleep tab
2. Check "Skip naps" checkbox
3. Click "Render sleep"
4. Verify charts update (fewer data points if naps existed)
5. Uncheck "Skip naps", render again
6. Verify all data points return

**Step 5: Commit**

```bash
git add index.html
git commit -m "Integrate nap filter into sleep dashboard"
```

---

## Task 4: Remove Render Button and Add Auto-Render

**Files:**
- Modify: `index.html` (HTML section ~line 127, JavaScript section ~line 3760)

**Step 1: Remove render button from HTML**

Find and DELETE the render button line:

```html
<!-- DELETE THIS LINE: -->
<button id="renderSleepBtn" title="Render sleep charts">Render sleep</button>
```

Updated controls row should be:

```html
<div class="row" style="gap:10px; align-items:center">
  <label for="sleepRangeSelect" style="margin:0" title="Filter all sleep data by date range. All charts and stats will update.">Date Range:</label>
  <select id="sleepRangeSelect" style="width:150px">
    <option value="1m">Last month</option>
    <option value="3m">Last 3 months</option>
    <option value="6m">Last 6 months</option>
    <option value="1y">Last 1 year</option>
    <option value="2y">Last 2 years</option>
    <option value="all" selected>All time</option>
  </select>
  <input type="checkbox" id="sleepSkipNaps" />
  <label for="sleepSkipNaps" style="margin:0" title="Suspected naps are periods of sleep <2h, starting between 10:00 and 17:00">Skip naps</label>
</div>
```

**Step 2: Remove render button event listener**

Find and DELETE (around line 3765):

```javascript
// DELETE THIS LINE:
if ($("renderSleepBtn")) $("renderSleepBtn").addEventListener("click", ()=>renderSleepDashboard().catch(console.error));
```

**Step 3: Add auto-render event listeners**

Add AFTER the deleted listener:

```javascript
// Auto-render on sleep filter changes
if ($("sleepRangeSelect")) {
  $("sleepRangeSelect").addEventListener("change", () => {
    renderSleepDashboard().catch(console.error);
  });
}

if ($("sleepSkipNaps")) {
  $("sleepSkipNaps").addEventListener("change", () => {
    renderSleepDashboard().catch(console.error);
  });
}
```

**Step 4: Test auto-render behavior**

1. Load app, navigate to Sleep tab
2. Change date range dropdown → charts should auto-render
3. Toggle "Skip naps" checkbox → charts should auto-render
4. Verify no manual button click needed

**Step 5: Commit**

```bash
git add index.html
git commit -m "Remove render button, add auto-render on filter change"
```

---

## Task 5: Implement wrapBedtimeHour Function

**Files:**
- Modify: `index.html` (add function near sleep helpers, ~line 1950)

**Step 1: Add wrapBedtimeHour function**

Insert near filterNaps function:

```javascript
function wrapBedtimeHour(hour) {
  // Input: hour in 0-24 range (from bedtime minutes / 60)
  // Output: hour in 12-36 range for Y-axis display
  // If hour < 12 (midnight to noon), add 24 to put it in "next day" section
  return hour < 12 ? hour + 24 : hour;
}
```

**Step 2: Test in browser console**

```javascript
console.log(wrapBedtimeHour(23));   // 23 (11pm stays as-is)
console.log(wrapBedtimeHour(1));    // 25 (1am wraps forward)
console.log(wrapBedtimeHour(6));    // 30 (6am wraps forward)
console.log(wrapBedtimeHour(12));   // 12 (noon boundary)
console.log(wrapBedtimeHour(0));    // 24 (midnight wraps)
```

Expected outputs: 23, 25, 30, 12, 24

**Step 3: Commit**

```bash
git add index.html
git commit -m "Add wrapBedtimeHour function for Y-axis reorientation"
```

---

## Task 6: Update Bedtime Chart with Reoriented Y-Axis

**Files:**
- Modify: `index.html` (~line 3589-3609, bedtime chart section)

**Step 1: Find bedtime chart rendering code**

Search for `sleepBedtimeChart` (around line 3589):

```javascript
const bedEl = $("sleepBedtimeChart");
if (!window.sleepBedChart && bedEl){
  window.sleepBedChart = echarts.init(bedEl, null, { renderer:"canvas" });
  window.addEventListener("resize", ()=>{ try{ window.sleepBedChart.resize(); }catch(e){} });
}
const bDates = ins.bd.dates;
const bVals = ins.bd.values;
const pts = bDates.map((d,i)=>[d, bVals[i]/60]); // hours
```

**Step 2: Update data transformation to use wrapping**

Replace the `pts` line:

```javascript
// OLD:
const pts = bDates.map((d,i)=>[d, bVals[i]/60]); // hours

// NEW:
const pts = bDates.map((d,i)=>{
  const hour = bVals[i]/60;
  const wrappedHour = wrapBedtimeHour(hour);
  return [d, wrappedHour];
});
```

**Step 3: Update Y-axis configuration**

Find the `yAxis` config in `sleepBedChart.setOption()`:

```javascript
// OLD:
yAxis:{ type:"value", min:0, max:24,
       axisLabel:{ color:"#9fb0c3", formatter:(v)=>{ const hh=Math.floor(v); const mm=Math.round((v%1)*60); return `${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`; } } },

// NEW:
yAxis:{ type:"value", min:12, max:36,
       axisLabel:{ color:"#9fb0c3", formatter:(v)=>{
         const wrapped = v >= 24 ? v - 24 : v;
         const hh=Math.floor(wrapped);
         const mm=Math.round((wrapped%1)*60);
         return `${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`;
       } } },
```

**Step 4: Update tooltip to handle wrapped values**

```javascript
// OLD:
tooltip:{ formatter:(p)=>{
  const d=p.data[0]; const v=p.data[1];
  const hh=Math.floor(v); const mm=Math.round((v%1)*60);
  return `${d}<br/>Bedtime: ${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`;
}},

// NEW:
tooltip:{ formatter:(p)=>{
  const d=p.data[0];
  const wrappedV=p.data[1];
  const v = wrappedV >= 24 ? wrappedV - 24 : wrappedV;
  const hh=Math.floor(v); const mm=Math.round((v%1)*60);
  return `${d}<br/>Bedtime: ${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}`;
}},
```

**Step 5: Test Y-axis reorientation**

1. Load app, navigate to Sleep tab
2. Observe bedtime scatter chart
3. Verify Y-axis shows 12:00 at bottom, goes up to 12:00 (wrapping through midnight)
4. Verify bedtime cluster (typically 22:00-02:00) appears grouped together
5. Verify axis labels show correct times (00:00, 06:00, 12:00, etc.)

**Step 6: Commit**

```bash
git add index.html
git commit -m "Reorient bedtime chart Y-axis from 12:00 to 11:59"
```

---

## Task 7: Add Color-Coding by Duration

**Files:**
- Modify: `index.html` (~line 3589-3609, bedtime chart section)

**Step 1: Transform data to include color**

This task builds on Task 6. We need access to the full sleep records, not just the aggregated bedtime data.

Find where `ins.bd` (bedtime data) is used and replace with direct sleep records access.

**Current approach uses aggregated data:**
```javascript
const bDates = ins.bd.dates;
const bVals = ins.bd.values;
const pts = bDates.map((d,i)=>{ ... });
```

**New approach uses sleep records directly:**

Replace the entire data preparation section:

```javascript
// Build bedtime scatter data from filtered sleep records
// Need to access the filtered sleep records from earlier in renderSleepDashboard
// Assume sleepRecordsFiltered is available in scope

const pts = [];
for (const record of sleepRecordsFiltered) {
  if (!record.from) continue;

  const fromDate = new Date(record.from);
  const bedtimeMinutes = fromDate.getHours() * 60 + fromDate.getMinutes();
  const bedtimeHour = bedtimeMinutes / 60;
  const wrappedHour = wrapBedtimeHour(bedtimeHour);

  const durationHours = (record.durationMinutes || 0) / 60;

  let color;
  if (!record.durationMinutes) color = '#6b7a8f'; // Gray for missing
  else if (durationHours < 6) color = '#ff5a6b';   // Red
  else if (durationHours < 7) color = '#ffbf3a';   // Yellow
  else if (durationHours < 8) color = '#3dce79';   // Green
  else color = '#3aa0ff';                          // Blue

  pts.push({
    value: [record.date, wrappedHour],
    itemStyle: { color }
  });
}
```

**Step 2: Ensure sleepRecordsFiltered is in scope**

Earlier in `renderSleepDashboard`, after applying filters, store in a variable:

```javascript
// After nap filter and date range filter
let sleepRecordsFiltered = allSleepRecords; // Use filtered records for charts
```

**Step 3: Update series config**

The series config stays the same since ECharts handles `itemStyle` automatically:

```javascript
series:[ { name:"Bedtime", type:"scatter", data: pts, symbolSize:6 } ]
```

**Step 4: Test color-coding**

1. Load app, navigate to Sleep tab
2. Observe bedtime scatter chart dots
3. Verify color variation:
   - Red dots appear for short sleep (<6h)
   - Yellow for borderline (6-7h)
   - Green for optimal (7-8h)
   - Blue for long sleep (>8h)
4. Hover over different colored dots to verify duration matches color

**Step 5: Commit**

```bash
git add index.html
git commit -m "Add duration-based color-coding to bedtime scatter"
```

---

## Task 8: Update Tooltip to Show Duration

**Files:**
- Modify: `index.html` (~line 3599, tooltip formatter)

**Step 1: Add formatDuration helper**

Add helper function near other sleep helpers:

```javascript
function formatDuration(durationMinutes) {
  if (!durationMinutes) return "—";
  const hours = Math.floor(durationMinutes / 60);
  const mins = Math.round(durationMinutes % 60);
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}
```

**Step 2: Update tooltip formatter**

Modify tooltip to find and display duration:

```javascript
tooltip:{ formatter:(p)=>{
  const date = p.data.value[0];
  const wrappedV = p.data.value[1];
  const displayV = wrappedV >= 24 ? wrappedV - 24 : wrappedV;
  const hh = Math.floor(displayV);
  const mm = Math.round((displayV % 1) * 60);

  // Find corresponding record to get duration
  const record = sleepRecordsFiltered.find(r => r.date === date);
  const durationText = record ? formatDuration(record.durationMinutes) : "—";

  return `${date}<br/>Bedtime: ${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}<br/>Duration: ${durationText}`;
}},
```

**Step 3: Test tooltip**

1. Load app, navigate to Sleep tab
2. Hover over bedtime scatter dots
3. Verify tooltip shows:
   - Date
   - Bedtime (correctly unwrapped to 0-23 range)
   - Duration (formatted as "7h 30m" or similar)

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add duration display to bedtime chart tooltip"
```

---

## Task 9: Manual Testing and Verification

**Files:**
- None (manual browser testing)

**Step 1: Full workflow test**

1. Open app in browser, clear local storage, reload
2. Load Withings ZIP export
3. Navigate to Sleep tab

**Step 2: Verify nap filtering**

1. Note total number of data points in bedtime chart
2. Check "Skip naps" checkbox
3. Verify chart auto-renders with fewer points
4. Uncheck "Skip naps"
5. Verify all points return

**Step 3: Verify Y-axis reorientation**

1. Observe Y-axis range (12:00 at bottom, through 00:00, to 12:00 at top)
2. Verify bedtime cluster (22:00-02:00) appears visually grouped
3. Verify wake time implied range (06:00-10:00) appears in upper portion
4. Check axis labels wrap correctly (24:00 displays as 00:00, etc.)

**Step 4: Verify color-coding**

1. Identify red dots (short sleep <6h)
2. Identify yellow dots (borderline 6-7h)
3. Identify green dots (optimal 7-8h)
4. Identify blue dots (long sleep >8h)
5. Hover over various dots, verify color matches duration shown in tooltip

**Step 5: Verify auto-render**

1. Change date range dropdown → verify auto-render
2. Toggle skip naps → verify auto-render
3. Verify no manual button needed

**Step 6: Verify all components receive filtered data**

1. With "Skip naps" checked, verify overview cards update
2. Verify duration chart shows fewer points
3. Verify deep dive components reflect filtered data
4. Verify pattern insights update

**Step 7: Edge case testing**

1. Check "Skip naps" with a dataset that might be all naps
2. Verify notice appears if all records filtered out
3. Test with date range that has no data
4. Test with missing duration values (should show gray dots)

**Step 8: Cross-browser testing (optional)**

1. Test in Chrome
2. Test in Firefox
3. Test in Safari (macOS)

**Step 9: Document any issues found**

Create notes in `docs/testing-notes.md` if issues discovered.

**Step 10: Final commit (if any fixes needed)**

```bash
git add index.html
git commit -m "Fix [specific issue found during testing]"
```

---

## Success Criteria

- [ ] "Skip naps" checkbox appears in sleep controls
- [ ] Checkbox has tooltip explaining nap detection criteria
- [ ] "Render sleep" button removed from UI
- [ ] Date range change triggers auto-render
- [ ] Skip naps change triggers auto-render
- [ ] Nap filter correctly excludes <2h sessions starting 10:00-17:00
- [ ] Bedtime chart Y-axis shows 12:00-11:59 range (not 00:00-24:00)
- [ ] Bedtime cluster (22:00-02:00) appears visually grouped
- [ ] Axis labels wrap correctly (displays 00:00 for value 24, etc.)
- [ ] Bedtime dots colored by duration (red/yellow/green/blue)
- [ ] Colors match duration ranges (<6h red, 6-7h yellow, 7-8h green, >8h blue)
- [ ] Tooltip shows date, bedtime, and duration
- [ ] All sleep components receive same filtered dataset
- [ ] Empty results show notice instead of broken charts
- [ ] No console errors during normal operation
- [ ] No breaking changes to existing sleep features

---

## Notes

**Single-file architecture:** All changes in `index.html`. No separate test files - manual browser testing only.

**Testing approach:** This project uses manual browser verification. Each task includes "Test in browser" steps.

**Error handling:** Existing error boundaries in `renderSleepDashboard` catch failures. No additional error handling needed beyond empty-result checks.

**Data consistency:** Nap filter applied once, early in pipeline. All components receive same filtered dataset automatically.

**Frequent commits:** Each task ends with a commit. Allows easy rollback if issues found.

**Dependencies:**
- Tasks 1-4 can be done in parallel
- Task 6 depends on Task 5 (needs wrapBedtimeHour function)
- Task 7 depends on Task 6 (builds on same data transformation)
- Task 8 depends on Task 7 (needs access to sleepRecordsFiltered)
- Task 9 depends on all previous tasks
