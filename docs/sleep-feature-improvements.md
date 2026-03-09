# Sleep Feature Improvement Ideas

**Date:** 2026-03-06

## 1. Filter Out Naps

**Feature:** Add a "Skip naps" button to filter suspected nap periods

**Criteria for nap detection:**
- Duration: less than 2 hours
- Start time: between 10:00 and 17:00

**Reasoning:** These criteria will never apply to actual night sleep periods

**Future use:** Nap vs night-sleep distinction could be valuable for correlation analysis engine

**Implementation notes:**
- Add checkbox/toggle in sleep controls section
- Filter sleep records before passing to analysis components
- Tooltip: "Suspected naps are periods of sleep of less than 2h, starting between 10:00 and 17:00"

---

## 2. Bedtime Scatter Chart: Color-Code by Sleep Duration

**Feature:** Enhance bedtime scatter chart by color-coding dots based on sleep duration

**Goal:** Visualize potential connections between bedtime and sleep duration at a glance

**Suggested color scale:**
- Red/Orange: Short sleep (<6h)
- Yellow/Green: Normal sleep (6-8h)
- Blue: Long sleep (>8h)

**Benefit:** Makes patterns visible - e.g., "Going to bed after midnight correlates with shorter sleep"

---

## 3. Bedtime Chart: Reorient Y-Axis (12:00 → 11:59)

**Current issue:** Y-axis goes from 00:00 to 24:00, which splits the bedtime dot cloud in two halves around midnight. Midnight itself has no particular significance for sleep/wake cycles.

**Proposed change:** Reorient Y-axis to go from 12:00 (noon) to 11:59 (next morning)

**Benefits:**
- More intuitive reading - matches natural sleep/wake distribution
- Bedtime cluster (typically 22:00-02:00) stays visually together
- Wake time cluster (typically 06:00-10:00) stays visually together
- Eliminates artificial midnight split

**Implementation:** Adjust Y-axis range and tick labels, wrap times accordingly (e.g., 23:00 → 11pm, 01:00 → 1am)

---

## Notes

All three improvements enhance the Sleep tab's readability and analytical power without adding complexity. Priority order suggested:
1. Nap filtering (quick win, high value for data quality)
2. Y-axis reorientation (significant UX improvement)
3. Color-coded duration (nice-to-have enhancement)
