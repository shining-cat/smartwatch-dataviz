# Health Data Export Analysis Report

**Generated:** 2026-03-05
**Data Source:** `/data/raw/health-export.zip`
**Analysis Agent:** Explore (very thorough)

---

## Executive Summary

**Dataset Scope:**
- **5+ years of continuous health data** (January 2021 - January 2026)
- **91 total files** from smartwatch health export
- **399 MB uncompressed** data
- **1,880 nightly sleep records** (98% temporal coverage)

**Sleep Deep Dive Feasibility:** ✅ **All three components fully feasible**
- Duration Analysis: Reliable sleep duration data available
- Timing Patterns: Bedtime/wake time extraction supported
- Weekly Patterns: 5+ years enables robust day-of-week statistics

---

## Critical Sleep Files

| File | Records | Date Range | Priority | Purpose |
|------|---------|------------|----------|---------|
| **sleep.csv** | 1,880 | 2021-01-15 to 2026-01-17 | CRITICAL | Aggregated nightly sleep summaries |
| **raw_tracker_sleep-state.csv** | 6,235 | 2021-01-15 to 2026-01-17 | HIGH | Minute-by-minute sleep staging |
| **raw_bed_sleep-state.csv** | 493 | 2021-06-01 to 2026-01-17 | MEDIUM | Bed sensor sleep staging (sparse) |
| **raw_bed_hr.csv** | 120,000+ | 2021-06-01 to 2026-01-17 | HIGH | Heart rate during sleep (1-sec granularity) |

---

## sleep.csv Structure

**Critical columns for Sleep Deep Dive:**

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `from` | ISO 8601 timestamp | Bedtime (sleep start) | **Timing Patterns** |
| `to` | ISO 8601 timestamp | Wake time (sleep end) | **Timing Patterns** |
| `lightsleepduration` | integer (seconds) | Light sleep duration | **Duration Analysis** |
| `deepsleepduration` | integer (seconds) | Deep sleep duration | **Duration Analysis** |
| `remsleepduration` | integer (seconds) | REM sleep duration (mostly 0) | ⚠️ Unreliable |
| `durationtosleep` | integer (seconds) | Time to fall asleep | Quality metric |
| `durationtowakeup` | integer (seconds) | Time to wake up | Quality metric |
| `wakeupcount` | integer | Number of wake-ups | Quality metric |
| `wakeupduration` | integer (seconds) | Total wake time during night | Quality metric |

**Sample data:**
```csv
from,to,lightsleepduration,deepsleepduration,remsleepduration,durationtosleep,wakeupcount
2026-01-16T23:35:00+01:00,2026-01-17T08:15:00+01:00,18360,10740,0,1320,2
2026-01-15T23:45:00+01:00,2026-01-16T08:00:00+01:00,17280,11520,0,840,1
```

**Calculated field needed:**
```javascript
// Total sleep duration in minutes
durationMinutes = (lightsleepduration + deepsleepduration + remsleepduration) / 60
durationHours = durationMinutes / 60
```

---

## Data Quality Assessment

### Strengths
✅ **Excellent temporal coverage** - 98% of nights across 5+ years
✅ **Reliable core metrics** - Sleep duration and timing consistent
✅ **High-frequency HR data** - 120K+ data points for correlation
✅ **Deep/Light distinction** - Sleep staging available
✅ **Long-term patterns** - 5+ years enables seasonal/yearly analysis

### Limitations
⚠️ **REM sleep unreliable** - Mostly zeros, don't rely on it
⚠️ **Apnea metrics sparse** - Only 24 records total
⚠️ **Respiratory rate unavailable** - Not collected by device
⚠️ **HRV metrics missing** - Would require raw HR processing
⚠️ **Some ordering inconsistencies** - Raw files may need sorting

### Data Validation Requirements

**Critical checks before processing:**
1. **Timestamp validity:** `from < to` (bedtime before wake time)
2. **Duration sanity:** `0 < total_sleep < 24 hours`
3. **Date parsing:** Handle timezone conversions (Europe/Paris, Europe/Stockholm)
4. **Missing values:** Filter out records with null critical fields
5. **Heart rate range:** 30-200 bpm (if using HR data)

---

## Sleep Deep Dive Implementation Recommendations

### Phase 1: Duration Analysis (Agent 1)

**Data Source:** `sleep.csv`

**Required calculations:**
```javascript
// Total sleep duration
totalSleep = (lightsleepduration + deepsleepduration + remsleepduration) / 3600 // hours

// Sleep efficiency
sleepEfficiency = totalSleep / (timeDifference(from, to)) * 100

// Distribution buckets
bins = ['<5h', '5-6h', '6-7h', '7-8h', '8-9h', '>9h']
```

**Output:**
- Histogram of sleep duration distribution
- Average, median, std deviation
- Consistency score (based on std dev)
- Healthy range highlighting (7-9h)

---

### Phase 2: Timing Patterns (Agent 2)

**Data Source:** `sleep.csv` columns: `from`, `to`

**Required extractions:**
```javascript
// Bedtime hour (24-hour format, e.g., 23.5 = 11:30 PM)
bedtimeHour = extractHourMinute(from)

// Wake time hour
wakeTimeHour = extractHourMinute(to)

// Consistency metrics
bedtimeStdDev = standardDeviation(bedtimeHours)
wakeTimeStdDev = standardDeviation(wakeTimeHours)
```

**Chronotype detection logic:**
```javascript
avgBedtime = mean(bedtimeHours)
if (avgBedtime < 22.0) return 'early-bird'
else if (avgBedtime > 24.0) return 'night-owl'
else return 'intermediate'
```

**Output:**
- Bedtime scatter plot (date vs time-of-day)
- Wake time scatter plot
- Consistency scores
- Chronotype classification

---

### Phase 3: Weekly Patterns (Agent 3)

**Data Source:** `sleep.csv`

**Required aggregation:**
```javascript
// Group by day of week
sleepByWeekday = groupBy(sleepData, d => new Date(d.date).getDay())

// Calculate averages per weekday
weekdayAverages = {
  Sun: mean(sleepByWeekday[0].map(d => d.durationHours)),
  Mon: mean(sleepByWeekday[1].map(d => d.durationHours)),
  // ... etc
}

// Weekend vs weekday comparison
weekdayAvg = mean([Mon, Tue, Wed, Thu, Fri])
weekendAvg = mean([Sat, Sun])
difference = weekendAvg - weekdayAvg
```

**Pattern detection:**
```javascript
// Identify strongest effect
weeklyMean = mean(Object.values(weekdayAverages))
deviations = weekdayAverages.map(avg => Math.abs(avg - weeklyMean))
strongestDay = argmax(deviations)
```

**Output:**
- Weekday bar chart (avg sleep per day)
- Weekend vs weekday comparison card
- Pattern insights (e.g., "Mondays: -45 min vs weekly avg")

---

## Parsing Implementation Notes

### Timezone Handling

Timestamps include timezone info (e.g., `+01:00`):
```javascript
// Use native Date parsing (supports ISO 8601 with timezone)
const bedtime = new Date('2026-01-16T23:35:00+01:00')

// Extract local hour (respects timezone)
const bedtimeHour = bedtime.getHours() + bedtime.getMinutes() / 60
```

### CSV Parsing

Already using PapaParse in the app:
```javascript
// Parse sleep.csv
Papa.parse(csvText, {
  header: true,
  dynamicTyping: true,
  skipEmptyLines: true,
  complete: (results) => {
    const sleepData = results.data.map(row => ({
      date: row.from.split('T')[0],
      from: row.from,
      to: row.to,
      durationMinutes: (row.lightsleepduration + row.deepsleepduration + row.remsleepduration) / 60,
      durationHours: (row.lightsleepduration + row.deepsleepduration + row.remsleepduration) / 3600,
      dayOfWeek: new Date(row.from).getDay(),
      weekdayName: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][new Date(row.from).getDay()]
    }))
  }
})
```

### Data Validation Filter

```javascript
// Filter valid sleep records
const validSleepData = sleepData.filter(d => {
  const fromDate = new Date(d.from)
  const toDate = new Date(d.to)
  const durationHours = d.durationHours

  return (
    fromDate < toDate &&                    // Bedtime before wake time
    durationHours > 0 &&                    // Positive duration
    durationHours < 24 &&                   // Less than 24 hours
    !isNaN(fromDate.getTime()) &&           // Valid timestamps
    !isNaN(toDate.getTime())
  )
})
```

---

## Phased Roadmap

### MVP (Phase 1) - Sleep Deep Dive Core
- ✅ Parse `sleep.csv` only
- ✅ Implement Duration Analysis (Agent 1)
- ✅ Implement Timing Patterns (Agent 2)
- ✅ Implement Weekly Patterns (Agent 3)
- ✅ Defensive error handling
- **Timeline:** Current sprint

### Phase 2 - Enhanced Insights
- Raw sleep state visualization (minute-level detail)
- Sleep efficiency calculations
- Quality score composites
- **Timeline:** Future feature

### Phase 3 - Correlation Analysis
- Heart rate correlation with sleep quality
- Activity vs sleep duration
- Seasonal pattern detection
- **Timeline:** Future feature

---

## Conclusion

**All Sleep Deep Dive components are fully feasible** with the available data. The `sleep.csv` file provides robust, high-quality data for duration, timing, and weekly pattern analysis across 5+ years.

**Recommended approach:**
1. Start with `sleep.csv` parsing (simple, reliable)
2. Implement three parallel agents as planned
3. Use data validation filters to handle edge cases
4. Consider Phase 2 enhancements after MVP validation

**Data quality is excellent for the MVP scope.** The main limitation (unreliable REM sleep) doesn't affect the planned features.
