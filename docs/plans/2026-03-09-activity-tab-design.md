# Activity Tab Design

**Date:** 2026-03-09
**Status:** Approved
**Replaces:** Weekly Seasonality tab

---

## Overview

Replace the "Weekly Seasonality" tab with a new "Activity" tab focused on **habit monitoring** (primary) and **pattern discovery** (secondary). The tab analyzes discrete workout sessions from `activities.csv` alongside daily step aggregates, prioritizing insights about workout consistency and behavior patterns over raw performance metrics.

**Key Design Principles:**
1. **Habit monitoring first** - Focus on consistency, streaks, gaps
2. **Pattern discovery second** - Weekly patterns, seasonal trends, type preferences
3. **Conditional detail** - Show distance/elevation only when relevant
4. **Defensive coding** - Graceful degradation, data validation, error boundaries
5. **Mirror Sleep tab structure** - Reuse proven patterns (sections, date filtering, insight cards)

---

## Architecture

### Tab Structure

**New Tab:** "Activity" (4th tab, alongside Timeline, Seasonality → removed, Sleep)

**Replacement Strategy:**
- Remove "Weekly Seasonality" tab entirely
- Calendar heatmap moves to Activity tab (focused on workouts, not arbitrary metrics)
- Seasonality functionality no longer needed - Activity and Sleep tabs provide better focused analysis

**Page Layout:**
```
Activity Tab
├─ Controls Card
│  ├─ Master date range selector (Last month, 3m, 6m, 1y, 2y, All time)
│  ├─ Activity type filter dropdown (All, Walking, Yoga, Cycling, etc.)
│  └─ "Render activity" button
│
├─ Section 1: Daily Steps (BASELINE - smaller, at top)
│  ├─ Steps time series chart (with 7-day rolling average)
│  └─ Weekly average bar chart
│
└─ Section 2: Workout Habits (PRIMARY - detailed analysis)
   ├─ Overview Cards (4 insight cards)
   ├─ Workout Calendar Heatmap
   ├─ Activity Type Distribution (bar chart)
   ├─ Weekly Patterns (day-of-week analysis)
   └─ Distance/Elevation Section (conditional - only for Walking/Hiking/Cycling)
```

### Data Sources

**Primary:**
- `activities.csv` - 5,635 discrete workout sessions
  - Columns: from, to, Activity type, Data (JSON), GPS, Timezone
  - Activity types: Walking (3,195), Multi Sport (1,368), Yoga (526), Gym class (251), Cycling (177), Swimming (28), Running (3), Climbing (8), Hiking (32), Horse riding (1), Other (46)

**Secondary:**
- `aggregates_steps.csv` - Daily step counts (784 records)

**Storage:**
- IndexedDB table: `activityRecords` (similar to `sleepRecords`)
- Indexed by date for fast filtering
- Persists across sessions

---

## Components & Visualizations

### Controls Card

**Master Date Range Selector:**
- Dropdown options: Last month, Last 3 months, Last 6 months, Last 1 year, Last 2 years, All time
- Default: All time
- Filters all charts and stats on the page simultaneously
- Same implementation as Sleep tab's date range filter

**Activity Type Filter:**
- Dropdown options: All Activities (default), Walking, Yoga, Cycling, Multi Sport, etc.
- Dynamically populated from available activity types in dataset
- When changed:
  - Re-filters activityRecords
  - Recalculates overview cards
  - Shows/hides distance/elevation section
  - Updates all charts

**Render Button:**
- Triggers data load and visualization rendering
- Shows progress indicator during load

### Section 1: Daily Steps

**Purpose:** Baseline activity context - shows "forced" daily movement

**Components:**

**1. Steps Time Series Chart**
- X-axis: Date (respects date range filter)
- Y-axis: Daily step count
- Series 1: Daily steps (bar chart, max width 12px)
- Series 2: 7-day rolling average (line, smooth)
- Tooltip: Date + step count formatted with thousands separator
- Empty state: "No step data available for selected date range"

**2. Weekly Average Bar Chart**
- X-axis: Mon-Sun
- Y-axis: Average steps per weekday
- Color coding: Green = above weekly avg, Blue = normal, Red = below weekly avg
- Tooltip: "Monday: 8,234 steps (12% below weekly average)"

### Section 2: Workout Habits

**Purpose:** Primary focus - intentional activity tracking and habit monitoring

#### Overview Cards (4 cards, responsive grid)

**When "All Activities" selected (default):**

1. **Workouts/week (last 30d)**
   - Value: Average workouts per week
   - Calculation: Count workouts in last 30 days / (30/7)
   - Tooltip: "Your average weekly workout frequency over the last 30 days"

2. **Current streak**
   - Value: Consecutive weeks with ≥1 workout
   - Format: "X weeks" or "X days" (if <1 week)
   - Tooltip: "How many consecutive weeks you've had at least one workout"

3. **Longest gap**
   - Value: Maximum days without any workout (in date range)
   - Format: "X days"
   - Tooltip: "Your longest period without a workout in the selected date range"

4. **Avg duration**
   - Value: Average workout duration across all types
   - Format: "Xh Ymin" or "X min"
   - Tooltip: "Average duration across all workouts in selected range"

**When specific activity type selected (e.g., "Walking"):**

1. **Walking sessions**
   - Value: Count of walking sessions (in date range)
   - Subtitle: "Last 30 days" or date range description

2. **Avg duration**
   - Value: Average walking workout duration
   - Format: "Xh Ymin"

3. **Avg distance** (conditional)
   - Value: Average distance per walking session
   - Format: "X.X km"
   - Only shown if activity type has distance data

4. **Avg elevation** (conditional)
   - Value: Average elevation gain per session
   - Format: "X m"
   - Only shown if activity type has elevation data

#### Workout Calendar Heatmap

**Visualization:**
- Type: Calendar heatmap (ECharts calendar component)
- X-axis: Weeks (7 columns: Mon-Sun)
- Y-axis: Months/Years (depending on date range)
- Cell color intensity: Number of workouts per day
  - 0 workouts: Dark background (#1f2a3a)
  - 1 workout: Light blue
  - 2 workouts: Medium blue
  - 3+ workouts: Bright blue
- Cell size: Dynamic based on date range (10-20px, same as Seasonality implementation)
- Range: Respects master date range filter

**Tooltip:**
- Format: "3 workouts on 2025-12-15"
- Details: "Walking (45min), Yoga (30min), Gym (60min)"

**Empty state:** "No workout data available for selected date range"

#### Activity Type Distribution

**Visualization:**
- Type: Horizontal bar chart
- X-axis: Number of sessions
- Y-axis: Activity types (sorted by count, descending)
- Bars show: Count + percentage
- Example: "Walking ████████████████ 3,195 (57%)"

**Interaction:**
- Click bar → Filters to that activity type (updates all components)
- Visual indicator on selected type

**Respects filters:**
- Date range: Only counts sessions in selected range
- Activity type filter: Highlights selected type

#### Weekly Patterns

**Visualization:**
- Type: Bar chart (same pattern as Sleep tab's Weekly Patterns)
- X-axis: Mon-Sun
- Y-axis: Average workouts per day
- Color coding:
  - Green: Above weekly average (>10% deviation)
  - Blue: Normal range (±10% of weekly avg)
  - Red: Below weekly average (<-10% deviation)

**Pattern Insights** (below chart):
- Auto-generated insight cards based on detected patterns:
  - "Weekend warrior: 2x more workouts on Sat/Sun vs weekdays"
  - "Monday motivated: 35% of workouts happen on Mondays"
  - "Wednesday slump: fewest workouts mid-week"
- Only show insights with significant patterns (>20% deviation or >1.5x multiplier)

**Tooltip:**
- Format: "Monday: 1.2 avg workouts (15% above weekly average)"

#### Distance/Elevation Section (Conditional)

**Visibility Rules:**
- Only shown when activity type filter is set to: Walking, Hiking, Cycling, Running
- Hidden for: All Activities, Yoga, Gym class, Swimming, Multi Sport, Other
- Graceful show/hide transition (no page jump)

**Components:**

**1. Distance Over Time**
- Type: Line chart
- X-axis: Date
- Y-axis: Distance (km)
- Series 1: Distance per workout (scatter points)
- Series 2: 7-workout rolling average (line, smooth)
- Tooltip: "Walking on 2025-12-15: 5.2 km"

**2. Elevation Over Time**
- Type: Line chart (same structure as distance)
- Y-axis: Elevation gain (m)

**3. Stats Cards** (2 cards side-by-side)
- **Avg distance:** Mean distance per session (format: "X.X km")
- **Total distance:** Sum of all distances in date range (format: "XXX km")
- **Avg elevation:** Mean elevation gain per session (format: "XX m")
- **Highest elevation:** Max elevation workout (format: "XXX m on 2025-08-12")

---

## Data Flow & Processing

### Data Ingestion

**Parse activities.csv:**
```javascript
// Raw CSV row
{
  from: '2026-01-16T10:30:00+01:00',
  to: '2026-01-16T11:15:00+01:00',
  'Activity type': 'Walking',
  Data: '{"calories":159,"hr_average":144,"hr_min":88,"hr_max":183,"steps":4247,"distance":3570,"elevation":182}',
  GPS: '{"latitude":[...],"longitude":[...]}'
}

// Transform to ActivityRecord
{
  date: '2026-01-16',              // Derived from 'from' timestamp
  from: '2026-01-16T10:30:00+01:00',
  to: '2026-01-16T11:15:00+01:00',
  activityType: 'Walking',          // Cleaned from 'Activity type'
  durationMinutes: 45,              // Calculated: (to - from) / 60000
  durationHours: 0.75,              // durationMinutes / 60

  // Parsed from Data JSON (all nullable)
  hrAverage: 144,
  hrMin: 88,
  hrMax: 183,
  calories: 159,
  distance: 3570,    // meters (null if not present)
  elevation: 182,    // meters (null if not present)
  steps: 4247
}
```

**Store in IndexedDB:**
```javascript
// Schema
db.version(4).stores({
  activityRecords: 'date, activityType, from'
});

// Batch insert
await db.activityRecords.bulkPut(validActivityRecords);
```

### Date Range Filtering

**Master Filter Implementation:**
```javascript
function filterByDateRange(data, cutoffDate) {
  if (!cutoffDate || !data) return data;
  const cutoffStr = cutoffDate.toISOString().split('T')[0];

  if (Array.isArray(data)) {
    return data.filter(record => {
      if (!record.date) return true;
      return record.date >= cutoffStr;
    });
  }
  return data;
}

// Apply to all data sources
const filteredWorkouts = filterByDateRange(activityRecords, cutoffDate);
const filteredSteps = filterByDateRange(stepAggregates, cutoffDate);
```

### Activity Type Filtering

**Secondary Filter:**
```javascript
function filterByActivityType(activityRecords, selectedType) {
  if (selectedType === 'all') return activityRecords;
  return activityRecords.filter(r => r.activityType === selectedType);
}

// Conditional visibility logic
function shouldShowDistanceElevation(activityType) {
  const distanceTypes = ['Walking', 'Hiking', 'Cycling', 'Running'];
  return activityType !== 'all' && distanceTypes.includes(activityType);
}
```

### Data Validation (Defensive Coding)

**Pre-Processing Validation:**
```javascript
function validateActivityRecord(record) {
  const issues = [];

  // Timestamp validation
  const fromDate = new Date(record.from);
  const toDate = new Date(record.to);
  if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
    issues.push('Invalid timestamps');
  }
  if (fromDate >= toDate) {
    issues.push('Start time must be before end time');
  }

  // Duration validation
  const durationMinutes = (toDate - fromDate) / 60000;
  if (durationMinutes <= 0 || durationMinutes > 1440) {
    issues.push('Invalid duration (must be 0-24 hours)');
  }

  // Activity type validation
  if (!record.activityType || record.activityType.trim() === '') {
    issues.push('Missing activity type');
  }

  // HR validation (if present)
  if (record.hrAverage != null) {
    if (record.hrAverage < 30 || record.hrAverage > 200) {
      issues.push('Heart rate out of valid range (30-200 bpm)');
    }
  }

  // Distance/elevation validation (if present)
  if (record.distance != null && record.distance < 0) {
    issues.push('Distance cannot be negative');
  }
  if (record.elevation != null && record.elevation < 0) {
    issues.push('Elevation cannot be negative');
  }

  return {
    valid: issues.length === 0,
    issues: issues,
    record: record
  };
}

// Filter valid records
const validated = activityRecords.map(validateActivityRecord);
const validRecords = validated.filter(v => v.valid).map(v => v.record);
const invalidCount = validated.filter(v => !v.valid).length;

if (invalidCount > 0) {
  console.warn(`Filtered out ${invalidCount} invalid activity records`);
}
```

### Graceful Degradation

**Missing Data Handling:**
- No HR data → Skip HR-based insights (don't show HR cards/charts)
- No distance/elevation → Hide distance/elevation section
- No workouts in date range → Show "No workouts found in selected date range" message
- Empty dataset → Show "No activity data loaded. Upload your data to get started."

**Error Boundaries:**
```javascript
try {
  await renderWorkoutHabits(validRecords, containerId);
} catch (error) {
  console.error("Workout Habits rendering error:", error);
  const el = $(containerId);
  if (el) el.innerHTML = `<div class="notice">Workout analysis unavailable: ${error.message}</div>`;
}
```

---

## Implementation Notes

### Code Organization

**New Functions:**
- `ingestActivitiesCSV()` - Parse activities.csv, validate, store in IndexedDB
- `fetchActivityRecords()` - Retrieve from IndexedDB
- `renderActivityDashboard()` - Main orchestrator (like `renderSleepDashboard`)
- `renderDailySteps()` - Steps section rendering
- `renderWorkoutOverview()` - Overview cards
- `renderWorkoutHeatmap()` - Calendar heatmap
- `renderActivityTypeDistribution()` - Bar chart
- `renderWeeklyWorkoutPatterns()` - Weekly analysis
- `renderDistanceElevation()` - Conditional distance/elevation charts

**Reuse from Sleep Tab:**
- `filterByDateRange()` helper
- Date range selector UI pattern
- Insight card HTML structure
- Error boundary pattern
- Progress indicator system

### Performance Considerations

- Lazy load activity data (only when Activity tab selected)
- Index activityRecords by date for fast filtering
- Debounce filter changes (300ms delay)
- Virtualize activity type list if >20 types
- Cache calculated stats (invalidate on filter change)

### Browser Compatibility

- Modern browsers only (Chrome, Firefox, Safari, Edge)
- IndexedDB required (no fallback)
- ECharts for all visualizations
- No polyfills needed (ES6+ assumed)

---

## Testing Strategy

**Data Quality:**
1. Parse activities.csv with real data
2. Verify record count matches file (5,635 sessions)
3. Check activity type distribution
4. Validate HR/distance/elevation parsing

**Filtering:**
1. Test date range filter on all charts
2. Test activity type filter show/hide logic
3. Test combined filters (date + type)
4. Test edge cases (empty results, single record)

**Visualizations:**
1. Verify calendar heatmap cell sizing
2. Check bar chart scaling
3. Test tooltip content accuracy
4. Verify color coding logic

**Defensive Coding:**
1. Test with malformed CSV data
2. Test with missing required fields
3. Test with out-of-range values
4. Verify error messages display correctly

---

## Future Enhancements (Out of Scope)

**Phase 2:**
- GPS track visualization (route maps)
- Activity correlation analysis (e.g., "Do walking workouts improve sleep?")
- Heart rate zone distribution analysis
- Activity intensity trends over time
- Export workout data to CSV

**Phase 3:**
- Multi-sport session breakdown (parse nested activities in Multi Sport type)
- Swimming-specific metrics (laps, strokes, pool length)
- Workout goal setting and tracking
- Social sharing/comparison features

---

## Success Criteria

**Must Have:**
- [ ] Activity tab replaces Seasonality tab
- [ ] Parses activities.csv successfully
- [ ] Displays all 4 overview cards with accurate calculations
- [ ] Calendar heatmap shows workout density correctly
- [ ] Activity type distribution bar chart functional
- [ ] Weekly patterns analysis working
- [ ] Date range filter affects all components
- [ ] Activity type filter shows/hides distance/elevation section
- [ ] Daily steps section displays time series + weekly averages
- [ ] Defensive validation filters invalid records
- [ ] Error boundaries handle rendering failures gracefully

**Nice to Have:**
- [ ] Smooth transitions on filter changes
- [ ] Loading skeletons during data fetch
- [ ] Tooltips on all charts with helpful explanations
- [ ] Keyboard navigation support
- [ ] Responsive layout on smaller screens

---

## Migration Plan

**Step 1: Data Ingestion**
- Add activities.csv to allowed files list
- Implement parsing logic
- Create activityRecords IndexedDB table
- Validate with real data

**Step 2: UI Structure**
- Remove "Weekly Seasonality" tab
- Add "Activity" tab
- Create controls card with date range + activity type filters
- Add section containers

**Step 3: Components (Incremental)**
1. Daily Steps section (reuse Timeline chart patterns)
2. Overview cards (reuse Sleep insight card pattern)
3. Workout calendar heatmap (adapt from Seasonality heatmap)
4. Activity type distribution
5. Weekly patterns (adapt from Sleep weekly patterns)
6. Distance/elevation section (conditional)

**Step 4: Integration**
- Wire up date range filter
- Wire up activity type filter
- Test all filter combinations
- Add defensive validation
- Add error boundaries

**Step 5: Polish**
- Add tooltips
- Tune chart colors
- Optimize performance
- Final testing

---

## Open Questions

None - design approved and ready for implementation.
