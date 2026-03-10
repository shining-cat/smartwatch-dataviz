# Activity Tab Insights Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add trend indicators to overview cards and auto-generated day-of-week pattern insights to Weekly Patterns chart

**Architecture:** Extend existing Activity tab with new calculation functions for trends (compare current vs previous period) and pattern detection (analyze weekly distribution). Minimal UI changes - add trend subtitle to cards and inline pattern text below chart.

**Tech Stack:** Vanilla JavaScript, ECharts (already in use), single-file HTML app

---

## Task 1: Add HTML Container for Pattern Insights

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:1695-1700`

**Step 1: Locate Weekly Patterns section in HTML**

Find the section around line 1695 that contains:
```html
<div id="workoutWeeklyPatternChart" style="..."></div>
```

**Step 2: Add pattern insights container**

Add immediately after `workoutWeeklyPatternChart` div (before closing the section):

```html
<div id="workoutWeeklyInsights" style="display:none;margin-top:12px;padding:12px;background:#1a2332;border-radius:6px;font-size:13px;color:#9fb0c3;text-align:center;"></div>
```

**Step 3: Verify in browser**

Expected: Container exists but is hidden (display:none)

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add HTML container for weekly pattern insights"
```

---

## Task 2: Implement calculatePreviousPeriodStats Function

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:2450` (after `calculateWorkoutStats`)

**Step 1: Add function after calculateWorkoutStats**

Insert at line ~2450 (after the closing brace of `calculateWorkoutStats`):

```javascript
/**
 * Calculate workout statistics for the previous equal period
 * @param {Array} activityRecords - All activity records
 * @param {string} selectedRange - Selected date range ('1m', '3m', '6m', '1y', '2y', 'all')
 * @param {Date} cutoffDate - Current period cutoff date
 * @returns {Object} Statistics for previous period
 */
function calculatePreviousPeriodStats(activityRecords, selectedRange, cutoffDate) {
  // For "all time", no previous period exists
  if (!selectedRange || selectedRange === 'all' || !cutoffDate) {
    return null;
  }

  // Calculate previous period date range
  let previousCutoffDate = new Date(cutoffDate);

  switch(selectedRange) {
    case '1m':
      previousCutoffDate.setMonth(previousCutoffDate.getMonth() - 1);
      break;
    case '3m':
      previousCutoffDate.setMonth(previousCutoffDate.getMonth() - 3);
      break;
    case '6m':
      previousCutoffDate.setMonth(previousCutoffDate.getMonth() - 6);
      break;
    case '1y':
      previousCutoffDate.setFullYear(previousCutoffDate.getFullYear() - 1);
      break;
    case '2y':
      previousCutoffDate.setFullYear(previousCutoffDate.getFullYear() - 2);
      break;
    default:
      return null;
  }

  // Filter records to previous period
  const cutoffStr = cutoffDate.toISOString().split('T')[0];
  const previousCutoffStr = previousCutoffDate.toISOString().split('T')[0];

  const previousRecords = activityRecords.filter(r =>
    r.date >= previousCutoffStr && r.date < cutoffStr
  );

  // Return stats for previous period
  return calculateWorkoutStats(previousRecords);
}
```

**Step 2: Verify syntax**

Expected: No console errors when page loads

**Step 3: Commit**

```bash
git add index.html
git commit -m "Add calculatePreviousPeriodStats function"
```

---

## Task 3: Implement calculateTrends Function

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:~2510` (after `calculatePreviousPeriodStats`)

**Step 1: Add calculateTrends function**

Insert after `calculatePreviousPeriodStats`:

```javascript
/**
 * Calculate trends by comparing current vs previous period
 * @param {Object} currentStats - Current period statistics
 * @param {Object} previousStats - Previous period statistics (null for "all time")
 * @returns {Object} Trend objects for each metric
 */
function calculateTrends(currentStats, previousStats) {
  const trends = {
    workoutsPerWeek: null,
    currentStreak: null,
    longestGap: null,
    avgDuration: null
  };

  // No trends for "all time" or missing previous data
  if (!previousStats) {
    return trends;
  }

  // Helper to calculate trend
  const calcTrend = (current, previous, invertColors = false) => {
    if (previous === 0 && current === 0) {
      return { direction: 'stable', text: 'No data' };
    }
    if (previous === 0) {
      return { direction: 'up', text: 'New data' };
    }

    const change = ((current - previous) / previous) * 100;
    let direction;

    if (Math.abs(change) < 5) {
      direction = 'stable';
    } else if (change > 0) {
      direction = invertColors ? 'down' : 'up';
    } else {
      direction = invertColors ? 'up' : 'down';
    }

    const text = Math.abs(change) < 5
      ? 'Stable'
      : `${Math.abs(change).toFixed(0)}% vs previous period`;

    return { direction, text };
  };

  // Calculate trends for each metric
  trends.workoutsPerWeek = calcTrend(
    currentStats.workoutsPerWeek,
    previousStats.workoutsPerWeek
  );

  // Current streak: special case for starting from 0
  if (previousStats.currentStreak === 0 && currentStats.currentStreak > 0) {
    trends.currentStreak = { direction: 'up', text: 'Started!' };
  } else {
    trends.currentStreak = calcTrend(
      currentStats.currentStreak,
      previousStats.currentStreak
    );
  }

  // Longest gap: inverted (lower is better)
  trends.longestGap = calcTrend(
    currentStats.longestGap,
    previousStats.longestGap,
    true  // invert colors
  );

  trends.avgDuration = calcTrend(
    currentStats.avgDuration,
    previousStats.avgDuration
  );

  return trends;
}
```

**Step 2: Verify syntax**

Expected: No console errors

**Step 3: Commit**

```bash
git add index.html
git commit -m "Add calculateTrends function"
```

---

## Task 4: Update renderWorkoutOverview to Show Trends

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:2470-2550`

**Step 1: Update function signature**

Change line ~2470 from:
```javascript
function renderWorkoutOverview(activityRecords, selectedType) {
```

To:
```javascript
function renderWorkoutOverview(activityRecords, selectedType, selectedRange, cutoffDate) {
```

**Step 2: Update card creation helper**

Replace the `mk` helper function (around line 2488) with:

```javascript
// Helper to create insight cards with optional trend
const mk = (title, main, sub, tooltip, trend) => {
  const d = document.createElement("div");
  d.className = "insight-card";
  if (tooltip) d.title = tooltip;

  let trendHTML = '';
  if (trend && trend.direction) {
    const color = trend.direction === 'up' ? '#3dce79' :
                  trend.direction === 'down' ? '#ff5a6b' : '#6b7a8f';
    const arrow = trend.direction === 'up' ? '↑' :
                  trend.direction === 'down' ? '↓' : '—';
    trendHTML = `<div style="font-size:11px;color:${color};margin-top:4px;">
                   ${arrow} ${trend.text}
                 </div>`;
  }

  d.innerHTML = `<div style="font-size:12px;color:#9fb0c3;">${title}</div>
                 <div style="font-size:18px;font-weight:700;margin-top:6px">${main}</div>
                 <div class="muted" style="margin-top:6px">${sub}</div>
                 ${trendHTML}`;
  return d;
};
```

**Step 3: Calculate trends**

Add after `const stats = calculateWorkoutStats(filteredRecords);` (around line 2498):

```javascript
// Calculate previous period stats and trends
const previousStats = calculatePreviousPeriodStats(activityRecords, selectedRange, cutoffDate);
const trends = calculateTrends(stats, previousStats);
```

**Step 4: Update card creation calls**

Find the four `cardsEl.appendChild(mk(...))` calls and update them to pass trends:

For "All Activities" mode (around line 2505):
```javascript
cardsEl.appendChild(mk(
  "Workouts/week",
  stats.workoutsPerWeek.toFixed(1),
  "Last 30 days",
  "Your average weekly workout frequency over the last 30 days",
  trends.workoutsPerWeek
));
cardsEl.appendChild(mk(
  "Current streak",
  `${stats.currentStreak} week${stats.currentStreak !== 1 ? 's' : ''}`,
  stats.currentStreak === 0 ? "No active streak" : "Consecutive weeks",
  "How many consecutive weeks you've had at least one workout",
  trends.currentStreak
));
cardsEl.appendChild(mk(
  "Longest gap",
  `${stats.longestGap} days`,
  "Max time without workout",
  "Your longest period without a workout in the selected date range",
  trends.longestGap
));
cardsEl.appendChild(mk(
  "Avg duration",
  formatDuration(stats.avgDuration),
  "Per workout",
  "Average duration across all workouts in selected range",
  trends.avgDuration
));
```

For specific activity type mode (around line 2520):
```javascript
cardsEl.appendChild(mk(
  `${selectedType} sessions`,
  stats.sessionCount,
  "In selected range",
  null,
  null  // No trend for session count
));
cardsEl.appendChild(mk(
  "Avg duration",
  formatDuration(stats.avgDuration),
  "Per session",
  null,
  trends.avgDuration
));

// Distance/elevation cards (conditional, no trends needed for now)
```

**Step 5: Test in browser**

Open Activity tab, select "Last month", check if trends appear below card values.

Expected: Cards show trend indicators like "↑ 12% vs previous period" in green/red/gray

**Step 6: Commit**

```bash
git add index.html
git commit -m "Add trend indicators to workout overview cards"
```

---

## Task 5: Implement detectWeeklyPatterns Function

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:~2630` (after `calculateTrends`)

**Step 1: Add detectWeeklyPatterns function**

Insert after `calculateTrends`:

```javascript
/**
 * Detect day-of-week workout patterns
 * @param {Array} avgWorkoutsPerDay - Array of 7 average workout values (Mon-Sun)
 * @param {Array} weekdayNames - Array of weekday names
 * @returns {Array} Array of pattern strings
 */
function detectWeeklyPatterns(avgWorkoutsPerDay, weekdayNames) {
  const patterns = [];

  // Calculate overall mean
  const weeklyMean = avgWorkoutsPerDay.reduce((a,b) => a+b, 0) / 7;

  if (weeklyMean === 0) return patterns;  // No data

  // Pattern 1: Weekend warrior (Sat+Sun vs Mon-Fri)
  const weekendAvg = (avgWorkoutsPerDay[5] + avgWorkoutsPerDay[6]) / 2;  // Sat, Sun
  const weekdayAvg = avgWorkoutsPerDay.slice(0, 5).reduce((a,b) => a+b, 0) / 5;  // Mon-Fri

  if (weekdayAvg > 0 && weekendAvg / weekdayAvg > 1.5) {
    const ratio = (weekendAvg / weekdayAvg).toFixed(1);
    patterns.push(`💪 Weekend warrior: ${ratio}x more workouts Sat/Sun`);
  }

  // Pattern 2: Peak day (>30% of workouts OR >1.5x mean)
  const totalWorkouts = avgWorkoutsPerDay.reduce((a,b) => a+b, 0);
  for (let i = 0; i < 7; i++) {
    const percentage = (avgWorkoutsPerDay[i] / totalWorkouts) * 100;
    const multiplier = avgWorkoutsPerDay[i] / weeklyMean;

    if (percentage > 30 || multiplier > 1.5) {
      patterns.push(`🎯 ${weekdayNames[i]} peak (${percentage.toFixed(0)}% of workouts)`);
      break;  // Only show one peak day
    }
  }

  // Pattern 3: Mid-week slump (day with <0.6x mean AND significantly lowest)
  const minDay = avgWorkoutsPerDay.indexOf(Math.min(...avgWorkoutsPerDay));
  if (avgWorkoutsPerDay[minDay] < weeklyMean * 0.6 && minDay >= 1 && minDay <= 4) {
    patterns.push(`Mid-week slump on ${weekdayNames[minDay]}`);
  }

  // Return max 2 patterns
  return patterns.slice(0, 2);
}
```

**Step 2: Verify syntax**

Expected: No console errors

**Step 3: Commit**

```bash
git add index.html
git commit -m "Add detectWeeklyPatterns function"
```

---

## Task 6: Update renderWorkoutWeeklyPatterns to Show Patterns

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:2844-2970`

**Step 1: Find the avgWorkoutsPerDay calculation**

Locate around line 2906 where `avgWorkoutsPerDay` is calculated.

**Step 2: Add pattern detection after chart rendering**

Add after the `window.workoutWeeklyPatternChart.setOption(...)` call (around line 2960):

```javascript
// Detect and display patterns
const patterns = detectWeeklyPatterns(avgWorkoutsPerDay, weekdayNames);
const insightsContainer = $("workoutWeeklyInsights");

if (insightsContainer) {
  if (patterns.length > 0) {
    insightsContainer.innerHTML = patterns.join(' • ');
    insightsContainer.style.display = '';
  } else {
    insightsContainer.style.display = 'none';
  }
}
```

**Step 3: Test in browser**

Open Activity tab, scroll to Weekly Patterns chart.

Expected: Pattern insights appear below chart, e.g., "💪 Weekend warrior: 2.5x more workouts Sat/Sun • 🎯 Monday peak (35% of workouts)"

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add pattern insights to weekly patterns chart"
```

---

## Task 7: Update renderActivityDashboard to Pass New Parameters

**Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html:3106-3245`

**Step 1: Find renderActivityDashboard function**

Locate around line 3106.

**Step 2: Update renderWorkoutOverview call**

Find the line (around line 3152):
```javascript
renderWorkoutOverview(filteredRecords, selectedType);
```

Replace with:
```javascript
renderWorkoutOverview(filteredRecords, selectedType, selectedRange, cutoffDate);
```

**Step 3: Test full flow in browser**

1. Open Activity tab
2. Select different date ranges (Last month, 3m, 6m, All time)
3. Verify trends show for ranges with data, hidden for "All time"
4. Check pattern insights below Weekly Patterns chart

Expected:
- Trends visible for time ranges
- Trends hidden for "All time"
- Patterns show relevant insights

**Step 4: Commit**

```bash
git add index.html
git commit -m "Wire up trends and patterns in dashboard render flow"
```

---

## Task 8: Manual Testing & Verification

**Step 1: Test trend indicators**

Test scenarios:
1. Select "Last month" → verify trends show
2. Select "All time" → verify trends hidden
3. Select "Last 3 months" → verify percentage calculations look reasonable
4. Check color coding: green for improvements, red for declines

**Step 2: Test pattern insights**

Test scenarios:
1. Check if "Weekend warrior" pattern appears (if applicable to data)
2. Check if peak day pattern appears
3. Verify pattern text is readable and compact
4. Verify container hides when no patterns detected

**Step 3: Test edge cases**

1. Filter to single activity type → verify trends still work
2. Select very short date range (few workouts) → verify no crashes
3. Refresh page → verify patterns persist

**Step 4: Visual polish check**

- Trend text readable (11px, good contrast)
- Pattern insights compact and centered
- No layout jumps when switching filters
- Colors match design (green #3dce79, red #ff5a6b, gray #6b7a8f)

**Step 5: Final commit if any fixes needed**

```bash
git add index.html
git commit -m "Polish trends and patterns UI"
```

---

## Success Criteria

- [ ] Trend indicators appear on all 4 overview cards
- [ ] Trends show comparison to previous equal period
- [ ] Trends hidden for "All time" range
- [ ] Trend colors correct (green=good, red=bad for most metrics, inverted for longest gap)
- [ ] "Started!" shown for streak from 0
- [ ] "New data" shown when no previous period data
- [ ] Pattern insights detect weekend warrior pattern
- [ ] Pattern insights detect peak day pattern
- [ ] Pattern insights detect mid-week slump
- [ ] Multiple patterns joined with " • " separator
- [ ] Pattern container hidden when no patterns detected
- [ ] UI remains compact and readable
- [ ] No console errors
- [ ] Works across all date range selections

---

## Notes

**No automated tests:** This is a single-file HTML app without a test framework. All verification is manual via browser testing.

**Defensive coding:** Functions return null/empty gracefully when data is missing. UI elements check for null before rendering.

**Performance:** All calculations are synchronous and fast (operating on already-filtered arrays of <10k records).
