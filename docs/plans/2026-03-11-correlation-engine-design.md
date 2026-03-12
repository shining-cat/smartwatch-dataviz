# Correlation Engine Design

**Date:** 2026-03-11
**Status:** Approved
**Author:** Design collaboration with user

## Overview

The correlation engine is a new tab that helps users discover relationships between their health metrics (sleep, activity, weight) through pattern discovery. It's designed for users with low statistics experience, making correlations accessible through visual indicators, plain English summaries, and prominent disclaimers about correlation vs causation.

## Goals

1. **Pattern discovery** - Automatically surface interesting correlations in user's personal data
2. **Beginner-friendly** - Make statistics accessible without overwhelming non-experts
3. **Actionable insights** - Show practical differences (e.g., "32 minutes more sleep on high-step days")
4. **Transparency** - Prominent disclaimer about correlation ≠ causation
5. **Data quality awareness** - Clear confidence indicators based on sample size

## Non-Goals

- Statistical deep-dive tools (p-values, confidence intervals, etc.)
- Predictive modeling or forecasting
- Automated recommendations ("you should do X")
- Multi-variate analysis (controlling for confounding variables)

## Overall Architecture

### Tab Structure

```
Correlation Tab (💡 icon)
├── Disclaimer Banner
│   └── Wikipedia link + "Correlation does not imply causation" quote
├── Top Discoveries (3 strongest patterns)
│   └── Deduplicated - won't appear in sections below
├── Sleep Insights (70% focus)
│   ├── Strong patterns (always visible)
│   └── "Show more" → Moderate patterns
├── Activity Insights (30% focus)
│   ├── Strong patterns (always visible)
│   └── "Show more" → Moderate patterns
└── Educational Fallback (when insufficient data)
```

### Data Flow

1. **Fetch** - Load all daily metrics from IndexedDB (sleep, steps, workouts, weight)
2. **Align** - Build overlapping date ranges for each metric pair
3. **Calculate** - Compute Pearson correlations with appropriate lag structures
4. **Filter** - Apply data quality thresholds (minimum 14 days overlap)
5. **Rank** - Sort by correlation strength and statistical confidence
6. **Deduplicate** - Remove top discoveries from category sections
7. **Render** - Display with confidence badges, summaries, and visualizations

### Why Sleep-Heavy (70/30 split)?

Sleep is:
- The richest dataset (continuous tracking, multiple dimensions)
- A passive outcome influenced by daily activities
- The primary health metric users want to optimize
- More likely to show meaningful correlations

Activity insights (30%) still valuable but secondary focus.

## Correlation Calculation

### Metric Pairs to Calculate

**Sleep as target (70% weight):**
- Sleep duration ← Same-day steps
- Sleep duration ← Same-day workout count
- Sleep duration ← Same-day total workout duration
- Sleep duration ← Previous night's sleep duration (momentum)
- Bedtime ← Same-day steps
- Bedtime ← Same-day workout count

**Activity as target (30% weight):**
- Steps ← Last night's sleep duration
- Workout count ← Last night's sleep duration
- Workout total duration ← Last night's sleep duration

### Lag Structure

Three relationship types:
1. **Same-day activity → Sleep**: Today's steps/workouts → tonight's sleep
2. **Last night's sleep → Today's activity**: Previous night → today's steps/workouts
3. **Sleep momentum**: Last night's sleep → tonight's sleep (consistency patterns)

### Statistical Approach

**Algorithm:** Pearson correlation coefficient (r-value)

**Strength Classification:**
- **Strong**: |r| ≥ 0.5 (explains 25%+ of variance)
- **Moderate**: 0.3 ≤ |r| < 0.5 (explains 9-25% of variance)
- **Weak**: 0.15 ≤ |r| < 0.3 (explains 2-9% of variance)
- **None/Noise**: |r| < 0.15 (not shown)

**Confidence Levels (by sample size):**
- 🟢 **Strong confidence**: 60+ overlapping days
- 🟡 **Moderate confidence**: 30-60 days
- 🟠 **Early pattern**: 14-30 days

**Minimum Requirements:**
- At least 14 overlapping data points to calculate
- Only show correlations ≥ "weak" strength (|r| ≥ 0.15)

### Bucketing for Comparisons

**Percentile-based (personalized to user):**
- **Bottom 33%**: "Low" (e.g., low-step days)
  - Tooltip: "Your lowest third of days for this metric"
- **Middle 34%**: "Medium" (typical days)
  - Tooltip: "Your typical/average days"
- **Top 33%**: "High" (best days)
  - Tooltip: "Your best third of days for this metric"

Why percentiles? Automatically adapts to each user's baseline without requiring knowledge of health guidelines.

### Weekly Pattern Enrichment

For each correlation:
1. Calculate separate correlations for weekdays vs weekends
2. If difference ≥ 0.2, show enrichment note:
   - "💡 This pattern is especially strong on weekdays"
   - "💡 This pattern is especially strong on weekends"

## Visualization & UI Components

### Individual Pattern Display

Each discovered pattern shows:

```
[🟢 Strong confidence: 65 days] High Step Days → Better Sleep

"On your high step days (>8,500 steps), you sleep 32 minutes
longer on average compared to low step days"

🟢 Strong positive relationship

Summary Bars:
Low days (1,200-5,400 steps):     ████░░░░░░ 6.2h avg
Medium days (5,400-8,500 steps):  ██████░░░░ 6.8h avg
High days (8,500-14,200 steps):   ████████░░ 7.4h avg

[▼ Show scatter plot]
  (When expanded: ECharts scatter with trend line,
   points color-coded by bucket)

💡 This pattern is especially strong on weekdays
```

**Visual Relationship Indicators:**
- 🟢 Strong positive (r ≥ 0.5)
- 🟡 Moderate positive (0.3 ≤ r < 0.5)
- 🟠 Weak positive (0.15 ≤ r < 0.3)
- 🔴 Strong negative (r ≤ -0.5)
- 🟠 Moderate negative (-0.5 < r ≤ -0.3)
- ⚪ Weak negative (-0.3 < r ≤ -0.15)

### Disclaimer Banner

```
⚠️ Remember: Correlation ≠ Causation

These patterns show relationships in YOUR data, not proof of
cause-and-effect. Just because two things happen together doesn't
mean one causes the other.

[Learn more: Correlation does not imply causation (Wikipedia)]

"Correlation does not imply causation" - attributed to statistics,
widely used in science education
```

**Styling:**
- Subtle warning color (not alarmist orange/red)
- Always visible at top of tab
- Wikipedia link opens in new tab
- Collapsible after first view (localStorage flag)

### Top Discoveries Section

**Purpose:** Highlight the 3 most interesting findings immediately

**Selection criteria:**
1. Strongest correlation strength (|r| value)
2. Weighted toward sleep (70/30 split maintained)
3. Must have at least "moderate" confidence (30+ days)

**Display:**
- Larger cards than category sections
- More prominent styling (subtle highlight border)
- Deduplicated from sections below (each pattern shown once)

### Educational Fallback

**When shown:**
- If 0 strong patterns: Show immediately at top
- If only weak patterns: Show before weak patterns section
- If enough strong patterns: Don't show

**Content:**
```
📚 Building Your Personal Insights

You need at least 14 days of overlapping data to discover patterns.
Current status:
• Sleep data: 8 days (need 6 more)
• Activity data: 12 days (need 2 more)

While you're tracking, here's what research shows:
• Regular exercise generally improves sleep quality
• Consistent sleep schedules help maintain energy levels
• Physical activity during the day helps regulate circadian rhythm

Keep tracking to unlock your personalized discoveries!
```

**Dismissible:**
- "Don't show this again for 7 days" checkbox
- Stored in localStorage
- Reappears if data quality improves (new patterns available)

## Error Handling & Edge Cases

### Data Quality Issues

**Insufficient overlap (<14 days):**
- Don't calculate correlation
- Don't show in UI
- Log to console for debugging: `Skipped steps↔sleep: only 9 overlapping days`

**Missing data patterns:**
- 0 workouts tracked → Skip all workout correlations, hide from UI
- 0 weight data → Skip weight correlations
- Partial data (e.g., sleep but no activity) → Show what's available, note what's missing

**Sparse data (many gaps):**
- Still calculate if ≥14 non-null pairs exist
- Pearson correlation handles gaps naturally
- Confidence badge reflects actual sample size

**Outliers:**
- Don't filter automatically (user's real data)
- Pearson correlation somewhat robust to outliers
- Future: Could add note if extreme outliers detected

### Empty States

**No patterns found (all sections empty):**
```
📊 Not Enough Data Yet

To discover correlations, you need:
✓ At least 14 days of sleep tracking
✓ At least 14 days of activity tracking (steps or workouts)
✓ Both metrics tracked on the same days

Current progress: 8/14 days

[Show educational fallback with research-based insights]
```

**Sleep Insights empty, but Activity Insights has patterns:**
- Show activity section normally
- In sleep section placeholder: "Keep tracking sleep to unlock insights here (5 more days needed)"

**Top Discoveries empty:**
- Fall back to showing category sections (Sleep/Activity Insights)
- If those are also empty → single educational fallback

### Performance Considerations

**Calculation timing:**
- Run correlations on-demand when Correlation tab opens
- Show loading state: "Analyzing your patterns..." (spinner + progress bar)
- Cache results in memory for current session
- Recalculate only when:
  - Tab switches away and back
  - New data uploaded
  - Page refresh

**Large datasets:**
- Expected performance: <2 seconds for 365+ days of data
- Correlation calculation is O(n) per pair, ~10-15 pairs total
- No pagination needed (showing top patterns only)

**Memory usage:**
- Store only calculated correlations, not full datasets
- Release cached results on tab switch

### UI State Management

**"Show more" toggles:**
- Persist within session (stays expanded until page reload)
- Separate state for Sleep Insights vs Activity Insights

**Scatter plot expand/collapse:**
- Per-pattern state (each pattern independent)
- Default: collapsed (summary bars visible)
- Stored in session, not localStorage

**Educational fallback dismissal:**
- localStorage flag: `correlation_edu_dismissed`
- Timestamp stored, expires after 7 days
- Resets if new strong patterns detected (notify user of discoveries)

## Implementation Notes

### Code Organization

All code in `index.html` following existing pattern:

```javascript
// Correlation calculation functions (~200-300 lines)
function calculatePearsonCorrelation(x, y) { ... }
function bucketByPercentile(values) { ... }
function calculateCorrelations(metrics) { ... }
function enrichWithWeeklyPatterns(correlation) { ... }

// Rendering functions (~300-400 lines)
function renderCorrelationTab() { ... }
function renderTopDiscoveries(correlations) { ... }
function renderSleepInsights(correlations) { ... }
function renderActivityInsights(correlations) { ... }
function renderPatternCard(correlation) { ... }
function renderScatterPlot(correlation, containerId) { ... }

// Tab switching logic (add to existing)
if (tabCorrelation.active) { await renderCorrelationTab(); }
```

### Data Structures

**Correlation object:**
```javascript
{
  id: "steps_to_sleep_duration",
  independent: "aggregates_steps",
  dependent: "sleep_duration_min",
  lag: "same_day", // or "previous_day"
  r: 0.62,
  strength: "strong", // strong | moderate | weak
  direction: "positive", // positive | negative
  sampleSize: 65,
  confidence: "strong", // strong | moderate | early
  buckets: {
    low: { threshold: [0, 5400], avg: 372, count: 21 },
    medium: { threshold: [5400, 8500], avg: 408, count: 22 },
    high: { threshold: [8500, 20000], avg: 444, count: 22 }
  },
  weeklyEnrichment: {
    weekdayR: 0.68,
    weekendR: 0.45,
    note: "especially strong on weekdays"
  },
  scatterData: [
    { x: 3200, y: 360, bucket: "low" },
    { x: 8900, y: 450, bucket: "high" },
    ...
  ]
}
```

### Testing Strategy

**Manual browser testing:**
1. Load with full dataset (365+ days) → verify all patterns render
2. Load with minimal dataset (14 days) → verify early pattern badges
3. Load with no overlapping data → verify educational fallback
4. Toggle "show more" → verify expand/collapse
5. Expand scatter plots → verify chart renders correctly
6. Test with missing metrics (no workouts) → verify graceful hiding
7. Test disclaimer dismissal → verify localStorage persistence

**No automated tests** (following project pattern of manual testing only)

## Open Questions

None - design approved and ready for implementation planning.

## Future Enhancements (Out of Scope for MVP)

1. **Multi-variate analysis** - Control for confounding variables (e.g., "steps → sleep, controlling for workout intensity")
2. **Time-series visualization** - Overlay both metrics on same timeline to see co-movement
3. **Custom metric selection** - Let users pick any two metrics to compare (not just predefined pairs)
4. **Export discoveries** - Save insights as PDF or share-friendly format
5. **Trend over time** - "This correlation is getting stronger over the last 3 months"
6. **Weather/external data** - Correlate with weather, moon phase, etc. (requires external API)

## References

- Existing Activity tab patterns (trend indicators, weekly patterns)
- Existing Sleep tab visualizations (scatter plots, summary cards)
- Wikipedia: [Correlation does not imply causation](https://en.wikipedia.org/wiki/Correlation_does_not_imply_causation)
- Statistical threshold choices based on common effect size guidelines (Cohen's benchmarks)
