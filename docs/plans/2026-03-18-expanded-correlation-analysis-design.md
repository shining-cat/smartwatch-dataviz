# Expanded Correlation Analysis - Design Document

**Date:** 2026-03-18
**Status:** Approved
**Goal:** Broaden correlation analysis to include heart rate metrics, day-of-week patterns, and segmented insights

## Problem Statement

Current correlation analysis is limited to 9 metric pairs (steps, workout count/duration, sleep duration, bedtime). With nearly 2000 days of tracking data, no significant correlations are found.

However, the Withings year summary showed correlations like "sleep quality (resting HR) lower the night before office days" - suggesting day-of-week patterns and HR metrics are missing from our analysis.

## Objectives

1. Extract and analyze heart rate data from sleep and activity records
2. Detect day-of-week patterns (weekend vs weekday, specific day differences)
3. Implement segmented correlation analysis (how correlations vary by context)
4. Reorganize UI to present insights in order of complexity: simple patterns → correlations → nuanced insights

## Design

### 1. Data Extraction & New Metrics

#### From `sleep.csv` - Extend sleep records with:
- `avgHeartRate` - "Average heart rate" column
- `minHeartRate` - "Heart rate (min)" column
- `maxHeartRate` - "Heart rate (max)" column
- `hrvMetric` (if available) - HRV data if present

#### From `activities.csv` - Daily aggregates:
- `avgWorkoutHR` - Average of all workout HR averages per day
- `maxWorkoutHR` - Maximum HR reached across all workouts that day
- `workoutHRByType` - HR metrics grouped by activity type (walking, yoga, etc.)

#### Derived day-of-week metrics:
- `dayOfWeek` - Numeric 0-6 (already stored)
- `isWeekend` - Boolean flag (Saturday/Sunday)
- `dayName` - String for readability

#### New daily time series for correlation:
- `sleep_avg_hr`, `sleep_min_hr`, `sleep_max_hr`
- `workout_avg_hr`, `workout_max_hr`
- Existing: steps, sleep duration, bedtime, wake time, workout count/duration

**Result:** ~8 new metrics, enabling ~25-30 additional meaningful metric pairs

### 2. Statistical Analysis Methods

#### Pearson Correlations (existing, expanded)
- Keep current implementation for continuous-to-continuous metrics
- Add ~25 new pairs involving HR data:
  - Sleep HR → next day activity (recovery indicator)
  - Activity → sleep HR that night (stress/exertion impact)
  - Sleep HR → sleep duration (quality correlation)
  - Workout HR → steps (intensity patterns)
  - Cross-lag: previous day metrics → current HR

#### Categorical Day Analysis (NEW)

**Weekend vs Weekday comparison:**
- t-test for each metric (sleep duration, steps, HR, etc.)
- Effect size calculation (Cohen's d) to show magnitude
- Report format: "Weekend sleep: 7.2h vs Weekday: 6.5h (p<0.01, moderate effect)"

**Day-of-week patterns:**
- ANOVA across all 7 days for each metric
- Post-hoc tests to find which specific days differ (Monday vs Friday, etc.)
- Report format: "Mondays: -45min sleep vs weekly average (p<0.05)"

#### Segmented Correlations (NEW)
- Take existing/new correlations and split by:
  - Weekend vs weekday: "Steps → Sleep: r=0.32 weekdays, r=0.15 weekends"
  - Individual days (if sample size adequate): "Steps → Sleep stronger on Mondays (r=0.41)"
- Only show segmentation when:
  - Each segment has n≥20 data points
  - Correlation difference between segments ≥0.15 (meaningful difference)

#### Statistical Rigor
- Minimum sample size: n≥14 for correlations, n≥10 per group for t-tests
- Significance threshold: p<0.05 (p<0.01 for correlations to reduce false positives)
- Multiple comparison correction: False Discovery Rate (Benjamini-Hochberg) when testing many hypotheses

### 3. UI Organization & Presentation

Reorganize the Insights tab into four sections (in order):

#### 1. Top Discoveries
- Shows 3 strongest findings across ALL analysis types
- Could be a correlation, a day pattern, or a segmented insight
- Sorted by: statistical strength × effect size × sample size
- Visual badge shows type: "📊 Correlation" | "📅 Day Pattern" | "🔍 Segmented"

#### 2. Day Patterns (NEW)
- **Weekend vs Weekday comparison card:**
  - Table showing metrics with significant differences
  - Bar charts for visual comparison
  - Example: "Sleep: 7.2h weekend vs 6.5h weekday (+42min, p<0.01)"

- **Day-of-week standouts:**
  - Only show days that significantly differ from weekly average
  - Example: "Mondays: -45min sleep, +15bpm avg HR vs weekly average"

#### 3. Metric Correlations
- Split into subsections:
  - **Sleep Quality Insights** - Correlations where sleep metrics are dependent variable
  - **Activity Insights** - Correlations where activity metrics are dependent variable
  - **Heart Rate Insights** (NEW) - HR as dependent variable (recovery, stress indicators)
- Same card format as current, showing scatter plots on expand
- Show strong/moderate, collapse weak behind "Show more"

#### 4. Context Matters (NEW - Segmented Insights)
- Shows how correlations change by context
- Card format: "Steps → Sleep correlation varies by day type"
  - Chart showing: Weekday r=0.32 vs Weekend r=0.15
  - Interpretation: "Activity impacts sleep more on weekdays"
- Only shown when segmentation reveals meaningful differences

#### Empty State Handling
- If no significant findings in a section: "No significant patterns found. Keep tracking!"
- Educational fallback (current): show what was analyzed, encourage continued tracking

### 4. Implementation Details

#### New Functions
- `extractHeartRateMetrics(sleepCSV, activitiesCSV)` - Parse HR columns during ingestion
- `calculateDayPatterns()` - Weekend vs weekday t-tests, ANOVA for day-of-week
- `calculateSegmentedCorrelations(correlations, segments)` - Split correlations by weekend/weekday
- `organizeAllInsights(correlations, dayPatterns, segmented)` - New organizer replacing `organizeCorrelations()`
- `renderDayPatternsSection()`, `renderSegmentedSection()` - New UI renderers

#### Modified Functions
- `parseSingleCSV()` - Extract HR fields from sleep.csv, activities.csv
- `defineMetricPairs()` - Add ~25 new HR-related pairs
- `renderCorrelationDashboard()` - Orchestrate all three analysis types, render in new order

#### Data Storage
- Extend `sleepRecords` schema: add `avgHeartRate`, `minHeartRate`, `maxHeartRate`
- Create `workoutHRMetrics` series in daily aggregates
- No schema migration needed (IndexedDB auto-extends)

#### Performance Considerations
- All analysis runs client-side (as now)
- With ~2000 days, expect ~30-50 correlations, ~10 day patterns, ~20 segmented insights
- Total computation: <2 seconds (current is <1s for 9 correlations)

## Success Criteria

1. HR data successfully extracted from sleep.csv and activities.csv
2. Day-of-week patterns detected and displayed (weekend vs weekday, specific day standouts)
3. At least 25 new correlation pairs analyzed (HR-related)
4. Segmented correlations shown when meaningful differences exist
5. UI reorganized in approved order: Top Discoveries → Day Patterns → Correlations → Segmented
6. With 2000 days of data, surface at least some significant findings (even if no strong correlations exist)
7. Performance remains under 2 seconds for full analysis

## Future Enhancements (Out of Scope)

- Manual day tagging (office/home/vacation)
- Multi-factor interaction terms (statistical models)
- Time-series analysis (trend detection over months/years)
- HRV deep dive (if sufficient data quality)
