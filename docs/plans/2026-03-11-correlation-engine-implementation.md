# Correlation Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a correlation discovery tab that automatically finds and visualizes relationships between health metrics (sleep, activity, weight) with beginner-friendly explanations.

**Architecture:** Discovery-first dashboard with sleep-heavy weighting (70/30 split), showing top correlations prominently then organized by target metric. Uses Pearson correlation with percentile-based bucketing and confidence indicators. Includes prominent "correlation ≠ causation" disclaimer and educational fallback for insufficient data.

**Tech Stack:** Vanilla JavaScript, ECharts for visualizations, IndexedDB via Dexie, single-file HTML architecture

---

## Task 1: Add Correlation Tab to HTML Structure

**Files:**
- Modify: `index.html` (around line 167, tabs section)
- Modify: `index.html` (around line 180, add new content container)

**Step 1: Add tab button to navigation**

Locate the tabs section (around line 166):
```html
<div class="tabs">
  <div class="tab active" id="tabActivity">📊 Activity</div>
  <div class="tab" id="tabSleep">😴 Sleep</div>
</div>
```

Add correlation tab after sleep:
```html
<div class="tabs">
  <div class="tab active" id="tabActivity">📊 Activity</div>
  <div class="tab" id="tabSleep">😴 Sleep</div>
  <div class="tab" id="tabCorrelation">💡 Insights</div>
</div>
```

**Step 2: Add correlation content container**

After the sleep charts container (around line 240), add:
```html
      <div id="correlationCharts" style="display:none; margin-top:10px;">
        <!-- Disclaimer Banner -->
        <div class="card" id="correlationDisclaimer" style="background: rgba(255,191,58,0.08); border: 1px solid rgba(255,191,58,0.25); margin-bottom: 16px;">
          <div style="display: flex; align-items: start; gap: 12px;">
            <div style="font-size: 24px;">⚠️</div>
            <div style="flex: 1;">
              <h2 style="margin: 0 0 8px 0; color: #ffd68a; font-size: 15px; text-transform: none; letter-spacing: 0;">Remember: Correlation ≠ Causation</h2>
              <div class="muted" style="line-height: 1.5;">
                These patterns show relationships in YOUR data, not proof of cause-and-effect. Just because two things happen together doesn't mean one causes the other.
                <a href="https://en.wikipedia.org/wiki/Correlation_does_not_imply_causation" target="_blank" rel="noopener" style="color: #3aa0ff; text-decoration: none; border-bottom: 1px dotted #3aa0ff;">Learn more</a>
              </div>
              <div style="margin-top: 8px; font-style: italic; color: #b8a57d; font-size: 11px;">
                "Correlation does not imply causation"
              </div>
            </div>
          </div>
        </div>

        <!-- Top Discoveries -->
        <div class="card" style="margin-bottom: 16px;">
          <h2 style="margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; color: #3aa0ff; font-size: 13px;">✨ Top Discoveries</h2>
          <div id="correlationTopDiscoveries"></div>
        </div>

        <!-- Sleep Insights -->
        <div class="card" style="margin-bottom: 16px;">
          <h2 style="margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; color: #3aa0ff; font-size: 13px;">😴 What Affects Your Sleep</h2>
          <div id="correlationSleepInsights"></div>
          <div id="correlationSleepShowMore" style="margin-top: 12px; text-align: center; display: none;">
            <button id="btnShowMoreSleep" style="font-size: 12px;">Show more patterns ▼</button>
          </div>
        </div>

        <!-- Activity Insights -->
        <div class="card" style="margin-bottom: 16px;">
          <h2 style="margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; color: #3aa0ff; font-size: 13px;">📊 What Drives Your Activity</h2>
          <div id="correlationActivityInsights"></div>
          <div id="correlationActivityShowMore" style="margin-top: 12px; text-align: center; display: none;">
            <button id="btnShowMoreActivity" style="font-size: 12px;">Show more patterns ▼</button>
          </div>
        </div>
      </div>
```

**Step 3: Update tab switching logic**

Find the tab switching code (search for `tabActivity.addEventListener` around line 4020). Update to include correlation tab:

```javascript
  // Tab switching
  function switchToTab(tabName) {
    const isActivity = tabName === "activity";
    const isSleep = tabName === "sleep";
    const isCorrelation = tabName === "correlation";

    // Update tab button states
    if ($("tabActivity")) $("tabActivity").classList.toggle("active", isActivity);
    if ($("tabSleep")) $("tabSleep").classList.toggle("active", isSleep);
    if ($("tabCorrelation")) $("tabCorrelation").classList.toggle("active", isCorrelation);

    // Update content visibility
    if ($("activityCharts")) $("activityCharts").style.display = isActivity ? "block" : "none";
    if ($("controlsActivity")) $("controlsActivity").style.display = isActivity ? "block" : "none";
    if ($("sleepCharts")) $("sleepCharts").style.display = isSleep ? "block" : "none";
    if ($("controlsSleep")) $("controlsSleep").style.display = isSleep ? "block" : "none";
    if ($("correlationCharts")) $("correlationCharts").style.display = isCorrelation ? "block" : "none";

    // Render tab content if needed
    if (isActivity) {
      renderActivityDashboard().catch(console.error);
    } else if (isSleep) {
      renderSleepDashboard().catch(console.error);
    } else if (isCorrelation) {
      renderCorrelationDashboard().catch(console.error);
    }
  }

  if ($("tabActivity")) $("tabActivity").addEventListener("click", () => switchToTab("activity"));
  if ($("tabSleep")) $("tabSleep").addEventListener("click", () => switchToTab("sleep"));
  if ($("tabCorrelation")) $("tabCorrelation").addEventListener("click", () => switchToTab("correlation"));
```

**Step 4: Test tab switching in browser**

Manual test:
1. Open index.html in browser
2. Click between Activity, Sleep, and Insights tabs
3. Verify only one content section visible at a time
4. Verify tab buttons highlight correctly

Expected: Tabs switch correctly, Insights tab shows empty containers

**Step 5: Commit**

```bash
git add index.html
git commit -m "Add Correlation/Insights tab structure and navigation"
```

---

## Task 2: Implement Pearson Correlation Calculation

**Files:**
- Modify: `index.html` (add before renderCorrelationDashboard function, around line 2050)

**Step 1: Add Pearson correlation function**

Add after the sleep-related functions (around line 2050):

```javascript
  // ========================================
  // CORRELATION ENGINE - STATISTICAL FUNCTIONS
  // ========================================

  /**
   * Calculate Pearson correlation coefficient between two arrays
   * @param {Array<number>} x - Independent variable values
   * @param {Array<number>} y - Dependent variable values
   * @returns {number|null} Correlation coefficient (-1 to 1), or null if insufficient data
   */
  function calculatePearsonCorrelation(x, y) {
    if (!x || !y || x.length !== y.length || x.length < 14) {
      return null; // Need at least 14 data points
    }

    const n = x.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

    for (let i = 0; i < n; i++) {
      sumX += x[i];
      sumY += y[i];
      sumXY += x[i] * y[i];
      sumX2 += x[i] * x[i];
      sumY2 += y[i] * y[i];
    }

    const numerator = (n * sumXY) - (sumX * sumY);
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

    if (denominator === 0) {
      return null; // Avoid division by zero
    }

    return numerator / denominator;
  }

  /**
   * Classify correlation strength
   * @param {number} r - Pearson correlation coefficient
   * @returns {string} "strong" | "moderate" | "weak" | "none"
   */
  function classifyCorrelationStrength(r) {
    const absR = Math.abs(r);
    if (absR >= 0.5) return "strong";
    if (absR >= 0.3) return "moderate";
    if (absR >= 0.15) return "weak";
    return "none";
  }

  /**
   * Classify confidence level based on sample size
   * @param {number} sampleSize - Number of data points
   * @returns {string} "strong" | "moderate" | "early"
   */
  function classifyConfidenceLevel(sampleSize) {
    if (sampleSize >= 60) return "strong";
    if (sampleSize >= 30) return "moderate";
    return "early";
  }
```

**Step 2: Test correlation calculation manually**

Add temporary test code after the functions:

```javascript
  // TEMP: Manual test
  console.log("Testing Pearson correlation:");
  const testX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
  const testY = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]; // Perfect positive correlation
  const r = calculatePearsonCorrelation(testX, testY);
  console.log(`Perfect positive: r = ${r} (should be ~1.0)`);
  console.log(`Strength: ${classifyCorrelationStrength(r)} (should be "strong")`);
  console.log(`Confidence: ${classifyConfidenceLevel(15)} (should be "early")`);
```

**Step 3: Run in browser and verify**

Manual test:
1. Reload page
2. Open console
3. Verify output shows: r ≈ 1.0, strength = "strong", confidence = "early"
4. Remove temporary test code

Expected: Console shows correct correlation calculation

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add Pearson correlation calculation functions"
```

---

## Task 3: Implement Data Alignment and Metric Pair Building

**Files:**
- Modify: `index.html` (add after correlation calculation functions)

**Step 1: Add data alignment function**

```javascript
  /**
   * Align two time series by date, handling missing values
   * @param {Array} series1 - {dates: [...], values: [...]}
   * @param {Array} series2 - {dates: [...], values: [...]}
   * @param {string} lag - "same_day" | "previous_day"
   * @returns {Object} {x: [...], y: [...], dates: [...]}
   */
  function alignTimeSeries(series1, series2, lag = "same_day") {
    const x = [], y = [], dates = [];

    // Build maps for fast lookup
    const map1 = new Map(series1.dates.map((d, i) => [d, series1.values[i]]));
    const map2 = new Map(series2.dates.map((d, i) => [d, series2.values[i]]));

    if (lag === "same_day") {
      // Match on same date
      for (const date of series1.dates) {
        if (map2.has(date)) {
          const v1 = map1.get(date);
          const v2 = map2.get(date);
          if (v1 != null && v2 != null && !isNaN(v1) && !isNaN(v2)) {
            x.push(v1);
            y.push(v2);
            dates.push(date);
          }
        }
      }
    } else if (lag === "previous_day") {
      // Match series1[date-1] with series2[date]
      const allDates = [...new Set([...series1.dates, ...series2.dates])].sort();

      for (let i = 1; i < allDates.length; i++) {
        const prevDate = allDates[i - 1];
        const currDate = allDates[i];

        if (map1.has(prevDate) && map2.has(currDate)) {
          const v1 = map1.get(prevDate);
          const v2 = map2.get(currDate);
          if (v1 != null && v2 != null && !isNaN(v1) && !isNaN(v2)) {
            x.push(v1);
            y.push(v2);
            dates.push(currDate);
          }
        }
      }
    }

    return { x, y, dates };
  }
```

**Step 2: Add metric pair definition function**

```javascript
  /**
   * Define all metric pairs to calculate correlations for
   * @returns {Array} Array of {independent, dependent, lag, target} objects
   */
  function defineMetricPairs() {
    return [
      // Sleep as target (70% weight)
      { independent: "aggregates_steps", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Steps → Sleep Duration" },
      { independent: "workout_count", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Workout Count → Sleep Duration" },
      { independent: "workout_total_duration", dependent: "sleep_duration_min", lag: "same_day", target: "sleep", label: "Workout Duration → Sleep Duration" },
      { independent: "sleep_duration_min", dependent: "sleep_duration_min", lag: "previous_day", target: "sleep", label: "Sleep → Next Night's Sleep" },
      { independent: "aggregates_steps", dependent: "sleep_bedtime_min", lag: "same_day", target: "sleep", label: "Steps → Bedtime" },
      { independent: "workout_count", dependent: "sleep_bedtime_min", lag: "same_day", target: "sleep", label: "Workout Count → Bedtime" },

      // Activity as target (30% weight)
      { independent: "sleep_duration_min", dependent: "aggregates_steps", lag: "previous_day", target: "activity", label: "Sleep → Steps" },
      { independent: "sleep_duration_min", dependent: "workout_count", lag: "previous_day", target: "activity", label: "Sleep → Workout Count" },
      { independent: "sleep_duration_min", dependent: "workout_total_duration", lag: "previous_day", target: "activity", label: "Sleep → Workout Duration" },
    ];
  }
```

**Step 3: Add helper to fetch workout aggregates**

```javascript
  /**
   * Calculate daily workout aggregates from activity records
   * @returns {Promise<Object>} {workout_count: {dates, values}, workout_total_duration: {dates, values}}
   */
  async function fetchWorkoutAggregates() {
    const records = await db.activityRecords.toArray();

    // Group by date
    const dailyMap = new Map();

    for (const record of records) {
      const date = record.date;
      if (!dailyMap.has(date)) {
        dailyMap.set(date, { count: 0, totalDuration: 0 });
      }
      const day = dailyMap.get(date);
      day.count++;
      day.totalDuration += record.durationMinutes || 0;
    }

    // Convert to series format
    const dates = Array.from(dailyMap.keys()).sort();
    const countValues = dates.map(d => dailyMap.get(d).count);
    const durationValues = dates.map(d => dailyMap.get(d).totalDuration);

    return {
      workout_count: { dates, values: countValues },
      workout_total_duration: { dates, values: durationValues }
    };
  }
```

**Step 4: Test alignment in browser console**

Add temporary test code:

```javascript
  // TEMP: Test alignment
  (async function testAlignment() {
    const steps = await fetchDailySeries("aggregates_steps");
    const sleep = await fetchDailySeries("sleep_duration_min");
    const aligned = alignTimeSeries(steps, sleep, "same_day");
    console.log(`Aligned ${aligned.x.length} data points between steps and sleep`);
    console.log("Sample:", aligned.x.slice(0, 5), aligned.y.slice(0, 5));
  })();
```

**Step 5: Verify in browser**

Manual test:
1. Reload page with data loaded
2. Check console for alignment output
3. Verify data points > 0
4. Remove temporary test code

Expected: Console shows aligned data points with sample values

**Step 6: Commit**

```bash
git add index.html
git commit -m "Add time series alignment and metric pair definitions"
```

---

## Task 4: Implement Percentile Bucketing

**Files:**
- Modify: `index.html` (add after alignment functions)

**Step 1: Add percentile bucketing function**

```javascript
  /**
   * Bucket continuous values into low/medium/high based on percentiles
   * @param {Array<number>} values - Values to bucket
   * @returns {Object} {low: {threshold, indices}, medium: {threshold, indices}, high: {threshold, indices}}
   */
  function bucketByPercentile(values) {
    if (!values || values.length < 3) return null;

    // Sort to find percentile thresholds
    const sorted = [...values].sort((a, b) => a - b);
    const p33 = sorted[Math.floor(sorted.length * 0.33)];
    const p67 = sorted[Math.floor(sorted.length * 0.67)];

    // Find indices for each bucket
    const lowIndices = [];
    const mediumIndices = [];
    const highIndices = [];

    values.forEach((v, i) => {
      if (v < p33) lowIndices.push(i);
      else if (v < p67) mediumIndices.push(i);
      else highIndices.push(i);
    });

    return {
      low: { threshold: [sorted[0], p33], indices: lowIndices },
      medium: { threshold: [p33, p67], indices: mediumIndices },
      high: { threshold: [p67, sorted[sorted.length - 1]], indices: highIndices }
    };
  }

  /**
   * Calculate average value for indices
   * @param {Array<number>} values - All values
   * @param {Array<number>} indices - Indices to average
   * @returns {number} Average value
   */
  function calculateBucketAverage(values, indices) {
    if (!indices || indices.length === 0) return null;
    const sum = indices.reduce((acc, i) => acc + values[i], 0);
    return sum / indices.length;
  }
```

**Step 2: Test bucketing**

Add temporary test:

```javascript
  // TEMP: Test bucketing
  const testValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150];
  const buckets = bucketByPercentile(testValues);
  console.log("Buckets:", buckets);
  console.log("Low avg:", calculateBucketAverage(testValues, buckets.low.indices));
  console.log("Medium avg:", calculateBucketAverage(testValues, buckets.medium.indices));
  console.log("High avg:", calculateBucketAverage(testValues, buckets.high.indices));
```

**Step 3: Verify bucketing works**

Manual test:
1. Reload page
2. Check console
3. Verify buckets contain ~33% of values each
4. Verify averages make sense
5. Remove test code

Expected: Three buckets with appropriate threshold and average values

**Step 4: Commit**

```bash
git add index.html
git commit -m "Add percentile-based bucketing for correlation comparisons"
```

---

## Task 5: Implement Main Correlation Calculation Pipeline

**Files:**
- Modify: `index.html` (add after bucketing functions)

**Step 1: Add main correlation calculation function**

```javascript
  /**
   * Calculate all correlations for defined metric pairs
   * @returns {Promise<Array>} Array of correlation objects
   */
  async function calculateAllCorrelations() {
    console.log("Calculating correlations...");

    // Fetch all needed metrics
    const steps = await fetchDailySeries("aggregates_steps");
    const sleepDuration = await fetchDailySeries("sleep_duration_min");
    const bedtime = await fetchDailySeries("sleep_bedtime_min");
    const workoutAggregates = await fetchWorkoutAggregates();

    const metricsData = {
      "aggregates_steps": steps,
      "sleep_duration_min": sleepDuration,
      "sleep_bedtime_min": bedtime,
      "workout_count": workoutAggregates.workout_count,
      "workout_total_duration": workoutAggregates.workout_total_duration
    };

    const pairs = defineMetricPairs();
    const correlations = [];

    for (const pair of pairs) {
      const indData = metricsData[pair.independent];
      const depData = metricsData[pair.dependent];

      if (!indData || !depData || indData.values.length === 0 || depData.values.length === 0) {
        console.log(`Skipping ${pair.label}: missing data`);
        continue;
      }

      // Align time series
      const aligned = alignTimeSeries(indData, depData, pair.lag);

      if (aligned.x.length < 14) {
        console.log(`Skipping ${pair.label}: only ${aligned.x.length} overlapping days`);
        continue;
      }

      // Calculate correlation
      const r = calculatePearsonCorrelation(aligned.x, aligned.y);

      if (r === null) {
        console.log(`Skipping ${pair.label}: correlation calculation failed`);
        continue;
      }

      const strength = classifyCorrelationStrength(r);

      if (strength === "none") {
        console.log(`Skipping ${pair.label}: correlation too weak (r=${r.toFixed(3)})`);
        continue;
      }

      // Calculate bucket statistics
      const buckets = bucketByPercentile(aligned.x);
      const bucketStats = {
        low: {
          threshold: buckets.low.threshold,
          avg: calculateBucketAverage(aligned.y, buckets.low.indices),
          count: buckets.low.indices.length
        },
        medium: {
          threshold: buckets.medium.threshold,
          avg: calculateBucketAverage(aligned.y, buckets.medium.indices),
          count: buckets.medium.indices.length
        },
        high: {
          threshold: buckets.high.threshold,
          avg: calculateBucketAverage(aligned.y, buckets.high.indices),
          count: buckets.high.indices.length
        }
      };

      // Build scatter data
      const scatterData = aligned.x.map((xVal, i) => {
        let bucket = "low";
        if (buckets.medium.indices.includes(i)) bucket = "medium";
        if (buckets.high.indices.includes(i)) bucket = "high";

        return { x: xVal, y: aligned.y[i], date: aligned.dates[i], bucket };
      });

      const correlation = {
        id: `${pair.independent}_to_${pair.dependent}_${pair.lag}`,
        label: pair.label,
        independent: pair.independent,
        dependent: pair.dependent,
        lag: pair.lag,
        target: pair.target,
        r: r,
        strength: strength,
        direction: r >= 0 ? "positive" : "negative",
        sampleSize: aligned.x.length,
        confidence: classifyConfidenceLevel(aligned.x.length),
        buckets: bucketStats,
        scatterData: scatterData
      };

      correlations.push(correlation);
      console.log(`✓ ${pair.label}: r=${r.toFixed(3)}, ${strength} ${correlation.direction}, n=${aligned.x.length}`);
    }

    // Sort by absolute correlation strength
    correlations.sort((a, b) => Math.abs(b.r) - Math.abs(a.r));

    console.log(`Calculated ${correlations.length} correlations`);
    return correlations;
  }
```

**Step 2: Test calculation pipeline**

Add temporary test:

```javascript
  // TEMP: Test correlation calculation
  window.testCorrelations = async function() {
    const correlations = await calculateAllCorrelations();
    console.log("All correlations:", correlations);
    return correlations;
  };
  console.log("Run testCorrelations() to test");
```

**Step 3: Verify in browser**

Manual test:
1. Reload page with data loaded
2. Run `testCorrelations()` in console
3. Verify correlations array populated
4. Check console logs for calculation details
5. Remove test code

Expected: Array of correlation objects with r-values, strengths, and bucket stats

**Step 4: Commit**

```bash
git add index.html
git commit -m "Implement main correlation calculation pipeline"
```

---

## Task 6: Implement Pattern Card Rendering

**Files:**
- Modify: `index.html` (add after correlation calculation functions)

**Step 1: Add confidence badge formatter**

```javascript
  /**
   * Format confidence badge HTML
   * @param {string} confidence - "strong" | "moderate" | "early"
   * @param {number} sampleSize - Number of data points
   * @returns {string} HTML string
   */
  function formatConfidenceBadge(confidence, sampleSize) {
    const badges = {
      strong: { icon: "🟢", label: "Strong confidence", color: "#3dce79" },
      moderate: { icon: "🟡", label: "Moderate confidence", color: "#ffbf3a" },
      early: { icon: "🟠", label: "Early pattern", color: "#ff8c42" }
    };

    const badge = badges[confidence];
    return `<span style="background: rgba(${confidence === 'strong' ? '61, 206, 121' : confidence === 'moderate' ? '255, 191, 58' : '255, 140, 66'}, 0.15);
                         border: 1px solid ${badge.color};
                         color: ${badge.color};
                         padding: 4px 10px;
                         border-radius: 12px;
                         font-size: 11px;
                         font-weight: 600;
                         letter-spacing: 0.3px;"
                  title="${badge.label}: ${sampleSize} days of data">
              ${badge.icon} ${badge.label}: ${sampleSize} days
            </span>`;
  }

  /**
   * Format relationship indicator HTML
   * @param {string} strength - "strong" | "moderate" | "weak"
   * @param {string} direction - "positive" | "negative"
   * @returns {string} HTML string
   */
  function formatRelationshipIndicator(strength, direction) {
    const indicators = {
      "strong-positive": { icon: "🟢", label: "Strong positive relationship", color: "#3dce79" },
      "moderate-positive": { icon: "🟡", label: "Moderate positive relationship", color: "#ffbf3a" },
      "weak-positive": { icon: "🟠", label: "Weak positive relationship", color: "#ff8c42" },
      "strong-negative": { icon: "🔴", label: "Strong negative relationship", color: "#ff5a6b" },
      "moderate-negative": { icon: "🟠", label: "Moderate negative relationship", color: "#ff8c42" },
      "weak-negative": { icon: "⚪", label: "Weak negative relationship", color: "#9fb0c3" }
    };

    const key = `${strength}-${direction}`;
    const indicator = indicators[key];

    return `<div style="display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: ${indicator.color};">
              <span style="font-size: 18px;">${indicator.icon}</span>
              <span style="font-weight: 600;">${indicator.label}</span>
            </div>`;
  }
```

**Step 2: Add metric label formatter**

```javascript
  /**
   * Get human-readable label for metric
   * @param {string} metric - Metric key
   * @returns {string} Label
   */
  function getMetricLabel(metric) {
    const labels = {
      "aggregates_steps": "steps",
      "sleep_duration_min": "sleep duration",
      "sleep_bedtime_min": "bedtime",
      "workout_count": "workouts",
      "workout_total_duration": "workout time"
    };
    return labels[metric] || metric;
  }

  /**
   * Format value with appropriate units
   * @param {string} metric - Metric key
   * @param {number} value - Value to format
   * @returns {string} Formatted value with units
   */
  function formatMetricValue(metric, value) {
    if (metric === "sleep_duration_min") {
      const hours = Math.floor(value / 60);
      const mins = Math.round(value % 60);
      return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    }
    if (metric === "sleep_bedtime_min") {
      const hours = Math.floor(value / 60);
      const mins = Math.round(value % 60);
      return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
    }
    if (metric === "workout_total_duration") {
      return `${Math.round(value)} min`;
    }
    if (metric === "workout_count") {
      return `${value.toFixed(1)} workouts`;
    }
    return Math.round(value).toLocaleString();
  }
```

**Step 3: Add pattern card rendering function**

```javascript
  /**
   * Render a single correlation pattern card
   * @param {Object} correlation - Correlation object
   * @param {boolean} isTopDiscovery - Whether this is in top discoveries section
   * @returns {string} HTML string
   */
  function renderPatternCard(correlation, isTopDiscovery = false) {
    const { label, r, strength, direction, confidence, sampleSize, buckets, independent, dependent } = correlation;

    // Generate plain English summary
    const indLabel = getMetricLabel(independent);
    const depLabel = getMetricLabel(dependent);
    const highAvg = formatMetricValue(dependent, buckets.high.avg);
    const lowAvg = formatMetricValue(dependent, buckets.low.avg);
    const diff = Math.abs(buckets.high.avg - buckets.low.avg);
    const diffFormatted = formatMetricValue(dependent, diff);
    const highThreshold = formatMetricValue(independent, buckets.high.threshold[0]);

    const relationshipText = direction === "positive"
      ? `On your high ${indLabel} days (>${highThreshold}), you average ${highAvg} ${depLabel} — that's ${diffFormatted} more than low ${indLabel} days (${lowAvg})`
      : `On your high ${indLabel} days (>${highThreshold}), you average ${highAvg} ${depLabel} — that's ${diffFormatted} less than low ${indLabel} days (${lowAvg})`;

    // Calculate bar widths (relative to max)
    const maxAvg = Math.max(buckets.low.avg, buckets.medium.avg, buckets.high.avg);
    const lowWidth = (buckets.low.avg / maxAvg) * 100;
    const medWidth = (buckets.medium.avg / maxAvg) * 100;
    const highWidth = (buckets.high.avg / maxAvg) * 100;

    const cardStyle = isTopDiscovery
      ? `border: 2px solid rgba(58, 160, 255, 0.3); background: rgba(58, 160, 255, 0.05);`
      : ``;

    return `
      <div class="correlation-pattern-card" style="background: #0f1521; border: 1px solid #223046; border-radius: 12px; padding: 16px; margin-bottom: 12px; ${cardStyle}">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; gap: 12px;">
          <div style="flex: 1;">
            <div style="font-size: 15px; font-weight: 700; color: var(--fg); margin-bottom: 8px;">
              ${label}
            </div>
            ${formatConfidenceBadge(confidence, sampleSize)}
          </div>
        </div>

        <!-- Plain English Summary -->
        <div style="font-size: 14px; color: var(--fg); line-height: 1.5; margin-bottom: 12px; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px;">
          ${relationshipText}
        </div>

        <!-- Relationship Indicator -->
        <div style="margin-bottom: 16px;">
          ${formatRelationshipIndicator(strength, direction)}
        </div>

        <!-- Summary Bars -->
        <div style="margin-bottom: 12px;">
          <div style="font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
            Comparison by ${indLabel} level
          </div>

          <!-- Low bucket -->
          <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 3px;">
              <span title="Your lowest third of days for this metric">Low (${formatMetricValue(independent, buckets.low.threshold[0])}–${formatMetricValue(independent, buckets.low.threshold[1])})</span>
              <span style="font-weight: 600; color: var(--fg);">${formatMetricValue(dependent, buckets.low.avg)} avg</span>
            </div>
            <div style="background: #0b1018; border-radius: 4px; height: 20px; overflow: hidden;">
              <div style="background: linear-gradient(90deg, #3a5a7f, #2a4a6f); height: 100%; width: ${lowWidth}%;"></div>
            </div>
          </div>

          <!-- Medium bucket -->
          <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 3px;">
              <span title="Your typical/average days">Medium (${formatMetricValue(independent, buckets.medium.threshold[0])}–${formatMetricValue(independent, buckets.medium.threshold[1])})</span>
              <span style="font-weight: 600; color: var(--fg);">${formatMetricValue(dependent, buckets.medium.avg)} avg</span>
            </div>
            <div style="background: #0b1018; border-radius: 4px; height: 20px; overflow: hidden;">
              <div style="background: linear-gradient(90deg, #5a8abf, #4a7aaf); height: 100%; width: ${medWidth}%;"></div>
            </div>
          </div>

          <!-- High bucket -->
          <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 3px;">
              <span title="Your best third of days for this metric">High (${formatMetricValue(independent, buckets.high.threshold[0])}–${formatMetricValue(independent, buckets.high.threshold[1])})</span>
              <span style="font-weight: 600; color: var(--fg);">${formatMetricValue(dependent, buckets.high.avg)} avg</span>
            </div>
            <div style="background: #0b1018; border-radius: 4px; height: 20px; overflow: hidden;">
              <div style="background: linear-gradient(90deg, #3aa0ff, #3dce79); height: 100%; width: ${highWidth}%;"></div>
            </div>
          </div>
        </div>

        <!-- Scatter plot (collapsible) -->
        <div>
          <button class="btn-show-scatter" data-correlation-id="${correlation.id}" style="font-size: 12px; padding: 6px 12px; width: 100%;">
            Show scatter plot ▼
          </button>
          <div id="scatter-${correlation.id}" style="display: none; height: 300px; margin-top: 12px;"></div>
        </div>
      </div>
    `;
  }
```

**Step 4: Test pattern card rendering**

Add temporary test in renderCorrelationDashboard stub:

```javascript
  async function renderCorrelationDashboard() {
    const container = $("correlationTopDiscoveries");
    if (!container) return;

    // TEMP: Create fake correlation for testing
    const fakeCorrelation = {
      id: "test_correlation",
      label: "Steps → Sleep Duration",
      independent: "aggregates_steps",
      dependent: "sleep_duration_min",
      lag: "same_day",
      target: "sleep",
      r: 0.62,
      strength: "strong",
      direction: "positive",
      sampleSize: 65,
      confidence: "strong",
      buckets: {
        low: { threshold: [1000, 5000], avg: 360, count: 20 },
        medium: { threshold: [5000, 8500], avg: 410, count: 25 },
        high: { threshold: [8500, 15000], avg: 445, count: 20 }
      },
      scatterData: []
    };

    container.innerHTML = renderPatternCard(fakeCorrelation, true);
  }
```

**Step 5: Verify card renders correctly**

Manual test:
1. Reload page with data
2. Click Insights tab
3. Verify pattern card displays with:
   - Confidence badge
   - Plain English summary
   - Relationship indicator
   - Three comparison bars
   - Show scatter plot button
4. Remove temporary test code

Expected: Pattern card renders with all components styled correctly

**Step 6: Commit**

```bash
git add index.html
git commit -m "Add pattern card rendering with confidence badges and comparison bars"
```

---

## Task 7: Implement Scatter Plot Visualization

**Files:**
- Modify: `index.html` (add scatter plot rendering and expand/collapse logic)

**Step 1: Add scatter plot rendering function**

```javascript
  /**
   * Render scatter plot for a correlation
   * @param {Object} correlation - Correlation object
   * @param {string} containerId - DOM element ID for chart
   */
  function renderCorrelationScatter(correlation, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Container ${containerId} not found`);
      return;
    }

    // Dispose existing chart if any
    const existingChart = echarts.getInstanceByDom(container);
    if (existingChart) {
      existingChart.dispose();
    }

    // Initialize chart
    const chart = echarts.init(container, null, { renderer: 'canvas' });

    // Prepare data by bucket
    const lowData = correlation.scatterData.filter(d => d.bucket === 'low').map(d => [d.x, d.y]);
    const mediumData = correlation.scatterData.filter(d => d.bucket === 'medium').map(d => [d.x, d.y]);
    const highData = correlation.scatterData.filter(d => d.bucket === 'high').map(d => [d.x, d.y]);

    // Calculate trend line (linear regression)
    const allX = correlation.scatterData.map(d => d.x);
    const allY = correlation.scatterData.map(d => d.y);
    const n = allX.length;
    const sumX = allX.reduce((a, b) => a + b, 0);
    const sumY = allY.reduce((a, b) => a + b, 0);
    const sumXY = allX.reduce((sum, x, i) => sum + x * allY[i], 0);
    const sumX2 = allX.reduce((sum, x) => sum + x * x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const minX = Math.min(...allX);
    const maxX = Math.max(...allX);
    const trendLine = [
      [minX, slope * minX + intercept],
      [maxX, slope * maxX + intercept]
    ];

    // Chart configuration
    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#121824',
        borderColor: '#2a3a55',
        textStyle: { color: '#e7eef7' },
        formatter: (params) => {
          if (params.seriesName === 'Trend') return '';
          const point = correlation.scatterData.find(d => d.x === params.value[0] && d.y === params.value[1]);
          const xLabel = getMetricLabel(correlation.independent);
          const yLabel = getMetricLabel(correlation.dependent);
          const xVal = formatMetricValue(correlation.independent, params.value[0]);
          const yVal = formatMetricValue(correlation.dependent, params.value[1]);
          return `${point?.date || ''}<br/>${xLabel}: ${xVal}<br/>${yLabel}: ${yVal}<br/>Bucket: ${point?.bucket || ''}`;
        }
      },
      grid: {
        left: '12%',
        right: '4%',
        bottom: '12%',
        top: '8%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: getMetricLabel(correlation.independent),
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: '#9fb0c3', fontSize: 12 },
        axisLabel: { color: '#9fb0c3', fontSize: 11 },
        axisLine: { lineStyle: { color: '#2a3a55' } },
        splitLine: { lineStyle: { color: '#1f2a3a' } }
      },
      yAxis: {
        type: 'value',
        name: getMetricLabel(correlation.dependent),
        nameLocation: 'middle',
        nameGap: 50,
        nameTextStyle: { color: '#9fb0c3', fontSize: 12 },
        axisLabel: {
          color: '#9fb0c3',
          fontSize: 11,
          formatter: (val) => {
            if (correlation.dependent === 'sleep_duration_min') {
              return `${Math.round(val / 60)}h`;
            }
            return Math.round(val);
          }
        },
        axisLine: { lineStyle: { color: '#2a3a55' } },
        splitLine: { lineStyle: { color: '#1f2a3a' } }
      },
      series: [
        {
          name: 'Low',
          type: 'scatter',
          data: lowData,
          symbolSize: 8,
          itemStyle: { color: '#3a5a7f' }
        },
        {
          name: 'Medium',
          type: 'scatter',
          data: mediumData,
          symbolSize: 8,
          itemStyle: { color: '#5a8abf' }
        },
        {
          name: 'High',
          type: 'scatter',
          data: highData,
          symbolSize: 8,
          itemStyle: { color: '#3aa0ff' }
        },
        {
          name: 'Trend',
          type: 'line',
          data: trendLine,
          lineStyle: { color: '#ffbf3a', width: 2, type: 'dashed' },
          symbol: 'none',
          silent: true
        }
      ]
    });

    // Handle resize
    window.addEventListener('resize', () => {
      try { chart.resize(); } catch (e) {}
    });
  }
```

**Step 2: Add scatter plot expand/collapse event handlers**

Add after renderCorrelationDashboard function:

```javascript
  /**
   * Setup scatter plot toggle handlers
   */
  function setupScatterPlotToggles() {
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-show-scatter')) {
        const correlationId = e.target.getAttribute('data-correlation-id');
        const scatterContainer = document.getElementById(`scatter-${correlationId}`);

        if (!scatterContainer) return;

        const isVisible = scatterContainer.style.display !== 'none';

        if (isVisible) {
          // Collapse
          scatterContainer.style.display = 'none';
          e.target.textContent = 'Show scatter plot ▼';
        } else {
          // Expand and render
          scatterContainer.style.display = 'block';
          e.target.textContent = 'Hide scatter plot ▲';

          // Find correlation data
          if (window.cachedCorrelations) {
            const correlation = window.cachedCorrelations.find(c => c.id === correlationId);
            if (correlation) {
              renderCorrelationScatter(correlation, `scatter-${correlationId}`);
            }
          }
        }
      }
    });
  }

  // Call setup on page load
  setupScatterPlotToggles();
```

**Step 3: Test scatter plot rendering**

Modify temporary test in renderCorrelationDashboard to include scatter data:

```javascript
  // TEMP: Add scatter data to fake correlation
  fakeCorrelation.scatterData = [];
  for (let i = 0; i < 50; i++) {
    const x = 1000 + Math.random() * 14000;
    const y = 300 + Math.random() * 200 + (x / 15000) * 100; // Positive correlation
    const bucket = x < 5000 ? 'low' : x < 8500 ? 'medium' : 'high';
    fakeCorrelation.scatterData.push({ x, y, date: '2026-03-01', bucket });
  }

  window.cachedCorrelations = [fakeCorrelation];
  container.innerHTML = renderPatternCard(fakeCorrelation, true);
```

**Step 4: Verify scatter plot works**

Manual test:
1. Reload page
2. Click Insights tab
3. Click "Show scatter plot ▼" button
4. Verify:
   - Chart expands
   - Scatter points render color-coded
   - Trend line displays
   - Tooltip shows on hover
   - Button text changes to "Hide scatter plot ▲"
5. Click hide button, verify chart collapses
6. Remove temporary test code

Expected: Scatter plot expands/collapses smoothly with color-coded points

**Step 5: Commit**

```bash
git add index.html
git commit -m "Add scatter plot visualization with expand/collapse functionality"
```

---

## Task 8: Implement Top Discoveries and Section Rendering

**Files:**
- Modify: `index.html` (implement full renderCorrelationDashboard)

**Step 1: Implement top discoveries deduplication**

```javascript
  /**
   * Select top N correlations and deduplicate from category sections
   * @param {Array} correlations - All correlations
   * @param {number} topN - Number of top discoveries to show
   * @returns {Object} {topDiscoveries, sleepInsights, activityInsights}
   */
  function organizeCorrelations(correlations, topN = 3) {
    // Filter out weak correlations with early confidence
    const qualityCorrelations = correlations.filter(c => {
      if (c.confidence === 'early' && c.strength === 'weak') return false;
      return true;
    });

    // Get top N strongest correlations
    const topDiscoveries = qualityCorrelations.slice(0, topN);
    const topIds = new Set(topDiscoveries.map(c => c.id));

    // Separate remaining by target
    const remaining = qualityCorrelations.filter(c => !topIds.has(c.id));

    const sleepInsights = remaining.filter(c => c.target === 'sleep');
    const activityInsights = remaining.filter(c => c.target === 'activity');

    // Further separate by strength
    const organizeSectionByStrength = (insights) => {
      const strong = insights.filter(c => c.strength === 'strong' || c.strength === 'moderate');
      const moderate = insights.filter(c => c.strength === 'weak');
      return { strong, moderate };
    };

    return {
      topDiscoveries,
      sleepInsights: organizeSectionByStrength(sleepInsights),
      activityInsights: organizeSectionByStrength(activityInsights)
    };
  }
```

**Step 2: Implement educational fallback**

```javascript
  /**
   * Render educational fallback when no correlations found
   * @param {number} minDaysNeeded - Days needed to unlock correlations
   * @returns {string} HTML string
   */
  function renderEducationalFallback(minDaysNeeded = 14) {
    return `
      <div style="text-align: center; padding: 40px 20px; background: rgba(58, 160, 255, 0.05); border-radius: 12px; border: 1px solid rgba(58, 160, 255, 0.15);">
        <div style="font-size: 48px; margin-bottom: 16px;">📚</div>
        <div style="font-size: 18px; font-weight: 700; color: var(--fg); margin-bottom: 12px;">
          Building Your Personal Insights
        </div>
        <div class="muted" style="max-width: 500px; margin: 0 auto 20px; line-height: 1.6;">
          You need at least ${minDaysNeeded} days of overlapping data to discover patterns.
          Keep tracking sleep and activity to unlock your personalized discoveries!
        </div>

        <div style="background: rgba(255,255,255,0.02); border-radius: 12px; padding: 20px; max-width: 600px; margin: 0 auto; text-align: left;">
          <div style="font-size: 14px; font-weight: 600; color: var(--fg); margin-bottom: 12px;">
            While you're tracking, here's what research shows:
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7;">
            • Regular exercise generally improves sleep quality<br/>
            • Consistent sleep schedules help maintain energy levels<br/>
            • Physical activity during the day helps regulate circadian rhythm<br/>
            • Getting enough sleep supports better workout performance
          </div>
        </div>
      </div>
    `;
  }
```

**Step 3: Implement main dashboard rendering**

Replace stub renderCorrelationDashboard with full implementation:

```javascript
  /**
   * Main correlation dashboard rendering function
   */
  async function renderCorrelationDashboard() {
    console.log("Rendering correlation dashboard...");

    // Show loading state
    const topContainer = $("correlationTopDiscoveries");
    const sleepContainer = $("correlationSleepInsights");
    const activityContainer = $("correlationActivityInsights");

    if (topContainer) topContainer.innerHTML = '<div style="text-align:center; padding:40px; color:var(--muted);">Analyzing your patterns...</div>';
    if (sleepContainer) sleepContainer.innerHTML = '';
    if (activityContainer) activityContainer.innerHTML = '';

    try {
      // Calculate all correlations
      const correlations = await calculateAllCorrelations();

      // Cache for scatter plot access
      window.cachedCorrelations = correlations;

      // Check if we have any correlations
      if (correlations.length === 0) {
        if (topContainer) {
          topContainer.innerHTML = renderEducationalFallback(14);
        }
        if (sleepContainer) sleepContainer.innerHTML = '';
        if (activityContainer) activityContainer.innerHTML = '';
        return;
      }

      // Organize correlations
      const organized = organizeCorrelations(correlations, 3);

      // Render top discoveries
      if (organized.topDiscoveries.length > 0) {
        const topHtml = organized.topDiscoveries.map(c => renderPatternCard(c, true)).join('');
        if (topContainer) topContainer.innerHTML = topHtml;
      } else {
        if (topContainer) topContainer.innerHTML = renderEducationalFallback(14);
      }

      // Render sleep insights
      if (organized.sleepInsights.strong.length > 0) {
        const sleepHtml = organized.sleepInsights.strong.map(c => renderPatternCard(c, false)).join('');
        if (sleepContainer) sleepContainer.innerHTML = sleepHtml;

        // Show "show more" if moderate patterns exist
        if (organized.sleepInsights.moderate.length > 0) {
          const showMoreContainer = $("correlationSleepShowMore");
          if (showMoreContainer) {
            showMoreContainer.style.display = 'block';
            const btn = $("btnShowMoreSleep");
            if (btn) {
              btn.onclick = () => {
                const moderateHtml = organized.sleepInsights.moderate.map(c => renderPatternCard(c, false)).join('');
                if (sleepContainer) sleepContainer.innerHTML += moderateHtml;
                showMoreContainer.style.display = 'none';
              };
            }
          }
        }
      } else if (organized.sleepInsights.moderate.length > 0) {
        // Only weak patterns available - show educational fallback first
        if (sleepContainer) {
          sleepContainer.innerHTML = renderEducationalFallback(30) + '<div style="margin-top: 20px;"></div>';
          const weakHtml = organized.sleepInsights.moderate.map(c => renderPatternCard(c, false)).join('');
          sleepContainer.innerHTML += `<div style="opacity: 0.7;">${weakHtml}</div>`;
        }
      } else {
        if (sleepContainer) sleepContainer.innerHTML = '<div class="muted" style="text-align:center; padding:20px;">Keep tracking to unlock sleep insights</div>';
      }

      // Render activity insights
      if (organized.activityInsights.strong.length > 0) {
        const activityHtml = organized.activityInsights.strong.map(c => renderPatternCard(c, false)).join('');
        if (activityContainer) activityContainer.innerHTML = activityHtml;

        // Show "show more" if moderate patterns exist
        if (organized.activityInsights.moderate.length > 0) {
          const showMoreContainer = $("correlationActivityShowMore");
          if (showMoreContainer) {
            showMoreContainer.style.display = 'block';
            const btn = $("btnShowMoreActivity");
            if (btn) {
              btn.onclick = () => {
                const moderateHtml = organized.activityInsights.moderate.map(c => renderPatternCard(c, false)).join('');
                if (activityContainer) activityContainer.innerHTML += moderateHtml;
                showMoreContainer.style.display = 'none';
              };
            }
          }
        }
      } else if (organized.activityInsights.moderate.length > 0) {
        // Only weak patterns - show educational fallback first
        if (activityContainer) {
          activityContainer.innerHTML = renderEducationalFallback(30) + '<div style="margin-top: 20px;"></div>';
          const weakHtml = organized.activityInsights.moderate.map(c => renderPatternCard(c, false)).join('');
          activityContainer.innerHTML += `<div style="opacity: 0.7;">${weakHtml}</div>`;
        }
      } else {
        if (activityContainer) activityContainer.innerHTML = '<div class="muted" style="text-align:center; padding:20px;">Keep tracking to unlock activity insights</div>';
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

**Step 4: Test full dashboard rendering**

Manual test:
1. Reload page with full dataset
2. Click Insights tab
3. Verify:
   - Top 3 discoveries show at top with highlight styling
   - Sleep insights section shows remaining sleep correlations
   - Activity insights section shows activity correlations
   - No duplicates between sections
   - "Show more" buttons appear if moderate patterns exist
4. Test "show more" buttons expand correctly

Expected: Full dashboard renders with all sections populated and organized

**Step 5: Commit**

```bash
git add index.html
git commit -m "Implement full correlation dashboard with top discoveries and organized sections"
```

---

## Task 9: Add Weekly Pattern Enrichment (Optional Enhancement)

**Files:**
- Modify: `index.html` (add weekly pattern detection, optional)

**Note:** This task is optional and can be skipped for MVP. It adds context about when patterns are strongest (weekdays vs weekends).

**Step 1: Add weekday/weekend correlation split**

```javascript
  /**
   * Enrich correlation with weekly pattern notes
   * @param {Object} correlation - Correlation object
   * @returns {Object} Correlation with weeklyEnrichment property
   */
  function enrichWithWeeklyPatterns(correlation) {
    // Separate data by weekday/weekend
    const weekdayData = { x: [], y: [] };
    const weekendData = { x: [], y: [] };

    correlation.scatterData.forEach(point => {
      const date = new Date(point.date + 'T00:00:00');
      const dayOfWeek = date.getDay();

      if (dayOfWeek === 0 || dayOfWeek === 6) {
        // Weekend
        weekendData.x.push(point.x);
        weekendData.y.push(point.y);
      } else {
        // Weekday
        weekdayData.x.push(point.x);
        weekdayData.y.push(point.y);
      }
    });

    // Calculate separate correlations
    const weekdayR = calculatePearsonCorrelation(weekdayData.x, weekdayData.y);
    const weekendR = calculatePearsonCorrelation(weekendData.x, weekendData.y);

    if (weekdayR === null || weekendR === null) {
      return correlation; // Not enough data to split
    }

    // Check if difference is meaningful (≥0.2)
    const diff = Math.abs(weekdayR - weekendR);

    if (diff >= 0.2) {
      const stronger = Math.abs(weekdayR) > Math.abs(weekendR) ? 'weekdays' : 'weekends';
      correlation.weeklyEnrichment = {
        weekdayR,
        weekendR,
        note: `especially strong on ${stronger}`
      };
    }

    return correlation;
  }
```

**Step 2: Add enrichment to calculation pipeline**

In calculateAllCorrelations, before pushing correlation to array, add:

```javascript
      // Before: correlations.push(correlation);
      // After:
      const enrichedCorrelation = enrichWithWeeklyPatterns(correlation);
      correlations.push(enrichedCorrelation);
```

**Step 3: Update pattern card to show weekly note**

In renderPatternCard, after summary bars section, add:

```javascript
        <!-- Weekly Pattern Note -->
        ${correlation.weeklyEnrichment ? `
          <div style="margin-top: 12px; padding: 10px; background: rgba(58, 160, 255, 0.08); border-left: 3px solid #3aa0ff; border-radius: 4px;">
            <div style="font-size: 12px; color: #3aa0ff; font-weight: 600;">
              💡 This pattern is ${correlation.weeklyEnrichment.note}
            </div>
          </div>
        ` : ''}
```

**Step 4: Test weekly enrichment**

Manual test:
1. Reload page with data
2. Click Insights tab
3. Check if any patterns show weekly enrichment note
4. Verify note only appears when difference is meaningful

Expected: Some patterns may show "especially strong on weekdays/weekends" note

**Step 5: Commit (if implemented)**

```bash
git add index.html
git commit -m "Add optional weekly pattern enrichment to correlations"
```

---

## Task 10: Manual Testing and Verification

**Files:**
- None (manual browser testing only)

**Step 1: Test with full dataset**

Manual test checklist:
- [ ] Load page with 60+ days of sleep and activity data
- [ ] Click Insights tab
- [ ] Verify disclaimer banner shows with Wikipedia link
- [ ] Verify top discoveries section shows 3 patterns
- [ ] Verify sleep insights section populated
- [ ] Verify activity insights section populated
- [ ] Check confidence badges show correct colors
- [ ] Test "show more" buttons expand additional patterns
- [ ] Click scatter plot expand on multiple patterns
- [ ] Verify scatter plots render with color-coded points
- [ ] Hover over scatter points, verify tooltips show
- [ ] Collapse scatter plots, verify they hide
- [ ] Switch to Activity tab and back, verify Insights re-renders
- [ ] Check browser console for errors

**Step 2: Test with minimal dataset (14-30 days)**

Manual test checklist:
- [ ] Load page with exactly 14-20 days of data
- [ ] Click Insights tab
- [ ] Verify patterns show "Early pattern" badges (orange)
- [ ] Verify educational fallback shows for weak patterns
- [ ] Check console shows which pairs were skipped

**Step 3: Test with insufficient data (<14 days)**

Manual test checklist:
- [ ] Load page with <14 days of data
- [ ] Click Insights tab
- [ ] Verify educational fallback shows in top discoveries
- [ ] Verify research-based insights display
- [ ] Verify no correlation cards show

**Step 4: Test edge cases**

Manual test checklist:
- [ ] Load data with sleep but no workouts → verify workout correlations skipped
- [ ] Load data with activity but no sleep → verify sleep correlations skipped
- [ ] Verify negative correlations show red indicators
- [ ] Test with very sparse data (many gaps) → verify still calculates if ≥14 pairs

**Step 5: Performance testing**

Manual test checklist:
- [ ] Load with 365+ days of data
- [ ] Click Insights tab
- [ ] Verify dashboard loads in <3 seconds
- [ ] Switch tabs multiple times, verify no memory leaks
- [ ] Check browser performance tools for issues

**Step 6: Visual polish check**

Manual test checklist:
- [ ] Verify all text is readable (contrast, size)
- [ ] Check card spacing and alignment
- [ ] Verify colors match app theme
- [ ] Test on narrow browser window (responsive)
- [ ] Check scatter plots don't overlap with text

**Step 7: Document any issues found**

Create a list of bugs or improvements needed:
```
Issues found:
1. [Example: Scatter plot tooltip cuts off on right edge]
2. [Example: "Show more" button doesn't hide after expanding]
3. ...

Fixes needed:
- ...
```

**Step 8: Fix critical bugs**

Address any blocking issues found during testing before final commit.

---

## Task 11: Final Commit and Cleanup

**Files:**
- Modify: `index.html` (remove any debug code, add final comments)

**Step 1: Remove debug/test code**

Search for and remove:
- All `console.log` statements used for debugging (keep error logging)
- Any `// TEMP:` test code
- Unused variables or functions

**Step 2: Add documentation comments**

Ensure all major functions have JSDoc comments:
```javascript
/**
 * Calculate Pearson correlation coefficient
 * @param {Array<number>} x - Independent variable
 * @param {Array<number>} y - Dependent variable
 * @returns {number|null} Correlation coefficient or null if insufficient data
 */
```

**Step 3: Final browser test**

Quick smoke test:
- [ ] Load page
- [ ] Switch to Insights tab
- [ ] Verify everything works
- [ ] No console errors

**Step 4: Final commit**

```bash
git add index.html
git commit -m "Complete correlation engine implementation with pattern discovery"
```

**Step 5: Create summary of work**

Document what was built:
```
Correlation Engine - Implementation Complete

Features implemented:
✓ Correlation tab with discovery-first dashboard
✓ Pearson correlation calculation for 9 metric pairs
✓ Percentile-based bucketing for comparisons
✓ Confidence indicators (strong/moderate/early)
✓ Pattern cards with plain English summaries
✓ Interactive scatter plots with expand/collapse
✓ Top discoveries deduplication
✓ Sleep-heavy organization (70/30 split)
✓ Educational fallback for insufficient data
✓ Prominent "correlation ≠ causation" disclaimer
✓ [Optional: Weekly pattern enrichment]

Manual testing completed:
- Full dataset (60+ days): ✓
- Minimal dataset (14-30 days): ✓
- Insufficient data: ✓
- Edge cases: ✓
- Performance: ✓

Known limitations:
- Manual testing only (no automated tests)
- No multi-variate analysis
- No time-series overlays
- Weekly enrichment is optional

Ready for user testing and feedback.
```

---

## Testing Strategy

**No automated tests** - Following project pattern of manual browser testing only.

**Manual testing checklist provided in Task 10** covering:
- Full dataset scenarios
- Minimal dataset scenarios
- Insufficient data scenarios
- Edge cases (missing metrics, sparse data)
- Performance testing
- Visual polish verification

---

## Implementation Notes

1. **Single-file architecture**: All code goes in `index.html` following existing pattern
2. **No external dependencies**: Uses existing ECharts library already loaded
3. **Consistent styling**: Matches Activity and Sleep tabs visual theme
4. **Defensive coding**: Null checks and graceful degradation throughout
5. **Performance**: Caches correlations in `window.cachedCorrelations` for session
6. **Accessibility**: Tooltips explain all statistics concepts for beginners

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-11-correlation-engine-implementation.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Review between tasks
- Fast iteration
- **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development

**2. Parallel Session (separate)**
- Open new session with executing-plans
- Batch execution with checkpoints
- **REQUIRED SUB-SKILL:** superpowers:executing-plans

**Which approach do you prefer?**
