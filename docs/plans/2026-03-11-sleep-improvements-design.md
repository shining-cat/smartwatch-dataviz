# Sleep Tab Improvements Design

**Date:** 2026-03-11
**Status:** Approved

---

## Overview

Enhance the Sleep tab with three features that improve data quality and visualization clarity:

1. **Nap filtering** - Filter out suspected nap periods to focus on nighttime sleep
2. **Y-axis reorientation** - Reorient bedtime scatter chart to group bedtime/wake clusters naturally
3. **Color-coded bedtime scatter** - Visualize sleep duration patterns via dot colors

**Goals:**
- Improve data quality by allowing users to exclude naps from analysis
- Make bedtime patterns more intuitive to read (eliminate midnight split)
- Surface duration patterns visually without adding chart complexity
- Match Activity tab UX pattern (auto-render on filter change)

---

## Architecture

### Overall Approach

**UI consistency:**
- Add "Skip naps" checkbox to sleep controls (next to date range selector)
- Remove "Render sleep" button - auto-render on any filter change (matches Activity tab)
- No toggles needed for bedtime chart enhancements (applied automatically)

**Data flow:**
1. User changes filter (date range or skip naps checkbox)
2. Event listener triggers `renderSleepDashboard()`
3. Fetch sleep records from IndexedDB
4. Apply nap filter if checkbox checked
5. Apply date range filter (existing code)
6. Pass filtered data to all charts and analysis components
7. Bedtime chart renders with reoriented Y-axis and duration-based colors

**Integration points:**
- Nap filter applied early in pipeline (affects all components)
- Bedtime chart config updated (Y-axis range, data transformation, colors)
- Existing validation and error handling remain unchanged

---

## Feature 1: Nap Filtering

### UI Components

**Checkbox:**
- ID: `sleepSkipNaps`
- Label: "Skip naps"
- Tooltip: "Suspected naps are periods of sleep <2h, starting between 10:00 and 17:00"
- Position: In sleep controls row, after date range selector

**HTML snippet:**
```html
<input type="checkbox" id="sleepSkipNaps" />
<label for="sleepSkipNaps" title="Suspected naps are periods of sleep <2h, starting between 10:00 and 17:00">Skip naps</label>
```

### Detection Logic

**Nap criteria:**
- Duration: less than 2 hours (120 minutes)
- Start time: between 10:00 and 17:00

**Reasoning:**
- These criteria will never apply to actual nighttime sleep
- Conservative thresholds minimize false positives
- Future use: nap vs night-sleep distinction valuable for correlation analysis

### Implementation

**Filter function:**
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

**Integration:**
- Call after fetching sleep records, before date range filter
- Apply to both main dashboard data and deep dive components
- Filter state read from checkbox: `$("sleepSkipNaps").checked`

### Edge Cases

- Missing `durationMinutes` field → treat as 0 (will be filtered if naps skipped)
- Invalid `from` timestamp → keep record (can't determine if nap)
- All records filtered out → show notice: "All sleep records appear to be naps. Uncheck 'Skip naps' to see data."

---

## Feature 2: Y-Axis Reorientation

### Problem Statement

**Current behavior:**
- Y-axis range: 0-24 (00:00 midnight to 24:00 midnight)
- Bedtime cluster (typically 22:00-02:00) split across top and bottom
- Wake time cluster (typically 06:00-10:00) appears disconnected
- Midnight has no biological significance for sleep/wake cycles

**Proposed change:**
- Y-axis range: 12-36 (12:00 noon to 11:59 next morning)
- Bedtime cluster stays together (22:00-26:00 on wrapped scale)
- Wake time cluster stays together (18:00-22:00 on wrapped scale)
- More intuitive reading matches natural sleep/wake distribution

### Transform Logic

**Hour wrapping:**
```javascript
function wrapBedtimeHour(hour) {
  // Input: hour in 0-24 range (from bedtime minutes / 60)
  // Output: hour in 12-36 range for display
  // If hour < 12 (midnight to noon), add 24 to put it in "next day" section
  return hour < 12 ? hour + 24 : hour;
}
```

**Examples:**
- 23:00 (11pm) → 23 (stays as-is)
- 01:00 (1am) → 25 (wraps forward)
- 06:00 (6am wake) → 30 (wraps forward)
- 12:00 (noon) → 12 (boundary, stays as-is)

### Y-Axis Configuration

**ECharts config:**
```javascript
yAxis: {
  type: "value",
  min: 12,
  max: 36,
  axisLabel: {
    color: "#9fb0c3",
    formatter: (v) => {
      // Wrap display values back to 0-23 for readability
      const wrapped = v >= 24 ? v - 24 : v;
      const hh = Math.floor(wrapped);
      const mm = Math.round((wrapped % 1) * 60);
      return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
    }
  }
}
```

**Tick values example:**
- 12 → displays "12:00"
- 18 → displays "18:00"
- 24 → displays "00:00" (wrapped)
- 30 → displays "06:00" (wrapped)
- 36 → displays "12:00" (wrapped)

### Data Transformation

**Current data structure:**
```javascript
const pts = bDates.map((d, i) => [d, bVals[i] / 60]); // [date, hour]
```

**New structure (with wrapping):**
```javascript
const pts = sleepRecordsFiltered.map(record => {
  const fromDate = new Date(record.from);
  const bedtimeMinutes = fromDate.getHours() * 60 + fromDate.getMinutes();
  const bedtimeHour = bedtimeMinutes / 60;
  const wrappedHour = wrapBedtimeHour(bedtimeHour);

  return [record.date, wrappedHour];
});
```

---

## Feature 3: Color-Coding by Duration

### Goal

Visualize correlation between bedtime and sleep duration at a glance, without adding separate chart or legend clutter.

### Color Scale

**Duration thresholds:**
- **Red** (`#ff5a6b`): < 6 hours (short sleep, generally insufficient)
- **Yellow** (`#ffbf3a`): 6-7 hours (borderline sleep)
- **Green** (`#3dce79`): 7-8 hours (optimal sleep range)
- **Blue** (`#3aa0ff`): > 8 hours (long sleep)
- **Gray** (`#6b7a8f`): missing/invalid duration (fallback)

**Color selection reasoning:**
- Red/yellow for concerning durations (matches app's existing semantic colors)
- Green for healthy range (consistent with app theme)
- Blue for long sleep (neutral, distinct from other categories)

### Implementation

**Data transformation:**
```javascript
const pts = sleepRecordsFiltered.map(record => {
  const fromDate = new Date(record.from);
  const bedtimeMinutes = fromDate.getHours() * 60 + fromDate.getMinutes();
  const bedtimeHour = bedtimeMinutes / 60;
  const wrappedHour = wrapBedtimeHour(bedtimeHour);

  const durationHours = (record.durationMinutes || 0) / 60;

  let color;
  if (!record.durationMinutes) color = '#6b7a8f'; // Gray for missing data
  else if (durationHours < 6) color = '#ff5a6b';   // Red
  else if (durationHours < 7) color = '#ffbf3a';   // Yellow
  else if (durationHours < 8) color = '#3dce79';   // Green
  else color = '#3aa0ff';                          // Blue

  return {
    value: [record.date, wrappedHour],
    itemStyle: { color }
  };
});
```

**ECharts series config:**
```javascript
series: [{
  name: "Bedtime",
  type: "scatter",
  data: pts, // Array of {value, itemStyle} objects
  symbolSize: 6
}]
```

**Tooltip enhancement:**
Show duration in tooltip for context:
```javascript
tooltip: {
  formatter: (p) => {
    const date = p.data.value[0];
    const wrappedHour = p.data.value[1];
    const displayHour = wrappedHour >= 24 ? wrappedHour - 24 : wrappedHour;
    const hh = Math.floor(displayHour);
    const mm = Math.round((displayHour % 1) * 60);

    // Find corresponding sleep record to get duration
    const record = sleepRecordsFiltered.find(r => r.date === date);
    const durationText = record ? formatDuration(record.durationMinutes) : "—";

    return `${date}<br/>Bedtime: ${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}<br/>Duration: ${durationText}`;
  }
}
```

### Visual Patterns Expected

**Common patterns that should emerge:**
- Late bedtimes (after midnight) often correlate with red/yellow dots (short sleep)
- Consistent bedtimes around 22:00-23:00 show green cluster (optimal sleep)
- Weekend bedtimes may show later times but still green (longer sleep opportunity)

---

## Auto-Render Behavior

### Remove Manual Render Button

**Current:**
- User selects date range
- Clicks "Render sleep" button
- Charts update

**New:**
- User selects date range OR toggles skip naps
- Charts auto-render immediately
- Matches Activity tab UX

### Event Listeners

**Remove:**
```javascript
if ($("renderSleepBtn")) $("renderSleepBtn").addEventListener("click", () => renderSleepDashboard().catch(console.error));
```

**Add:**
```javascript
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

**HTML changes:**
- Remove `<button id="renderSleepBtn">` element
- Keep date range selector and label
- Add skip naps checkbox and label

---

## Error Handling

### Nap Filtering

**Edge cases:**
- Missing `durationMinutes` → treat as 0, will be filtered if checkbox checked
- Invalid `from` timestamp → keep record (can't determine if nap)
- All records filtered out → show notice: "All sleep records appear to be naps. Uncheck 'Skip naps' to see data."

### Y-Axis Reorientation

**Validation:**
- Bedtime hours already validated by existing `validateSleepData()` function
- Hour wrapping handles edge cases (23:59 → 23.98, 00:01 → 24.02)
- Axis labels wrap correctly back to 0-23 for display

**No breaking changes:**
- Transform is purely presentational
- Raw data unchanged

### Color-Coding

**Fallbacks:**
- Missing duration → gray (`#6b7a8f`)
- Zero or negative duration → filtered upstream by validation (already exists)
- Invalid values → gray fallback

**Tooltip enhancement:**
- If duration unavailable, show "—" instead of breaking

### Auto-Render

**Error boundaries:**
- Both event listeners wrap `renderSleepDashboard()` in `.catch(console.error)`
- Existing error handling in `renderSleepDashboard()` catches failures
- User sees partial results if possible (existing behavior)

---

## Data Consistency

### Filter Order

1. Fetch sleep records from IndexedDB
2. **Nap filter** (if checkbox checked)
3. **Date range filter** (existing)
4. Pass to validation
5. Pass validated/filtered data to all components

**Reasoning:** Nap filter before date range ensures consistent behavior. Date range is more restrictive (time-based), nap filter is categorical (type-based).

### Pipeline Flow

```
IndexedDB
  ↓
Fetch sleepRecords
  ↓
Apply nap filter (filterNaps)
  ↓
Apply date range filter (filterByDateRange)
  ↓
Validate data (validateSleepData)
  ↓
Split into components:
  - Overview cards (duration avg, bedtime variability, etc.)
  - Duration chart (existing)
  - Bedtime scatter (ENHANCED: Y-axis + colors)
  - Deep dive components (duration, timing, weekly patterns)
```

**Same filtered dataset flows to all components** - no special handling needed, existing pipeline works.

---

## Success Criteria

- [ ] "Skip naps" checkbox added to sleep controls
- [ ] "Render sleep" button removed
- [ ] Date range change auto-renders sleep dashboard
- [ ] Skip naps change auto-renders sleep dashboard
- [ ] Nap filter correctly excludes <2h sessions starting 10:00-17:00
- [ ] Bedtime chart Y-axis shows 12:00-11:59 range
- [ ] Bedtime dots colored by duration (red/yellow/green/blue)
- [ ] Tooltip shows duration alongside bedtime
- [ ] All sleep components receive filtered data consistently
- [ ] No breaking changes to existing charts/analysis
- [ ] Error handling preserves existing robustness

---

## Out of Scope

**Not included in this enhancement:**
- Nap-specific analysis tab (future: compare naps vs night sleep)
- Wake time scatter chart (bedtime scatter only)
- Duration color legend (colors are intuitive: red=bad, green=good)
- Configurable nap detection thresholds (hardcoded for MVP)
- Historical nap patterns over time
- User preference persistence (filters reset on page reload)
