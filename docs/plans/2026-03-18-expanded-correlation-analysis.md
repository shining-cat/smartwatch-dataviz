# Expanded Correlation Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add heart rate metrics, day-of-week patterns, and segmented correlation analysis to surface more insights from health data

**Architecture:** Extend existing correlation engine with three new analysis types: (1) HR-based correlations using existing data extraction, (2) categorical day-of-week analysis using t-tests and ANOVA, (3) segmented correlations that split by weekend/weekday context

**Tech Stack:** Vanilla JavaScript, ECharts for visualization, IndexedDB (Dexie) for storage

---

## Overview

This is a single-file HTML application (`index.html`). Testing is manual via browser. Each task follows the pattern: implement → verify in browser → commit.

**Key Files:**
- Modify: `/Users/shiva.bernhard@m10s.io/__DEV/PERSO/smartwatch-dataviz/index.html`

**Testing:**
- Start local server: `python3 -m http.server 8000`
- Open: `http://localhost:8000`
- Load data: Use existing ZIP at `data/raw/20260305_data_withings_export_BKP.zip`

---

## Task 1: Extract Heart Rate from sleep.csv

**Goal:** Extend sleep records with avgHeartRate, minHeartRate, maxHeartRate fields

**Files:**
- Modify: `index.html:862-917` (sleep.csv parsing section)

**Step 1: Add HR extraction to sleep record creation**

In the sleep.csv parsing block (around line 887-895), extend the `sleepRecordsBuffer.push()` to include HR fields:

```javascript
// Store full sleep record for Sleep Deep Dive components
const durationMinutes = value;
const durationHours = Math.round((durationMinutes / 60) * 100) / 100;
const dayOfWeek = toDt.getDay();
const weekdayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Extract HR data from CSV columns
const avgHR = r["Average heart rate"] || r["average heart rate"] || r.hr_average;
const minHR = r["Heart rate (min)"] || r["heart rate (min)"] || r.hr_min;
const maxHR = r["Heart rate (max)"] || r["heart rate (max)"] || r.hr_max;

// Parse and validate HR values (valid range: 20-200 bpm)
const avgHeartRate = avgHR ? parseFloat(avgHR) : null;
const minHeartRate = minHR ? parseFloat(minHR) : null;
const maxHeartRate = maxHR ? parseFloat(maxHR) : null;

// Sanitize (set to null if invalid, but keep the sleep record)
const validAvgHR = (avgHeartRate !== null && !isNaN(avgHeartRate) && avgHeartRate >= 20 && avgHeartRate <= 200) ? avgHeartRate : null;
const validMinHR = (minHeartRate !== null && !isNaN(minHeartRate) && minHeartRate >= 20 && minHeartRate <= 200) ? minHeartRate : null;
const validMaxHR = (maxHeartRate !== null && !isNaN(maxHeartRate) && maxHeartRate >= 20 && maxHeartRate <= 200) ? maxHeartRate : null;

sleepRecordsBuffer.push({
  date: iso,
  from: fromDt.toISOString(),
  to: toDt.toISOString(),
  durationMinutes,
  durationHours,
  dayOfWeek,
  weekdayName: weekdayNames[dayOfWeek],
  avgHeartRate: validAvgHR,
  minHeartRate: validMinHR,
  maxHeartRate: validMaxHR
});
```

**Step 2: Add HR metrics to daily time series**

After storing the sleep record (around line 879-880), add HR metrics to the daily rowsBuffer:

```javascript
rowsBuffer.push({ metric: "sleep_bedtime_min", date: iso, value: bdMin });
rowsBuffer.push({ metric: "sleep_wake_min", date: iso, value: wdMin });

// Add HR daily metrics
if (validAvgHR !== null) {
  rowsBuffer.push({ metric: "sleep_avg_hr", date: iso, value: validAvgHR });
}
if (validMinHR !== null) {
  rowsBuffer.push({ metric: "sleep_min_hr", date: iso, value: validMinHR });
}
if (validMaxHR !== null) {
  rowsBuffer.push({ metric: "sleep_max_hr", date: iso, value: validMaxHR });
}
```

**Step 3: Test in browser**

1. Start server and open app
2. Clear existing data: Browser DevTools → Application → IndexedDB → Delete `smartwatch-viz` database
3. Load ZIP file from `data/raw/`
4. Open DevTools Console, check for:
   - No errors during ingestion
   - Log messages showing sleep records with HR data
5. Verify in IndexedDB:
   - Navigate to `sleepRecords` table
   - Confirm records have `avgHeartRate`, `minHeartRate`, `maxHeartRate` fields
   - Check that `daily` table has `sleep_avg_hr`, `sleep_min_hr`, `sleep_max_hr` metrics

**Expected:** HR data extracted and stored without errors

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: extract heart rate metrics from sleep.csv"
```

---

## Task 2: Create Daily Workout HR Aggregates

**Goal:** Calculate daily workout average HR and max HR from activity records

**Files:**
- Modify: `index.html:2219-2245` (fetchWorkoutAggregates function)

**Step 1: Extend fetchWorkoutAggregates to include HR**

Locate `fetchWorkoutAggregates()` function (around line 2219) and modify it to calculate HR aggregates:

```javascript
async function fetchWorkoutAggregates() {
  const records = await db.activityRecords.toArray();

  // Group by date
  const dailyMap = new Map();

  for (const record of records) {
    const date = record.date;
    if (!date) continue; // Skip records with missing dates
    if (!dailyMap.has(date)) {
      dailyMap.set(date, { count: 0, totalDuration: 0, hrValues: [], maxHR: null });
    }
    const day = dailyMap.get(date);
    day.count++;
    day.totalDuration += record.durationMinutes || 0;

    // Collect HR values for averaging
    if (record.hrAverage !== null && !isNaN(record.hrAverage)) {
      day.hrValues.push(record.hrAverage);
    }

    // Track max HR across all workouts
    if (record.hrMax !== null && !isNaN(record.hrMax)) {
      day.maxHR = day.maxHR === null ? record.hrMax : Math.max(day.maxHR, record.hrMax);
    }
  }

  // Convert to series format
  const dates = Array.from(dailyMap.keys()).sort();
  const countValues = dates.map(d => dailyMap.get(d).count);
  const durationValues = dates.map(d => dailyMap.get(d).totalDuration);

  // Calculate average HR across all workouts that day
  const avgHRValues = dates.map(d => {
    const hrValues = dailyMap.get(d).hrValues;
    if (hrValues.length === 0) return null;
    const sum = hrValues.reduce((acc, val) => acc + val, 0);
    return sum / hrValues.length;
  });

  // Max HR across all workouts that day
  const maxHRValues = dates.map(d => dailyMap.get(d).maxHR);

  return {
    workout_count: { dates, values: countValues },
    workout_total_duration: { dates, values: durationValues },
    workout_avg_hr: { dates, values: avgHRValues },
    workout_max_hr: { dates, values: maxHRValues }
  };
}
```

**Step 2: Test in browser**

1. Reload app (existing data should persist)
2. Open DevTools Console
3. Run manually:
   ```javascript
   fetchWorkoutAggregates().then(result => {
     console.log('Workout aggregates:', result);
     console.log('Sample avg HR:', result.workout_avg_hr.values.filter(v => v !== null).slice(0, 10));
     console.log('Sample max HR:', result.workout_max_hr.values.filter(v => v !== null).slice(0, 10));
   });
   ```
4. Verify output shows HR data

**Expected:** Function returns workout_avg_hr and workout_max_hr series with valid values

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: aggregate daily workout heart rate metrics"
```

---

## Task 3: Add HR-Based Correlation Pairs

**Goal:** Define ~25 new metric pairs involving heart rate data

**Files:**
- Modify: `index.html:2198-2213` (defineMetricPairs function)

**Step 1: Expand metric pairs definition**

Replace the `defineMetricPairs()` function with expanded list:

```javascript
function defineMetricPairs() {
  return [
    // ============================================
    // SLEEP QUALITY INSIGHTS (Sleep HR as target)
    // ============================================
    { independent: "aggregates_steps", dependent: "sleep_avg_hr", lag: "same_day", target: "sleep", label: "Steps → Sleep HR" },
    { independent: "workout_count", dependent: "sleep_avg_hr", lag: "same_day", target: "sleep", label: "Workout Count → Sleep HR" },
    { independent: "workout_total_duration", dependent: "sleep_avg_hr", lag: "same_day", target: "sleep", label: "Workout Duration → Sleep HR" },
    { independent: "workout_avg_hr", dependent: "sleep_avg_hr", lag: "same_day", target: "sleep", label: "Workout Intensity → Sleep HR" },
    { independent: "sleep_duration_min", dependent: "sleep_avg_hr", lag: "same_day", target: "sleep", label: "Sleep Duration → Sleep HR" },

    // ============================================
    // SLEEP DURATION INSIGHTS (existing + new)
    // ============================================
    { independent: "aggregates_steps", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Steps → Sleep Duration" },
    { independent: "workout_count", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Workout Count → Sleep Duration" },
    { independent: "workout_total_duration", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Workout Duration → Sleep Duration" },
    { independent: "workout_avg_hr", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Workout Intensity → Sleep Duration" },
    { independent: "sleep_duration_min", dependent: "sleep_duration_min", lag: "previous_day", target: "sleep", label: "Sleep → Next Night's Sleep" },
    { independent: "sleep_avg_hr", dependent: "sleep_duration_min", lag: "previous_day", target: "sleep", label: "Previous Sleep HR → Sleep Duration" },

    // ============================================
    // SLEEP TIMING INSIGHTS (existing + new)
    // ============================================
    { independent: "aggregates_steps", dependent: "sleep_bedtime_min", lag: "same_day", target: "sleep", label: "Steps → Bedtime" },
    { independent: "workout_count", dependent: "sleep_bedtime_min", lag: "same_day", target: "sleep", label: "Workout Count → Bedtime" },
    { independent: "workout_avg_hr", dependent: "sleep_bedtime_min", lag: "same_day", target: "sleep", label: "Workout Intensity → Bedtime" },

    // ============================================
    // ACTIVITY INSIGHTS (Activity as target)
    // ============================================
    { independent: "sleep_duration_min", dependent: "aggregates_steps", lag: "previous_day", target: "activity", label: "Sleep → Steps" },
    { independent: "sleep_avg_hr", dependent: "aggregates_steps", lag: "previous_day", target: "activity", label: "Sleep HR → Steps" },
    { independent: "sleep_duration_min", dependent: "workout_count", lag: "previous_day", target: "activity", label: "Sleep → Workout Count" },
    { independent: "sleep_avg_hr", dependent: "workout_count", lag: "previous_day", target: "activity", label: "Sleep HR → Workout Count" },
    { independent: "sleep_duration_min", dependent: "workout_total_duration", lag: "previous_day", target: "activity", label: "Sleep → Workout Duration" },
    { independent: "sleep_avg_hr", dependent: "workout_total_duration", lag: "previous_day", target: "activity", label: "Sleep HR → Workout Duration" },

    // ============================================
    // HEART RATE RECOVERY INSIGHTS (HR as target)
    // ============================================
    { independent: "workout_avg_hr", dependent: "sleep_avg_hr", lag: "same_day", target: "hr", label: "Workout Intensity → Recovery HR" },
    { independent: "aggregates_steps", dependent: "sleep_min_hr", lag: "same_day", target: "hr", label: "Steps → Resting HR" },
    { independent: "sleep_duration_min", dependent: "workout_avg_hr", lag: "previous_day", target: "hr", label: "Sleep → Workout Intensity" },
    { independent: "sleep_avg_hr", dependent: "workout_avg_hr", lag: "previous_day", target: "hr", label: "Sleep HR → Next Day Workout Intensity" },
  ];
}
```

**Step 2: Update metricsData in calculateAllCorrelations**

Locate `calculateAllCorrelations()` function (around line 2309) and update the metricsData object to include new HR metrics:

Find this section (around line 2320-2326):
```javascript
const metricsData = {
  "aggregates_steps": steps,
  "sleep_duration_min": sleepDuration,
  "sleep_bedtime_min": bedtime,
  "workout_count": workoutAggregates.workout_count,
  "workout_total_duration": workoutAggregates.workout_total_duration
};
```

Replace with:
```javascript
const metricsData = {
  "aggregates_steps": steps,
  "sleep_duration_min": sleepDuration,
  "sleep_bedtime_min": bedtime,
  "workout_count": workoutAggregates.workout_count,
  "workout_total_duration": workoutAggregates.workout_total_duration,
  "sleep_avg_hr": await fetchDailySeries("sleep_avg_hr"),
  "sleep_min_hr": await fetchDailySeries("sleep_min_hr"),
  "sleep_max_hr": await fetchDailySeries("sleep_max_hr"),
  "workout_avg_hr": workoutAggregates.workout_avg_hr,
  "workout_max_hr": workoutAggregates.workout_max_hr
};
```

**Step 3: Test in browser**

1. Navigate to Insights tab
2. Open DevTools Console
3. Look for log: "Calculating correlations..."
4. Check for log output showing new correlation pairs being calculated
5. Verify no JavaScript errors

**Expected:** Console shows ~25 correlations being calculated, including HR-based pairs

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add 25 heart rate correlation pairs"
```

---

## Task 4: Add Statistical Functions for Day Analysis

**Goal:** Implement t-test, ANOVA, and Cohen's d for categorical day analysis

**Files:**
- Modify: `index.html:2080` (after existing statistical functions)

**Step 1: Add statistical helper functions**

After `classifyCorrelationStrength()` function (around line 2130), add new statistical functions:

```javascript
/**
 * Calculate mean of an array
 * @param {Array<number>} values
 * @returns {number|null}
 */
function calculateMean(values) {
  if (!values || values.length === 0) return null;
  const validValues = values.filter(v => v !== null && !isNaN(v));
  if (validValues.length === 0) return null;
  return validValues.reduce((sum, v) => sum + v, 0) / validValues.length;
}

/**
 * Calculate standard deviation
 * @param {Array<number>} values
 * @returns {number|null}
 */
function calculateStdDev(values) {
  if (!values || values.length < 2) return null;
  const validValues = values.filter(v => v !== null && !isNaN(v));
  if (validValues.length < 2) return null;

  const mean = calculateMean(validValues);
  if (mean === null) return null;

  const squaredDiffs = validValues.map(v => Math.pow(v - mean, 2));
  const variance = squaredDiffs.reduce((sum, v) => sum + v, 0) / (validValues.length - 1);
  return Math.sqrt(variance);
}

/**
 * Two-sample t-test (Welch's t-test for unequal variances)
 * @param {Array<number>} group1
 * @param {Array<number>} group2
 * @returns {Object|null} {t, df, p, mean1, mean2, diff}
 */
function tTest(group1, group2) {
  const valid1 = group1.filter(v => v !== null && !isNaN(v));
  const valid2 = group2.filter(v => v !== null && !isNaN(v));

  if (valid1.length < 10 || valid2.length < 10) return null; // Minimum sample size

  const mean1 = calculateMean(valid1);
  const mean2 = calculateMean(valid2);
  const std1 = calculateStdDev(valid1);
  const std2 = calculateStdDev(valid2);

  if (mean1 === null || mean2 === null || std1 === null || std2 === null) return null;
  if (std1 === 0 && std2 === 0) return null; // No variance

  const n1 = valid1.length;
  const n2 = valid2.length;

  // Welch's t-statistic
  const var1 = Math.pow(std1, 2);
  const var2 = Math.pow(std2, 2);
  const t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);

  // Welch-Satterthwaite degrees of freedom
  const df = Math.pow(var1 / n1 + var2 / n2, 2) /
             (Math.pow(var1 / n1, 2) / (n1 - 1) + Math.pow(var2 / n2, 2) / (n2 - 1));

  // Approximate p-value using t-distribution (two-tailed)
  // For simplicity, use critical values: |t| > 2.0 ≈ p < 0.05, |t| > 2.6 ≈ p < 0.01
  let p;
  const absT = Math.abs(t);
  if (absT > 2.6) p = 0.01;
  else if (absT > 2.0) p = 0.05;
  else p = 0.10; // Not significant

  return {
    t,
    df,
    p,
    mean1,
    mean2,
    diff: mean1 - mean2,
    n1,
    n2
  };
}

/**
 * Cohen's d effect size
 * @param {Array<number>} group1
 * @param {Array<number>} group2
 * @returns {number|null}
 */
function cohensD(group1, group2) {
  const valid1 = group1.filter(v => v !== null && !isNaN(v));
  const valid2 = group2.filter(v => v !== null && !isNaN(v));

  if (valid1.length < 2 || valid2.length < 2) return null;

  const mean1 = calculateMean(valid1);
  const mean2 = calculateMean(valid2);
  const std1 = calculateStdDev(valid1);
  const std2 = calculateStdDev(valid2);

  if (mean1 === null || mean2 === null || std1 === null || std2 === null) return null;

  const n1 = valid1.length;
  const n2 = valid2.length;

  // Pooled standard deviation
  const pooledStd = Math.sqrt(((n1 - 1) * Math.pow(std1, 2) + (n2 - 1) * Math.pow(std2, 2)) / (n1 + n2 - 2));

  if (pooledStd === 0) return null;

  return (mean1 - mean2) / pooledStd;
}

/**
 * Classify effect size magnitude
 * @param {number} d - Cohen's d
 * @returns {string} "small" | "medium" | "large"
 */
function classifyEffectSize(d) {
  const absD = Math.abs(d);
  if (absD >= 0.8) return "large";
  if (absD >= 0.5) return "medium";
  if (absD >= 0.2) return "small";
  return "negligible";
}
```

**Step 2: Test statistical functions**

Open DevTools Console and run:
```javascript
// Test t-test
const weekday = [420, 400, 390, 410, 405, 415, 408, 412, 395, 405, 410, 415];
const weekend = [480, 470, 465, 475, 485, 490, 478, 482, 475, 480, 485, 488];
const result = tTest(weekday, weekend);
console.log('t-test result:', result);
console.log('Effect size:', cohensD(weekday, weekend));
```

**Expected:** Console shows t-test result with p < 0.05 and large negative effect size

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add t-test and effect size statistical functions"
```

---

## Task 5: Implement Day Pattern Analysis

**Goal:** Calculate weekend vs weekday comparisons and day-of-week patterns

**Files:**
- Modify: `index.html` (add new function after statistical helpers)

**Step 1: Add calculateDayPatterns function**

After the statistical helper functions added in Task 4, add:

```javascript
/**
 * Calculate day-of-week patterns for all metrics
 * @returns {Promise<Object>} {weekendVsWeekday: [...], dayOfWeek: [...]}
 */
async function calculateDayPatterns() {
  console.log("Calculating day patterns...");

  const patterns = {
    weekendVsWeekday: [],
    dayOfWeek: []
  };

  // Metrics to analyze
  const metricsToAnalyze = [
    { name: "sleep_duration_min", label: "Sleep Duration", unit: "min", formatFn: (v) => `${Math.round(v / 60 * 10) / 10}h` },
    { name: "sleep_avg_hr", label: "Sleep Heart Rate", unit: "bpm", formatFn: (v) => `${Math.round(v)} bpm` },
    { name: "aggregates_steps", label: "Steps", unit: "steps", formatFn: (v) => `${Math.round(v).toLocaleString()} steps` },
    { name: "workout_count", label: "Workouts", unit: "count", formatFn: (v) => `${Math.round(v * 10) / 10}` },
    { name: "workout_avg_hr", label: "Workout Heart Rate", unit: "bpm", formatFn: (v) => `${Math.round(v)} bpm` }
  ];

  // Fetch sleep records for day-of-week grouping
  const sleepRecords = await db.sleepRecords.toArray();

  for (const metric of metricsToAnalyze) {
    // Fetch metric data
    const series = await fetchDailySeries(metric.name);
    if (!series || series.values.length < 28) continue; // Need at least 4 weeks

    // Group by weekend vs weekday
    const weekendValues = [];
    const weekdayValues = [];

    // Group by day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
    const dayGroups = Array.from({ length: 7 }, () => []);

    for (let i = 0; i < series.dates.length; i++) {
      const date = series.dates[i];
      const value = series.values[i];
      if (value === null || isNaN(value)) continue;

      // Find corresponding sleep record to get day of week
      const sleepRecord = sleepRecords.find(r => r.date === date);
      if (!sleepRecord) continue;

      const dayOfWeek = sleepRecord.dayOfWeek;
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sunday or Saturday

      if (isWeekend) {
        weekendValues.push(value);
      } else {
        weekdayValues.push(value);
      }

      dayGroups[dayOfWeek].push(value);
    }

    // Weekend vs Weekday t-test
    if (weekendValues.length >= 10 && weekdayValues.length >= 10) {
      const tTestResult = tTest(weekendValues, weekdayValues);
      if (tTestResult && tTestResult.p <= 0.05) {
        const effectSize = cohensD(weekendValues, weekdayValues);
        const effectMagnitude = classifyEffectSize(effectSize);

        patterns.weekendVsWeekday.push({
          metric: metric.name,
          label: metric.label,
          unit: metric.unit,
          formatFn: metric.formatFn,
          weekendMean: tTestResult.mean1,
          weekdayMean: tTestResult.mean2,
          diff: tTestResult.diff,
          p: tTestResult.p,
          effectSize,
          effectMagnitude,
          weekendN: tTestResult.n1,
          weekdayN: tTestResult.n2
        });
      }
    }

    // Day-of-week patterns - find days that stand out
    const allValues = series.values.filter(v => v !== null && !isNaN(v));
    const overallMean = calculateMean(allValues);
    if (overallMean === null) continue;

    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    for (let day = 0; day < 7; day++) {
      const dayValues = dayGroups[day];
      if (dayValues.length < 10) continue; // Need minimum sample size

      const dayMean = calculateMean(dayValues);
      const diff = dayMean - overallMean;
      const percentDiff = (diff / overallMean) * 100;

      // Only report if difference is meaningful (>10% or significant t-test vs rest)
      if (Math.abs(percentDiff) > 10) {
        // Create "rest of week" group
        const restValues = [];
        for (let otherDay = 0; otherDay < 7; otherDay++) {
          if (otherDay !== day) restValues.push(...dayGroups[otherDay]);
        }

        const tTestResult = tTest(dayValues, restValues);
        if (tTestResult && tTestResult.p <= 0.05) {
          patterns.dayOfWeek.push({
            metric: metric.name,
            label: metric.label,
            unit: metric.unit,
            formatFn: metric.formatFn,
            day: dayNames[day],
            dayMean,
            overallMean,
            diff,
            percentDiff,
            p: tTestResult.p,
            n: dayValues.length
          });
        }
      }
    }
  }

  console.log(`Found ${patterns.weekendVsWeekday.length} weekend/weekday patterns, ${patterns.dayOfWeek.length} day-of-week standouts`);
  return patterns;
}
```

**Step 2: Test in browser**

Open DevTools Console:
```javascript
calculateDayPatterns().then(result => {
  console.log('Weekend vs Weekday:', result.weekendVsWeekday);
  console.log('Day standouts:', result.dayOfWeek);
});
```

**Expected:** Console shows patterns found, with statistical significance

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: calculate weekend vs weekday and day-of-week patterns"
```

---

## Task 6: Implement Segmented Correlations

**Goal:** Split correlations by weekend/weekday context

**Files:**
- Modify: `index.html` (add new function after calculateDayPatterns)

**Step 1: Add calculateSegmentedCorrelations function**

```javascript
/**
 * Calculate how correlations vary by weekend vs weekday
 * @param {Array} correlations - Existing correlation objects
 * @returns {Promise<Array>} Segmented correlation insights
 */
async function calculateSegmentedCorrelations(correlations) {
  console.log("Calculating segmented correlations...");

  const segmented = [];
  const sleepRecords = await db.sleepRecords.toArray();

  // Create date-to-dayOfWeek lookup
  const dateToDay = new Map();
  sleepRecords.forEach(r => {
    dateToDay.set(r.date, r.dayOfWeek);
  });

  for (const corr of correlations) {
    // Only segment moderate/strong correlations
    if (corr.strength === 'weak' || corr.strength === 'none') continue;

    // Get the original aligned data
    const indData = { dates: [], values: [] };
    const depData = { dates: [], values: [] };

    // Re-fetch metrics (this is a bit inefficient but ensures consistency)
    // In practice, we could cache this in calculateAllCorrelations
    let indSeries, depSeries;

    // Helper to fetch series by metric name
    const fetchMetric = async (metricName) => {
      if (metricName === "workout_count" || metricName === "workout_total_duration" ||
          metricName === "workout_avg_hr" || metricName === "workout_max_hr") {
        const agg = await fetchWorkoutAggregates();
        return agg[metricName];
      } else {
        return await fetchDailySeries(metricName);
      }
    };

    indSeries = await fetchMetric(corr.independent);
    depSeries = await fetchMetric(corr.dependent);

    if (!indSeries || !depSeries) continue;

    // Align and segment
    const aligned = alignTimeSeries(indSeries, depSeries, corr.lag);
    if (!aligned || aligned.x.length < 28) continue; // Need enough data

    // Split into weekend/weekday
    const weekendX = [], weekendY = [];
    const weekdayX = [], weekdayY = [];

    for (let i = 0; i < aligned.dates.length; i++) {
      const date = aligned.dates[i];
      const dayOfWeek = dateToDay.get(date);
      if (dayOfWeek === undefined) continue;

      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
      const x = aligned.x[i];
      const y = aligned.y[i];

      if (x === null || y === null || isNaN(x) || isNaN(y)) continue;

      if (isWeekend) {
        weekendX.push(x);
        weekendY.push(y);
      } else {
        weekdayX.push(x);
        weekdayY.push(y);
      }
    }

    // Calculate correlations for each segment
    if (weekendX.length < 20 || weekdayX.length < 20) continue; // Minimum sample per segment

    const weekendR = calculatePearsonCorrelation(weekendX, weekendY);
    const weekdayR = calculatePearsonCorrelation(weekdayX, weekdayY);

    if (weekendR === null || weekdayR === null) continue;

    const rDiff = Math.abs(weekendR - weekdayR);

    // Only report if difference is meaningful (≥0.15)
    if (rDiff >= 0.15) {
      const weekendStrength = classifyCorrelationStrength(weekendR);
      const weekdayStrength = classifyCorrelationStrength(weekdayR);

      segmented.push({
        baseCorrelation: corr.label,
        independent: corr.independent,
        dependent: corr.dependent,
        weekendR,
        weekendStrength,
        weekendN: weekendX.length,
        weekdayR,
        weekdayStrength,
        weekdayN: weekdayX.length,
        rDiff,
        interpretation: Math.abs(weekdayR) > Math.abs(weekendR)
          ? "Stronger on weekdays"
          : "Stronger on weekends"
      });
    }
  }

  console.log(`Found ${segmented.length} segmented correlation patterns`);
  return segmented;
}
```

**Step 2: Test in browser**

Open DevTools Console:
```javascript
// First get correlations
calculateAllCorrelations().then(correlations => {
  return calculateSegmentedCorrelations(correlations);
}).then(result => {
  console.log('Segmented correlations:', result);
});
```

**Expected:** Console shows segmented correlations with weekend/weekday split

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: calculate segmented correlations by weekend/weekday"
```

---

## Task 7: Reorganize Insights - New Organizer Function

**Goal:** Replace organizeCorrelations with organizeAllInsights that combines all analysis types

**Files:**
- Modify: `index.html:2880` (replace organizeCorrelations function)

**Step 1: Create organizeAllInsights function**

Replace the `organizeCorrelations()` function (around line 2880) with new comprehensive organizer:

```javascript
/**
 * Organize all insights (correlations, day patterns, segmented) for UI rendering
 * @param {Array} correlations - Metric correlations
 * @param {Object} dayPatterns - {weekendVsWeekday: [], dayOfWeek: []}
 * @param {Array} segmented - Segmented correlations
 * @returns {Object} Organized insights for rendering
 */
function organizeAllInsights(correlations, dayPatterns, segmented) {
  console.log("Organizing all insights...");

  // Filter out weak correlations with early confidence
  const qualityCorrelations = correlations.filter(c => {
    if (c.strength === 'none' || c.r === null) return false;
    if (c.strength === 'weak' && c.sampleSize < 30) return false;
    return true;
  });

  // Create scoreable items from all three sources
  const allFindings = [];

  // Add correlations
  qualityCorrelations.forEach(c => {
    const score = Math.abs(c.r) * Math.min(c.sampleSize / 100, 1) * (c.strength === 'strong' ? 1.5 : c.strength === 'moderate' ? 1.2 : 1);
    allFindings.push({
      type: 'correlation',
      score,
      data: c
    });
  });

  // Add weekend vs weekday patterns
  dayPatterns.weekendVsWeekday.forEach(p => {
    // Score based on effect size and significance
    const effectScore = Math.abs(p.effectSize);
    const pScore = p.p <= 0.01 ? 1.5 : 1.0;
    const score = effectScore * pScore;
    allFindings.push({
      type: 'weekendVsWeekday',
      score,
      data: p
    });
  });

  // Add day-of-week standouts
  dayPatterns.dayOfWeek.forEach(p => {
    const score = Math.abs(p.percentDiff / 10) * (p.p <= 0.01 ? 1.3 : 1.0);
    allFindings.push({
      type: 'dayStandout',
      score,
      data: p
    });
  });

  // Add segmented correlations
  segmented.forEach(s => {
    const score = s.rDiff * 1.2; // Boost segmented findings as they show context
    allFindings.push({
      type: 'segmented',
      score,
      data: s
    });
  });

  // Sort by score and pick top 3 discoveries
  allFindings.sort((a, b) => b.score - a.score);
  const topDiscoveries = allFindings.slice(0, 3);

  // Organize correlations by target
  const topDiscoveryIds = new Set(topDiscoveries.filter(f => f.type === 'correlation').map(f => f.data.id));
  const remaining = qualityCorrelations.filter(c => !topDiscoveryIds.has(c.id));

  const sleepInsights = remaining.filter(c => c.target === 'sleep');
  const activityInsights = remaining.filter(c => c.target === 'activity');
  const hrInsights = remaining.filter(c => c.target === 'hr');

  const organizeSectionByStrength = (insights) => {
    const strong = insights.filter(c => c.strength === 'strong' || c.strength === 'moderate');
    const weak = insights.filter(c => c.strength === 'weak');
    return { strong, weak };
  };

  return {
    topDiscoveries,
    dayPatterns: {
      weekendVsWeekday: dayPatterns.weekendVsWeekday,
      dayOfWeek: dayPatterns.dayOfWeek
    },
    correlations: {
      sleep: organizeSectionByStrength(sleepInsights),
      activity: organizeSectionByStrength(activityInsights),
      hr: organizeSectionByStrength(hrInsights)
    },
    segmented
  };
}
```

**Step 2: Test organizing logic**

Open DevTools Console:
```javascript
// Test with mock data
const mockCorr = [{id: 1, r: 0.45, strength: 'moderate', sampleSize: 50, target: 'sleep'}];
const mockDay = {weekendVsWeekday: [{effectSize: 0.9, p: 0.01}], dayOfWeek: []};
const mockSeg = [{rDiff: 0.25}];
const result = organizeAllInsights(mockCorr, mockDay, mockSeg);
console.log('Organized:', result);
```

**Expected:** Returns organized structure with topDiscoveries, dayPatterns, correlations, segmented

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: create organizeAllInsights to combine all analysis types"
```

---

## Task 8: Render Day Patterns Section

**Goal:** Create UI rendering for weekend vs weekday and day-of-week patterns

**Files:**
- Modify: `index.html` (add new function after organizeAllInsights)

**Step 1: Add renderDayPatternsSection function**

```javascript
/**
 * Render Day Patterns section
 * @param {Object} dayPatterns - {weekendVsWeekday: [], dayOfWeek: []}
 * @param {HTMLElement} container - DOM container element
 */
function renderDayPatternsSection(dayPatterns, container) {
  if (!container) return;

  container.innerHTML = '';

  const hasWeekendPatterns = dayPatterns.weekendVsWeekday.length > 0;
  const hasDayPatterns = dayPatterns.dayOfWeek.length > 0;

  if (!hasWeekendPatterns && !hasDayPatterns) {
    container.innerHTML = '<div class="muted" style="text-align:center; padding:40px;">No significant day patterns found. Keep tracking!</div>';
    return;
  }

  let html = '';

  // Weekend vs Weekday patterns
  if (hasWeekendPatterns) {
    html += `
      <div class="card" style="margin-bottom: 16px;">
        <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">Weekend vs Weekday</h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
    `;

    dayPatterns.weekendVsWeekday.forEach(pattern => {
      const direction = pattern.diff > 0 ? 'higher' : 'lower';
      const arrow = pattern.diff > 0 ? '↑' : '↓';
      const color = pattern.diff > 0 ? 'var(--good)' : 'var(--accent)';
      const pStar = pattern.p <= 0.01 ? '**' : '*';

      html += `
        <div style="background: #0f1521; border: 1px solid #223046; border-radius: 8px; padding: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="font-size: 14px;">${pattern.label}</strong>
            <span style="color: ${color}; font-size: 14px; font-weight: 600;">${arrow} ${pattern.formatFn(Math.abs(pattern.diff))}</span>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
            <div>
              <div style="color: var(--muted);">Weekend</div>
              <div style="font-weight: 600;">${pattern.formatFn(pattern.weekendMean)}</div>
            </div>
            <div>
              <div style="color: var(--muted);">Weekday</div>
              <div style="font-weight: 600;">${pattern.formatFn(pattern.weekdayMean)}</div>
            </div>
          </div>
          <div style="margin-top: 8px; font-size: 12px; color: var(--muted);">
            ${pattern.effectMagnitude} effect (d=${pattern.effectSize.toFixed(2)})${pStar}
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  }

  // Day-of-week standouts
  if (hasDayPatterns) {
    html += `
      <div class="card">
        <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">Day-of-Week Standouts</h3>
        <div style="display: flex; flex-direction: column; gap: 8px;">
    `;

    dayPatterns.dayOfWeek.forEach(pattern => {
      const direction = pattern.diff > 0 ? 'above' : 'below';
      const arrow = pattern.diff > 0 ? '↑' : '↓';
      const color = pattern.diff > 0 ? 'var(--good)' : 'var(--warn)';

      html += `
        <div style="background: #0f1521; border: 1px solid #223046; border-radius: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong style="font-size: 13px;">${pattern.day}s: ${pattern.label}</strong>
            <div style="font-size: 12px; color: var(--muted); margin-top: 2px;">
              ${pattern.formatFn(pattern.dayMean)} vs ${pattern.formatFn(pattern.overallMean)} weekly avg
            </div>
          </div>
          <div style="text-align: right;">
            <div style="color: ${color}; font-weight: 600; font-size: 14px;">
              ${arrow} ${pattern.formatFn(Math.abs(pattern.diff))}
            </div>
            <div style="font-size: 11px; color: var(--muted);">
              ${Math.abs(pattern.percentDiff).toFixed(0)}% ${direction}
            </div>
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}
```

**Step 2: Test rendering**

Add temporary test button to HTML (in the control panel section around line 160):
```html
<button id="testDayPatternsBtn">Test Day Patterns Render</button>
```

Add click handler in JavaScript (around line 5150):
```javascript
if ($("testDayPatternsBtn")) {
  $("testDayPatternsBtn").addEventListener("click", async () => {
    const patterns = await calculateDayPatterns();
    const testContainer = document.createElement('div');
    document.querySelector('main').appendChild(testContainer);
    renderDayPatternsSection(patterns, testContainer);
  });
}
```

**Step 3: Verify in browser**

1. Click "Test Day Patterns Render" button
2. Check that cards render with weekend/weekday comparisons
3. Verify styling matches existing design
4. Remove test button and handler after verification

**Expected:** Day patterns render with proper formatting and statistics

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: render day patterns section with weekend/weekday comparison"
```

---

## Task 9: Render Segmented Insights Section

**Goal:** Create UI for segmented correlation insights

**Files:**
- Modify: `index.html` (add new function after renderDayPatternsSection)

**Step 1: Add renderSegmentedSection function**

```javascript
/**
 * Render Segmented Insights section
 * @param {Array} segmented - Segmented correlation objects
 * @param {HTMLElement} container - DOM container element
 */
function renderSegmentedSection(segmented, container) {
  if (!container) return;

  container.innerHTML = '';

  if (segmented.length === 0) {
    container.innerHTML = '<div class="muted" style="text-align:center; padding:40px;">No context-dependent correlations found</div>';
    return;
  }

  let html = `
    <div class="card">
      <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">How Correlations Vary by Context</h3>
      <div style="display: flex; flex-direction: column; gap: 12px;">
  `;

  segmented.forEach(seg => {
    const strongerContext = Math.abs(seg.weekdayR) > Math.abs(seg.weekendR) ? 'weekday' : 'weekend';
    const weaker = strongerContext === 'weekday' ? 'weekend' : 'weekday';
    const strongerR = strongerContext === 'weekday' ? seg.weekdayR : seg.weekendR;
    const weakerR = strongerContext === 'weekday' ? seg.weekendR : seg.weekdayR;

    html += `
      <div style="background: #0f1521; border: 1px solid #223046; border-radius: 8px; padding: 12px;">
        <div style="margin-bottom: 10px;">
          <strong style="font-size: 14px;">${seg.baseCorrelation}</strong>
          <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">${seg.interpretation}</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
          <div style="background: ${strongerContext === 'weekday' ? 'rgba(58,160,255,0.08)' : '#0b1018'}; border: 1px solid ${strongerContext === 'weekday' ? '#2b66b6' : '#1a2332'}; border-radius: 6px; padding: 8px;">
            <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px;">Weekday</div>
            <div style="font-weight: 600; margin-top: 4px;">r = ${seg.weekdayR.toFixed(3)}</div>
            <div style="font-size: 11px; color: var(--muted); margin-top: 2px;">${seg.weekdayStrength}</div>
            <div style="font-size: 11px; color: var(--muted);">n = ${seg.weekdayN}</div>
          </div>

          <div style="background: ${strongerContext === 'weekend' ? 'rgba(58,160,255,0.08)' : '#0b1018'}; border: 1px solid ${strongerContext === 'weekend' ? '#2b66b6' : '#1a2332'}; border-radius: 6px; padding: 8px;">
            <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px;">Weekend</div>
            <div style="font-weight: 600; margin-top: 4px;">r = ${seg.weekendR.toFixed(3)}</div>
            <div style="font-size: 11px; color: var(--muted); margin-top: 2px;">${seg.weekendStrength}</div>
            <div style="font-size: 11px; color: var(--muted);">n = ${seg.weekendN}</div>
          </div>
        </div>

        <div style="margin-top: 8px; font-size: 12px; color: var(--muted);">
          Difference: Δr = ${seg.rDiff.toFixed(3)}
        </div>
      </div>
    `;
  });

  html += `
      </div>
    </div>
  `;

  container.innerHTML = html;
}
```

**Step 2: Test rendering**

Add temporary test in browser console:
```javascript
calculateAllCorrelations().then(correlations => {
  return calculateSegmentedCorrelations(correlations);
}).then(segmented => {
  const testContainer = document.createElement('div');
  document.querySelector('main').appendChild(testContainer);
  renderSegmentedSection(segmented, testContainer);
});
```

**Expected:** Segmented insights render with weekend/weekday comparison cards

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: render segmented insights showing context-dependent correlations"
```

---

## Task 10: Render Top Discoveries Section

**Goal:** Create universal top discoveries renderer supporting all finding types

**Files:**
- Modify: `index.html` (add new function)

**Step 1: Add renderTopDiscoveries function**

```javascript
/**
 * Render Top Discoveries section (mixed finding types)
 * @param {Array} topDiscoveries - Array of {type, score, data} objects
 * @param {HTMLElement} container - DOM container element
 */
function renderTopDiscoveries(topDiscoveries, container) {
  if (!container) return;

  container.innerHTML = '';

  if (topDiscoveries.length === 0) {
    return; // Don't show empty state - let individual sections handle it
  }

  let html = '';

  topDiscoveries.forEach((finding, index) => {
    const badge = finding.type === 'correlation' ? '📊 Correlation' :
                  finding.type === 'weekendVsWeekday' ? '📅 Day Pattern' :
                  finding.type === 'dayStandout' ? '📅 Day Pattern' :
                  finding.type === 'segmented' ? '🔍 Segmented' : '';

    html += `<div style="margin-bottom: 12px; padding: 2px 0;">`;
    html += `<div style="font-size: 11px; color: var(--muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.8px;">${badge}</div>`;

    if (finding.type === 'correlation') {
      html += renderPatternCard(finding.data, true);
    } else if (finding.type === 'weekendVsWeekday') {
      const p = finding.data;
      const direction = p.diff > 0 ? 'higher' : 'lower';
      const arrow = p.diff > 0 ? '↑' : '↓';
      const color = p.diff > 0 ? 'var(--good)' : 'var(--accent)';

      html += `
        <div class="correlation-pattern-card" style="background: linear-gradient(135deg, rgba(58,160,255,0.08), rgba(61,206,121,0.06)); border: 2px solid #2b66b6; box-shadow: 0 4px 12px rgba(58,160,255,0.15); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <div>
              <strong style="font-size: 15px;">${p.label}</strong>
              <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">Weekend vs Weekday difference</div>
            </div>
            <span style="color: ${color}; font-size: 16px; font-weight: 700;">${arrow} ${p.formatFn(Math.abs(p.diff))}</span>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px;">
            <div style="background: rgba(0,0,0,0.2); border-radius: 6px; padding: 8px;">
              <div style="color: var(--muted); font-size: 12px;">Weekend</div>
              <div style="font-weight: 600; font-size: 14px; margin-top: 2px;">${p.formatFn(p.weekendMean)}</div>
            </div>
            <div style="background: rgba(0,0,0,0.2); border-radius: 6px; padding: 8px;">
              <div style="color: var(--muted); font-size: 12px;">Weekday</div>
              <div style="font-weight: 600; font-size: 14px; margin-top: 2px;">${p.formatFn(p.weekdayMean)}</div>
            </div>
          </div>
          <div style="margin-top: 10px; font-size: 12px; color: var(--muted);">
            ${p.effectMagnitude} effect (n=${p.weekendN + p.weekdayN})
          </div>
        </div>
      `;
    } else if (finding.type === 'dayStandout') {
      const p = finding.data;
      const arrow = p.diff > 0 ? '↑' : '↓';
      const color = p.diff > 0 ? 'var(--good)' : 'var(--warn)';

      html += `
        <div class="correlation-pattern-card" style="background: linear-gradient(135deg, rgba(255,191,58,0.1), rgba(58,160,255,0.06)); border: 2px solid rgba(255,191,58,0.4); box-shadow: 0 4px 12px rgba(255,191,58,0.12); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
              <strong style="font-size: 15px;">${p.day}s: ${p.label}</strong>
              <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">
                ${p.formatFn(p.dayMean)} vs ${p.formatFn(p.overallMean)} weekly average
              </div>
            </div>
            <div style="text-align: right;">
              <div style="color: ${color}; font-weight: 700; font-size: 16px;">
                ${arrow} ${p.formatFn(Math.abs(p.diff))}
              </div>
              <div style="font-size: 12px; color: var(--muted);">
                ${Math.abs(p.percentDiff).toFixed(0)}% different
              </div>
            </div>
          </div>
        </div>
      `;
    } else if (finding.type === 'segmented') {
      const s = finding.data;
      html += `
        <div class="correlation-pattern-card" style="background: linear-gradient(135deg, rgba(147,51,234,0.08), rgba(58,160,255,0.06)); border: 2px solid rgba(147,51,234,0.4); box-shadow: 0 4px 12px rgba(147,51,234,0.12); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
          <strong style="font-size: 15px;">${s.baseCorrelation}</strong>
          <div style="font-size: 13px; color: var(--muted); margin-top: 4px; margin-bottom: 12px;">${s.interpretation}</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div style="background: rgba(0,0,0,0.2); border-radius: 6px; padding: 8px;">
              <div style="font-size: 11px; color: var(--muted);">WEEKDAY</div>
              <div style="font-weight: 600; margin-top: 4px;">r = ${s.weekdayR.toFixed(3)}</div>
              <div style="font-size: 11px; color: var(--muted);">${s.weekdayStrength}</div>
            </div>
            <div style="background: rgba(0,0,0,0.2); border-radius: 6px; padding: 8px;">
              <div style="font-size: 11px; color: var(--muted);">WEEKEND</div>
              <div style="font-weight: 600; margin-top: 4px;">r = ${s.weekendR.toFixed(3)}</div>
              <div style="font-size: 11px; color: var(--muted);">${s.weekendStrength}</div>
            </div>
          </div>
        </div>
      `;
    }

    html += `</div>`;
  });

  container.innerHTML = html;
}
```

**Step 2: Test rendering with mixed findings**

Browser console:
```javascript
const mockDiscoveries = [
  {type: 'weekendVsWeekday', score: 2.5, data: {label: 'Sleep', diff: 45, weekendMean: 450, weekdayMean: 405, formatFn: (v) => `${Math.round(v/60)}h`, effectMagnitude: 'large', weekendN: 50, weekdayN: 150}},
  {type: 'correlation', score: 2.0, data: {id: 1, label: 'Steps → Sleep', r: 0.45, strength: 'moderate', direction: 'positive', sampleSize: 100}},
  {type: 'dayStandout', score: 1.8, data: {day: 'Monday', label: 'Steps', diff: -2000, dayMean: 8000, overallMean: 10000, percentDiff: -20, formatFn: (v) => `${v.toLocaleString()}`}}
];

const testContainer = document.createElement('div');
document.querySelector('main').appendChild(testContainer);
renderTopDiscoveries(mockDiscoveries, testContainer);
```

**Expected:** Mixed finding types render with distinct visual styling

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: render top discoveries with support for all finding types"
```

---

## Task 11: Update Correlation Dashboard - Main Orchestrator

**Goal:** Modify renderCorrelationDashboard to calculate and render all analysis types

**Files:**
- Modify: `index.html:5007-5116` (renderCorrelationDashboard function)

**Step 1: Update renderCorrelationDashboard function**

Replace the `renderCorrelationDashboard()` function with:

```javascript
/**
 * Main correlation dashboard rendering function - orchestrates all analysis
 */
async function renderCorrelationDashboard() {
  console.log("Rendering correlation dashboard...");

  // Get DOM containers
  const topContainer = $("correlationTopDiscoveries");
  const dayPatternsContainer = $("correlationDayPatterns");
  const sleepContainer = $("correlationSleepInsights");
  const activityContainer = $("correlationActivityInsights");
  const hrContainer = $("correlationHRInsights");
  const segmentedContainer = $("correlationSegmentedInsights");

  try {
    // Calculate all three analysis types in parallel
    const [correlations, dayPatterns] = await Promise.all([
      calculateAllCorrelations(),
      calculateDayPatterns()
    ]);

    // Calculate segmented correlations (depends on correlations)
    const segmented = await calculateSegmentedCorrelations(correlations);

    // Cache for scatter plot rendering
    window.cachedCorrelations = correlations;

    // Check if we have any findings at all
    const hasFindings = correlations.length > 0 ||
                       dayPatterns.weekendVsWeekday.length > 0 ||
                       dayPatterns.dayOfWeek.length > 0 ||
                       segmented.length > 0;

    if (!hasFindings) {
      const minDaysNeeded = 14;
      renderNoCorrelationsFound(minDaysNeeded, topContainer);
      if (dayPatternsContainer) dayPatternsContainer.innerHTML = '';
      if (sleepContainer) sleepContainer.innerHTML = '';
      if (activityContainer) activityContainer.innerHTML = '';
      if (hrContainer) hrContainer.innerHTML = '';
      if (segmentedContainer) segmentedContainer.innerHTML = '';
      return;
    }

    // Organize all insights
    const organized = organizeAllInsights(correlations, dayPatterns, segmented);

    // Render Top Discoveries
    if (topContainer && organized.topDiscoveries.length > 0) {
      renderTopDiscoveries(organized.topDiscoveries, topContainer);
    } else if (topContainer) {
      topContainer.innerHTML = '';
    }

    // Render Day Patterns
    if (dayPatternsContainer) {
      renderDayPatternsSection(organized.dayPatterns, dayPatternsContainer);
    }

    // Render Metric Correlations - Sleep
    if (sleepContainer) {
      if (organized.correlations.sleep.strong.length > 0) {
        const html = organized.correlations.sleep.strong.map(c => renderPatternCard(c, false)).join('');
        sleepContainer.innerHTML = html;
      } else {
        sleepContainer.innerHTML = '<div class="muted" style="text-align:center; padding:20px;">No significant sleep correlations found</div>';
      }
    }

    // Render Metric Correlations - Activity
    if (activityContainer) {
      if (organized.correlations.activity.strong.length > 0) {
        const html = organized.correlations.activity.strong.map(c => renderPatternCard(c, false)).join('');
        activityContainer.innerHTML = html;
      } else {
        activityContainer.innerHTML = '<div class="muted" style="text-align:center; padding:20px;">No significant activity correlations found</div>';
      }
    }

    // Render Metric Correlations - Heart Rate (NEW)
    if (hrContainer) {
      if (organized.correlations.hr.strong.length > 0) {
        const html = organized.correlations.hr.strong.map(c => renderPatternCard(c, false)).join('');
        hrContainer.innerHTML = html;
      } else {
        hrContainer.innerHTML = '<div class="muted" style="text-align:center; padding:20px;">No significant heart rate correlations found</div>';
      }
    }

    // Render Segmented Insights
    if (segmentedContainer) {
      renderSegmentedSection(organized.segmented, segmentedContainer);
    }

    console.log("Correlation dashboard rendered");

  } catch (error) {
    console.error("Error rendering correlation dashboard:", error);
    if (topContainer) {
      topContainer.innerHTML = `<div style="text-align:center; padding:40px; color:var(--bad);">Error loading insights. Check console for details.</div>`;
    }
  }
}
```

**Step 2: Test full dashboard render**

1. Open app and navigate to Insights tab
2. Check DevTools Console for:
   - "Calculating correlations..."
   - "Calculating day patterns..."
   - "Calculating segmented correlations..."
   - "Organizing all insights..."
   - "Correlation dashboard rendered"
3. Verify all sections render without errors

**Expected:** Full dashboard renders with all analysis types

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: orchestrate all analysis types in correlation dashboard"
```

---

## Task 12: Update HTML Structure for New Sections

**Goal:** Add DOM containers for day patterns, HR insights, and segmented insights

**Files:**
- Modify: `index.html:366-408` (correlationCharts section)

**Step 1: Reorganize correlation dashboard HTML**

Find the `<div id="correlationCharts">` section (around line 366) and replace the content with new structure:

```html
<div id="correlationCharts" style="display:none; margin-top:10px;">

  <!-- Disclaimer card -->
  <div class="card" id="correlationDisclaimer" style="background: rgba(255,191,58,0.08); border: 1px solid rgba(255,191,58,0.25); margin-bottom: 16px;">
    <div style="padding: 4px;">
      <h2 style="margin: 0 0 8px 0; color: #ffd68a; font-size: 15px; text-transform: none; letter-spacing: 0;">Remember: Correlation ≠ Causation</h2>
      <p style="margin: 0; font-size: 13px; line-height: 1.5; color: var(--muted);">
        These patterns show associations in your data, not proof of cause and effect.
        <a href="https://en.wikipedia.org/wiki/Correlation_does_not_imply_causation" target="_blank" rel="noopener" style="color: #3aa0ff; text-decoration: none; border-bottom: 1px dotted #3aa0ff;">Learn more</a>
      </p>
      <p style="margin: 8px 0 0 0; font-size: 12px; line-height: 1.4; color: var(--muted); font-style: italic;">
        "Correlation does not imply causation"
        means that just because two things are related doesn't mean one causes the other.
        For instance, ice cream sales and drowning deaths both increase in summer,
        but ice cream doesn't cause drowning — warm weather causes both.
      </p>
    </div>
  </div>

  <!-- 1. TOP DISCOVERIES -->
  <div class="card" style="margin-bottom: 16px;">
    <h2>Top Discoveries</h2>
    <div id="correlationTopDiscoveries"></div>
  </div>

  <!-- 2. DAY PATTERNS (NEW) -->
  <div style="margin-bottom: 16px;">
    <h2 style="margin: 0 0 12px 0; font-size: 16px; color: var(--fg); font-weight: 600;">Day Patterns</h2>
    <div id="correlationDayPatterns"></div>
  </div>

  <!-- 3. METRIC CORRELATIONS -->
  <div style="margin-bottom: 16px;">
    <h2 style="margin: 0 0 12px 0; font-size: 16px; color: var(--fg); font-weight: 600;">Metric Correlations</h2>

    <!-- Sleep Insights -->
    <div class="card" style="margin-bottom: 12px;">
      <h3 style="margin: 0 0 10px 0; font-size: 14px; color: var(--muted); font-weight: 600;">Sleep Quality Insights</h3>
      <div id="correlationSleepInsights"></div>
    </div>

    <!-- Activity Insights -->
    <div class="card" style="margin-bottom: 12px;">
      <h3 style="margin: 0 0 10px 0; font-size: 14px; color: var(--muted); font-weight: 600;">Activity Insights</h3>
      <div id="correlationActivityInsights"></div>
    </div>

    <!-- Heart Rate Insights (NEW) -->
    <div class="card">
      <h3 style="margin: 0 0 10px 0; font-size: 14px; color: var(--muted); font-weight: 600;">Heart Rate Insights</h3>
      <div id="correlationHRInsights"></div>
    </div>
  </div>

  <!-- 4. CONTEXT MATTERS - Segmented Insights (NEW) -->
  <div style="margin-bottom: 16px;">
    <h2 style="margin: 0 0 12px 0; font-size: 16px; color: var(--fg); font-weight: 600;">Context Matters</h2>
    <div id="correlationSegmentedInsights"></div>
  </div>

</div>
```

**Step 2: Test in browser**

1. Navigate to Insights tab
2. Verify all sections appear in order:
   - Top Discoveries
   - Day Patterns
   - Metric Correlations (Sleep, Activity, HR)
   - Context Matters
3. Check visual hierarchy and spacing

**Expected:** New section structure renders correctly with proper styling

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: reorganize insights UI with day patterns and HR sections"
```

---

## Task 13: Add Weekend/Weekday Flag to Sleep Records

**Goal:** Ensure sleep records have isWeekend flag for easier filtering

**Files:**
- Modify: `index.html:887-895` (sleep record creation)

**Step 1: Add isWeekend flag**

In the sleep record creation block, add isWeekend calculation:

```javascript
const durationMinutes = value;
const durationHours = Math.round((durationMinutes / 60) * 100) / 100;
const dayOfWeek = toDt.getDay();
const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sunday or Saturday
const weekdayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// ... HR extraction code from Task 1 ...

sleepRecordsBuffer.push({
  date: iso,
  from: fromDt.toISOString(),
  to: toDt.toISOString(),
  durationMinutes,
  durationHours,
  dayOfWeek,
  isWeekend, // NEW FLAG
  weekdayName: weekdayNames[dayOfWeek],
  avgHeartRate: validAvgHR,
  minHeartRate: validMinHR,
  maxHeartRate: validMaxHR
});
```

**Step 2: Verify in IndexedDB**

1. Clear database and reload data
2. Check sleepRecords table for isWeekend field
3. Verify values are correct (Saturday/Sunday = true, others = false)

**Expected:** isWeekend flag correctly set for all sleep records

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add isWeekend flag to sleep records"
```

---

## Task 14: Add Metric Label Helper Function

**Goal:** Create helper to get human-readable labels for metric names

**Files:**
- Modify: `index.html` (add helper function before correlation functions)

**Step 1: Add getMetricLabel function**

Before the correlation engine section (around line 2080), add:

```javascript
/**
 * Get human-readable label for metric name
 * @param {string} metricName
 * @returns {string}
 */
function getMetricLabel(metricName) {
  const labels = {
    'sleep_duration_min': 'Sleep Duration',
    'sleep_bedtime_min': 'Bedtime',
    'sleep_wake_min': 'Wake Time',
    'sleep_avg_hr': 'Sleep Heart Rate',
    'sleep_min_hr': 'Min Sleep HR',
    'sleep_max_hr': 'Max Sleep HR',
    'aggregates_steps': 'Steps',
    'workout_count': 'Workout Count',
    'workout_total_duration': 'Workout Duration',
    'workout_avg_hr': 'Workout Heart Rate',
    'workout_max_hr': 'Max Workout HR'
  };

  return labels[metricName] || metricName;
}

/**
 * Format metric value for display
 * @param {string} metricName
 * @param {number} value
 * @returns {string}
 */
function formatMetricValue(metricName, value) {
  if (value === null || isNaN(value)) return 'N/A';

  if (metricName === 'sleep_duration_min') {
    return `${Math.round(value / 60 * 10) / 10}h`;
  } else if (metricName.includes('_hr')) {
    return `${Math.round(value)} bpm`;
  } else if (metricName === 'aggregates_steps') {
    return Math.round(value).toLocaleString();
  } else if (metricName === 'workout_total_duration') {
    return `${Math.round(value)} min`;
  } else if (metricName.includes('bedtime') || metricName.includes('wake')) {
    const hours = Math.floor(value / 60);
    const mins = Math.round(value % 60);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
  }

  return Math.round(value * 10) / 10;
}
```

**Step 2: Update existing renderPatternCard**

Find where scatter plots use metric labels (around line 2774-2777) and verify it's using these helper functions correctly (it already does in current code, but confirm consistency).

**Step 3: Test helpers**

Browser console:
```javascript
console.log(getMetricLabel('sleep_avg_hr')); // "Sleep Heart Rate"
console.log(formatMetricValue('sleep_duration_min', 450)); // "7.5h"
console.log(formatMetricValue('sleep_avg_hr', 65)); // "65 bpm"
```

**Expected:** Helper functions return correct labels and formats

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add metric label and formatting helper functions"
```

---

## Task 15: Final Integration Test & Documentation

**Goal:** Test complete workflow and update README if needed

**Files:**
- Test: Full workflow in browser
- Modify (optional): `README.md` if insights section changed significantly

**Step 1: Complete integration test**

1. Clear browser IndexedDB completely
2. Reload page and load ZIP from `data/raw/`
3. Wait for ingestion to complete
4. Navigate to Insights tab
5. Verify all sections render:
   - Top Discoveries shows mixed finding types
   - Day Patterns shows weekend/weekday and day-of-week
   - Metric Correlations split into Sleep/Activity/HR
   - Context Matters shows segmented insights
6. Click "Show scatter plot" on a correlation
7. Verify scatter plot renders correctly
8. Check browser console for any errors

**Expected:** Complete workflow works end-to-end with no errors

**Step 2: Check README accuracy**

Read `README.md` sections:
- "What You Get" section mentions Insights
- Check if description matches new capabilities

If changes needed:
```markdown
**💡 Pattern Discovery**
- Automatically finds correlations between sleep, activity, and heart rate metrics
- Detects weekend vs weekday patterns and day-of-week trends
- Shows how relationships vary by context (e.g., "Steps → Sleep stronger on weekdays")
- Statistical analysis with easy-to-understand visualizations
- Shows what was analyzed even when no patterns are found
```

**Step 3: Performance check**

1. Open DevTools Performance tab
2. Record Insights tab load
3. Verify total computation < 3 seconds
4. Check memory usage is reasonable

**Expected:** Performance remains acceptable with expanded analysis

**Step 4: Final commit**

```bash
git add README.md  # if modified
git commit -m "docs: update README with expanded insight capabilities"
```

---

## Implementation Complete

**Verification Checklist:**

- [ ] HR data extracted from sleep.csv
- [ ] Workout HR aggregates calculated
- [ ] 25 new correlation pairs defined
- [ ] Statistical functions (t-test, Cohen's d) implemented
- [ ] Day pattern analysis working (weekend/weekday, day-of-week)
- [ ] Segmented correlations calculated
- [ ] All insights organized correctly
- [ ] Top discoveries render with mixed types
- [ ] Day patterns section renders
- [ ] HR insights section added to correlations
- [ ] Segmented insights section renders
- [ ] Full dashboard orchestration works
- [ ] No JavaScript errors in console
- [ ] Performance acceptable (<3s for analysis)
- [ ] UI matches design (4 sections in correct order)

**Next Steps:**

After completing this plan, the tool will surface significantly more insights from 2000 days of health data including:
- Heart rate recovery patterns
- Office day vs home day patterns (via weekday analysis)
- Context-dependent correlations
- Multi-metric relationships

If still no patterns emerge, consider:
- Data quality investigation (are HR values consistently recorded?)
- Looser significance thresholds (exploratory analysis)
- Visualizations without statistics (time series overlays, distributions)
