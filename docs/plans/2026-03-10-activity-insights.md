# Activity Tab Insights Design

**Date:** 2026-03-10
**Status:** Approved
**Enhancement for:** Activity tab (existing implementation)

---

## Overview

Add trend indicators to overview cards and auto-generated pattern insights to the Weekly Patterns section. Enhances the Activity tab's habit monitoring capabilities by showing progress over time and highlighting behavioral patterns.

**Goals:**
1. Show metric trends (improving/declining) vs previous equal period
2. Auto-detect and display day-of-week workout patterns
3. Keep UI compact and readable

---

## Feature 1: Trend Indicators

### Display Location

All 4 overview cards in Workout Habits section:
- Workouts/week (last 30d)
- Current streak
- Longest gap
- Avg duration

### Calculation Logic

**For each metric:**
1. Calculate current period value (already exists)
2. Calculate previous equal period value:
   - If "Last month" selected → compare to previous month (days 31-60)
   - If "Last 3 months" → compare to previous 3 months (days 91-180)
   - If "Last 6 months" → compare to previous 6 months
   - If "Last 1 year" → compare to previous year
   - If "Last 2 years" → compare to previous 2 years
   - If "All time" → **hide trend** (no comparison possible)
3. Calculate percentage change: `((current - previous) / previous) * 100`
4. Classify trend:
   - `change > 5%` → positive trend (↑ green #3dce79)
   - `change < -5%` → negative trend (↓ red #ff5a6b)
   - `-5% ≤ change ≤ 5%` → stable (— gray #6b7a8f)

**Special Cases:**

- **Longest gap:** Invert colors (lower is better)
  - Decrease → green (improvement)
  - Increase → red (regression)
- **Division by zero:** Show "New data" instead of percentage
- **Current streak from 0:** Show "Started!" instead of "+∞%"
- **No previous data:** Hide trend line

### UI Format

Add trend as subtitle below existing card content:

```
┌─────────────────────┐
│ Workouts/week       │
│ 3.2                 │ ← main value
│ Last 30 days        │ ← subtitle
│ ↑ 12% vs prev period│ ← NEW: trend (green)
└─────────────────────┘
```

**Trend line styling:**
- Font size: 11px
- Margin-top: 4px
- Color: Conditional (green/red/gray)
- Format: `{arrow} {percentage}% vs previous period` OR `{arrow} Stable` OR `New data`

---

## Feature 2: Weekly Pattern Insights

### Display Location

New container below Weekly Patterns chart:
- Inline text format (single line)
- Centered text
- Background: #1a2332
- Border-radius: 6px
- Padding: 12px

### Pattern Detection Logic

Analyze weekly workout distribution (from existing `renderWorkoutWeeklyPatterns` data):

**Pattern Types:**

1. **Weekend Warrior**
   - Threshold: `weekend_avg / weekday_avg > 1.5`
   - Format: "💪 Weekend warrior: {ratio}x more workouts Sat/Sun"
   - Example: "💪 Weekend warrior: 2.5x more workouts Sat/Sun"

2. **Peak Day**
   - Threshold: Day has >30% of total workouts OR >1.5x weekly mean
   - Format: "🎯 {Day} peak ({percentage}% of workouts)"
   - Example: "🎯 Monday peak (35% of workouts)"

3. **Mid-week Slump**
   - Threshold: Day has <0.6x weekly mean AND is significantly lowest
   - Format: "Mid-week slump on {Day}"
   - Example: "Mid-week slump on Wednesday"

**Pattern Selection:**
- Show 0-2 patterns (most significant)
- Priority: Weekend warrior > Peak day > Slump
- Join multiple patterns with " • " separator
- Hide container if no patterns detected

**Example outputs:**
- "💪 Weekend warrior: 2.5x more workouts Sat/Sun • 🎯 Monday peak (35% of workouts)"
- "🎯 Saturday peak (40% of workouts)"
- "Mid-week slump on Wednesday"

---

## Implementation Notes

### New Functions

**`calculateTrends(currentStats, previousStats, selectedRange)`**
- Input: Current period stats, previous period stats, selected date range
- Output: Object with trend info for each metric
- Returns: `{ workoutsPerWeek: {direction, text}, currentStreak: {...}, ... }`

**`calculatePreviousPeriodStats(activityRecords, selectedRange, cutoffDate)`**
- Input: All activity records, selected range ("1m", "3m", etc), current cutoff date
- Output: Stats object for previous equal period
- Returns: Same format as `calculateWorkoutStats()`

**`detectWeeklyPatterns(weekdayAverages, weekdayNames)`**
- Input: Array of 7 average workout values, weekday names
- Output: Array of pattern strings
- Returns: `["💪 Weekend warrior: 2.5x more workouts Sat/Sun", "🎯 Monday peak (35%)"]`

### Modified Functions

**`renderWorkoutOverview(activityRecords, selectedType, selectedRange, cutoffDate)`**
- Add `selectedRange` and `cutoffDate` parameters
- Calculate trends using new helper functions
- Pass trend object to `mk()` card creator
- Update `mk()` to accept optional `trend` parameter

**`renderWorkoutWeeklyPatterns(activityRecords)`**
- Call `detectWeeklyPatterns()` after calculating weekday averages
- Populate `#workoutWeeklyInsights` container
- Show/hide container based on pattern presence

### HTML Changes

Add new container in Activity tab HTML:
```html
<div id="workoutWeeklyInsights" style="display:none;margin-top:12px;padding:12px;background:#1a2332;border-radius:6px;font-size:13px;color:#9fb0c3;text-align:center;"></div>
```

Place directly after `#workoutWeeklyPatternChart` container.

---

## Data Flow

```
User selects date range
    ↓
renderActivityDashboard()
    ↓
Calculate current period stats (existing)
    ↓
Calculate previous period stats (NEW)
    ↓
Calculate trends (NEW)
    ↓
renderWorkoutOverview() → Display cards with trends
    ↓
renderWorkoutWeeklyPatterns() → Calculate weekday averages
    ↓
detectWeeklyPatterns() → Generate insight strings (NEW)
    ↓
Display patterns below chart
```

---

## Testing Scenarios

**Trend Indicators:**
1. Select "Last month" → verify trend shows comparison to previous month
2. Select "All time" → verify trend is hidden
3. Test with no previous data → verify "New data" shown
4. Test streak from 0 → verify "Started!" shown
5. Test longest gap decrease → verify green color (improvement)

**Pattern Insights:**
1. Weekend-heavy workouts → verify "Weekend warrior" shown
2. Monday-heavy workouts → verify "Monday peak" shown
3. Even distribution → verify no patterns shown (container hidden)
4. Multiple patterns → verify bullet separator used

**Edge Cases:**
1. Single workout in period → no patterns detected
2. Less than 4 weeks data → existing validation prevents pattern calculation
3. All workouts on one day → verify only one pattern shown

---

## Success Criteria

- [ ] All 4 overview cards show trend indicators when date range selected
- [ ] Trends hidden for "All time" range
- [ ] Trend colors correct (green=good, red=bad, gray=stable)
- [ ] Longest gap uses inverted color logic
- [ ] Pattern insights detect weekend warrior pattern
- [ ] Pattern insights detect peak day pattern
- [ ] Pattern insights detect mid-week slump
- [ ] Multiple patterns joined with " • " separator
- [ ] Pattern container hidden when no patterns detected
- [ ] UI remains compact and readable

---

## Out of Scope

**Not included in this enhancement:**
- Activity type patterns (e.g., "Yoga on weekdays, Walking on weekends")
- Duration patterns (e.g., "Weekend workouts are longer")
- Seasonal patterns (e.g., "Most active in summer")
- Trend graphs/sparklines
- Historical trend data beyond previous period
- User-configurable pattern thresholds
