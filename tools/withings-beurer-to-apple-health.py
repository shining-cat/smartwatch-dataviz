#!/usr/bin/env python3
"""
One-shot transformer: Withings + Beurer historical exports -> Apple Health XML.

Output XML is consumed by OpenVitals (codeberg.org/OpenVitals/android-app),
which then writes the records into Android Health Connect.

See vault task:
  Vault/PERSO/smartwatch-dataviz/tasks/open/2026-06-14-withings-beurer-health-connect-backfill.md

Usage:
  python3 withings-beurer-to-apple-health.py \\
    --withings-dir ~/Downloads/20260614_withings-data \\
    --beurer-csv ~/Downloads/HealthManagerPro_Export_20251022_20260614.csv \\
    --output ~/Downloads/withings-beurer-export.xml \\
    --date-from 2026-06-01 --date-to 2026-06-07

Categories handled:
  Withings (from extracted dir):
    aggregates_steps.csv             -> StepCount (one record/day)
    aggregates_distance.csv          -> DistanceWalkingRunning (m -> km)
    aggregates_elevation.csv         -> ElevationAscended (m)
    aggregates_calories_earned.csv   -> ActiveEnergyBurned (kcal)
    aggregates_calories_passive.csv  -> BasalEnergyBurned (kcal)
    manual_spo2.csv                  -> OxygenSaturation (per measurement)
    raw_spo2_auto_spo2.csv           -> OxygenSaturation (per ScanWatch sample)
    weight.csv                       -> BodyMass (+ optional body composition)
    height.csv                       -> Height (m -> cm)
    sleep.csv                        -> SleepAnalysis (per stage segment)
    activities.csv                   -> Workout (typed activities)
    raw_hr_hr.csv                    -> HeartRate (downsampled per --hr-downsample-minutes)
  Beurer:
    HealthManagerPro CSV             -> BodyMass + BodyFatPercentage
                                        + LeanBodyMass (from muscle %)
                                        + BodyWaterMass (from water %)
                                        + BoneMass (kg)

Skipped (out of scope, see task file rationale):
  - HRV files (SDNN/RMSSD mismatch in OpenVitals)
  - ECG (no HKType mapping)
  - aggregates_manual_spo2.csv (SUM not avg per README, garbage for HC)
  - raw_bed_* / raw_tracker_* / raw_apnea_* / raw_location_* / raw_swim_*
    (specialized internal streams, no clean HKType target)
  - bp.csv (visible entries are HR-only; no real BP cuff data)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape, quoteattr
from zoneinfo import ZoneInfo


# ---------- Constants ----------

# Beurer CSV records local clock times without TZ info; Sweden timezone covers DST.
BEURER_TZ = ZoneInfo("Europe/Stockholm")

# Apple Health HK type identifiers (subset we actually use)
HK = {
    "steps": "HKQuantityTypeIdentifierStepCount",
    "distance": "HKQuantityTypeIdentifierDistanceWalkingRunning",
    "elevation": "HKQuantityTypeIdentifierElevationAscended",
    "active_energy": "HKQuantityTypeIdentifierActiveEnergyBurned",
    "basal_energy": "HKQuantityTypeIdentifierBasalEnergyBurned",
    "weight": "HKQuantityTypeIdentifierBodyMass",
    "body_fat_pct": "HKQuantityTypeIdentifierBodyFatPercentage",
    "lean_mass": "HKQuantityTypeIdentifierLeanBodyMass",
    "bone_mass": "HKQuantityTypeIdentifierBoneMass",
    "water_mass": "HKQuantityTypeIdentifierBodyWaterMass",
    "height": "HKQuantityTypeIdentifierHeight",
    "heart_rate": "HKQuantityTypeIdentifierHeartRate",
    "resting_hr": "HKQuantityTypeIdentifierRestingHeartRate",
    "spo2": "HKQuantityTypeIdentifierOxygenSaturation",
    "sleep": "HKCategoryTypeIdentifierSleepAnalysis",
}

SLEEP_STAGE = {
    "light": "HKCategoryValueSleepAnalysisAsleepCore",
    "deep":  "HKCategoryValueSleepAnalysisAsleepDeep",
    "rem":   "HKCategoryValueSleepAnalysisAsleepREM",
    "awake": "HKCategoryValueSleepAnalysisAwake",
}

# Withings "Activity type" -> Apple workoutActivityType. Keys lowercased on lookup.
# Default fallback: HKWorkoutActivityTypeOther.
WORKOUT_TYPE_MAP = {
    "running":          "HKWorkoutActivityTypeRunning",
    "walking":          "HKWorkoutActivityTypeWalking",
    "cycling":          "HKWorkoutActivityTypeCycling",
    "swimming":         "HKWorkoutActivityTypeSwimming",
    "yoga":             "HKWorkoutActivityTypeYoga",
    "weights":          "HKWorkoutActivityTypeFunctionalStrengthTraining",
    "weight training":  "HKWorkoutActivityTypeFunctionalStrengthTraining",
    "hiit":             "HKWorkoutActivityTypeHighIntensityIntervalTraining",
    "hiking":           "HKWorkoutActivityTypeHiking",
    "multi sport":      "HKWorkoutActivityTypeCrossTraining",
    "rowing":           "HKWorkoutActivityTypeRowing",
    "elliptical":       "HKWorkoutActivityTypeElliptical",
    "dance":            "HKWorkoutActivityTypeDance",
    "tennis":           "HKWorkoutActivityTypeTennis",
    "basketball":       "HKWorkoutActivityTypeBasketball",
    "soccer":           "HKWorkoutActivityTypeSoccer",
    "stairs":           "HKWorkoutActivityTypeStairClimbing",
    "gym class":        "HKWorkoutActivityTypeMixedCardio",  # 328 entries — generic structured class, default to MixedCardio; override per session if known
    "climbing":         "HKWorkoutActivityTypeClimbing",
    "horse riding":     "HKWorkoutActivityTypeEquestrianSports",
    "other":            "HKWorkoutActivityTypeOther",        # Withings's own "Other" — pass through
}

DEFAULT_SOURCE = "Withings/Beurer Backfill"


# ---------- Helpers ----------

def fmt_dt(dt: datetime) -> str:
    """Apple Health date format: 'YYYY-MM-DD HH:MM:SS +HHMM'. Note: no colon in offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Python's %z yields '+0200' (no colon) which is exactly what Apple expects.
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def in_range(d: date, start: date | None, end: date | None) -> bool:
    if start is not None and d < start:
        return False
    if end is not None and d > end:
        return False
    return True


def parse_iso_z(s: str) -> datetime | None:
    """Parse Withings ISO timestamps like '2026-06-13T10:39:46+02:00'."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_quoted_local_dt(s: str) -> datetime | None:
    """Parse '"2025-10-24 08:24:18"' as naive then assume Beurer TZ."""
    if not s:
        return None
    s = s.strip().strip('"')
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=BEURER_TZ)
    except ValueError:
        return None


def parse_beurer_dt(date_str: str, time_str: str) -> datetime | None:
    """Beurer: 'DD/MM/YYYY' + 'HH:MM' in Sweden local time."""
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        return dt.replace(tzinfo=BEURER_TZ)
    except ValueError:
        return None


def write_record(out, hk_type: str, source: str, start: datetime, end: datetime,
                 unit: str | None, value: str) -> None:
    """Emit a <Record> element. value should be pre-formatted as string."""
    attrs = [
        f'type={quoteattr(hk_type)}',
        f'sourceName={quoteattr(source)}',
        f'startDate={quoteattr(fmt_dt(start))}',
        f'endDate={quoteattr(fmt_dt(end))}',
    ]
    if unit is not None:
        attrs.append(f'unit={quoteattr(unit)}')
    attrs.append(f'value={quoteattr(value)}')
    out.write("    <Record " + " ".join(attrs) + " />\n")


def write_category_record(out, hk_type: str, source: str, start: datetime, end: datetime,
                          category_value: str) -> None:
    attrs = [
        f'type={quoteattr(hk_type)}',
        f'sourceName={quoteattr(source)}',
        f'startDate={quoteattr(fmt_dt(start))}',
        f'endDate={quoteattr(fmt_dt(end))}',
        f'value={quoteattr(category_value)}',
    ]
    out.write("    <Record " + " ".join(attrs) + " />\n")


def write_workout(out, activity_type: str, source: str, start: datetime, end: datetime,
                  duration_min: float) -> None:
    attrs = [
        f'workoutActivityType={quoteattr(activity_type)}',
        f'sourceName={quoteattr(source)}',
        f'startDate={quoteattr(fmt_dt(start))}',
        f'endDate={quoteattr(fmt_dt(end))}',
        f'duration={quoteattr(f"{duration_min:.2f}")}',
        f'durationUnit={quoteattr("min")}',
    ]
    out.write("    <Workout " + " ".join(attrs) + " />\n")


# ---------- Emitters per category ----------

def emit_daily_aggregate(path: Path, out, hk_type: str, unit: str,
                         start_d: date | None, end_d: date | None,
                         source: str, value_xform=lambda v: v) -> int:
    """Withings aggregates_*.csv format: 'date,value' with date as YYYY-MM-DD.
    Emits one record per day spanning the local-time day (midnight to midnight Sweden TZ)."""
    if not path.is_file():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_s = row.get("date", "").strip()
            val_s = row.get("value", "").strip()
            if not date_s or not val_s:
                continue
            try:
                d = date.fromisoformat(date_s)
            except ValueError:
                continue
            if not in_range(d, start_d, end_d):
                continue
            try:
                v = float(val_s)
            except ValueError:
                continue
            v = value_xform(v)
            # Day boundaries in local TZ
            start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=BEURER_TZ)
            end = start + timedelta(days=1) - timedelta(seconds=1)
            # Skip records with zero value (no activity that day) — they pollute the import
            if v <= 0:
                continue
            # Format value: integers as int strings, floats with reasonable precision
            if isinstance(v, float) and v == int(v):
                vs = str(int(v))
            elif isinstance(v, float):
                vs = f"{v:.3f}".rstrip("0").rstrip(".")
            else:
                vs = str(v)
            write_record(out, hk_type, source, start, end, unit, vs)
            n += 1
    return n


def emit_height(path: Path, out, start_d: date | None, end_d: date | None,
                source: str) -> int:
    """height.csv: 'Date,"Height (m)",Comments' with date as '"YYYY-MM-DD HH:MM:SS"'.
    Emits in cm (Apple unit)."""
    if not path.is_file():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_quoted_local_dt(row.get("Date", ""))
            if not dt or not in_range(dt.date(), start_d, end_d):
                continue
            h_m_s = row.get("Height (m)", "").strip()
            if not h_m_s:
                continue
            try:
                h_cm = float(h_m_s) * 100.0
            except ValueError:
                continue
            write_record(out, HK["height"], source, dt, dt, "cm", f"{h_cm:.1f}")
            n += 1
    return n


def emit_withings_weight(path: Path, out, start_d: date | None, end_d: date | None,
                         source: str) -> int:
    """weight.csv: Date, Weight (kg), Fat mass (kg), Bone mass (kg), Muscle mass (kg), Hydration (kg), Comments
    Body composition fields are often blank — only emit when present."""
    if not path.is_file():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_quoted_local_dt(row.get("Date", ""))
            if not dt or not in_range(dt.date(), start_d, end_d):
                continue
            def num(key):
                v = row.get(key, "").strip()
                if not v:
                    return None
                try:
                    return float(v)
                except ValueError:
                    return None
            w = num("Weight (kg)")
            if w:
                write_record(out, HK["weight"], source, dt, dt, "kg", f"{w:.2f}")
                n += 1
            fat = num("Fat mass (kg)")
            if fat and w:
                # Apple wants BodyFatPercentage as fraction-of-1 (e.g. 0.225 = 22.5%) per fixture (value="22.5", unit="%")
                # The fixture uses unit="%" with value "22.5" — so it's already a percent.
                pct = (fat / w) * 100.0
                write_record(out, HK["body_fat_pct"], source, dt, dt, "%", f"{pct:.2f}")
                n += 1
            bone = num("Bone mass (kg)")
            if bone:
                write_record(out, HK["bone_mass"], source, dt, dt, "kg", f"{bone:.2f}")
                n += 1
            muscle = num("Muscle mass (kg)")
            if muscle:
                write_record(out, HK["lean_mass"], source, dt, dt, "kg", f"{muscle:.2f}")
                n += 1
            water = num("Hydration (kg)")
            if water:
                write_record(out, HK["water_mass"], source, dt, dt, "kg", f"{water:.2f}")
                n += 1
    return n


def emit_beurer(path: Path, out, start_d: date | None, end_d: date | None,
                source: str) -> int:
    """Beurer HealthManagerPro CSV: multi-section file, weight table has header
    'Date;Time;kg;BMI;Body fat;Water;Muscles;Bone' with values as kg / kg/m2 / % / % / % / kg."""
    if not path.is_file():
        return 0
    n = 0
    in_weight_table = False
    headers = None
    with path.open(newline="", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip():
                in_weight_table = False
                headers = None
                continue
            # Header detection: first column is "Date" and separator is ';'
            if not in_weight_table:
                if line.startswith("Date;"):
                    headers = [h.strip() for h in line.split(";")]
                    in_weight_table = True
                    continue
                else:
                    continue
            # Data row inside the weight table
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < len(headers):
                continue
            row = dict(zip(headers, parts))
            dt = parse_beurer_dt(row.get("Date", ""), row.get("Time", ""))
            if not dt or not in_range(dt.date(), start_d, end_d):
                continue
            def num(key):
                v = row.get(key, "").strip()
                if not v:
                    return None
                try:
                    return float(v.replace(",", "."))
                except ValueError:
                    return None
            w = num("kg")
            if not w:
                continue
            write_record(out, HK["weight"], source, dt, dt, "kg", f"{w:.2f}")
            n += 1
            fat_pct = num("Body fat")
            if fat_pct is not None:
                write_record(out, HK["body_fat_pct"], source, dt, dt, "%", f"{fat_pct:.2f}")
                n += 1
            water_pct = num("Water")
            if water_pct is not None:
                water_kg = w * water_pct / 100.0
                write_record(out, HK["water_mass"], source, dt, dt, "kg", f"{water_kg:.2f}")
                n += 1
            muscle_pct = num("Muscles")
            if muscle_pct is not None:
                muscle_kg = w * muscle_pct / 100.0
                write_record(out, HK["lean_mass"], source, dt, dt, "kg", f"{muscle_kg:.2f}")
                n += 1
            bone_kg = num("Bone")
            if bone_kg is not None:
                write_record(out, HK["bone_mass"], source, dt, dt, "kg", f"{bone_kg:.2f}")
                n += 1
    return n


def emit_spo2_manual(path: Path, out, start_d: date | None, end_d: date | None,
                     source: str) -> int:
    """manual_spo2.csv: per-measurement SpO2 with quoted datetime."""
    if not path.is_file():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_quoted_local_dt(row.get("date", ""))
            if not dt or not in_range(dt.date(), start_d, end_d):
                continue
            try:
                v = float(row.get("value", "").strip())
            except ValueError:
                continue
            # Apple SpO2 is a fraction-of-1 in HC but Apple Health export uses % units per fixture
            write_record(out, HK["spo2"], source, dt, dt, "%", f"{v:.1f}")
            n += 1
    return n


def _parse_array(s: str) -> list[float]:
    """Parse a Withings array cell like '[60,65,70]' or '[1500]'."""
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        try:
            return [float(x) for x in inner.split(",")]
        except ValueError:
            return []
    # Fallback: single value
    try:
        return [float(s)]
    except ValueError:
        return []


def emit_spo2_auto(path: Path, out, start_d: date | None, end_d: date | None,
                   source: str) -> int:
    """raw_spo2_auto_spo2.csv: start, duration (array of seconds), value (array of % readings)."""
    if not path.is_file():
        return 0
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t0 = parse_iso_z(row.get("start", ""))
            if not t0 or not in_range(t0.date(), start_d, end_d):
                continue
            durs = _parse_array(row.get("duration", ""))
            vals = _parse_array(row.get("value", ""))
            cursor = t0
            for i, v in enumerate(vals):
                dur_s = durs[i] if i < len(durs) else 60
                start = cursor
                end = cursor + timedelta(seconds=dur_s)
                write_record(out, HK["spo2"], source, start, end, "%", f"{v:.1f}")
                cursor = end
                n += 1
    return n


def emit_sleep(path: Path, out, start_d: date | None, end_d: date | None,
               source: str) -> tuple[int, int]:
    """sleep.csv: per-session record with stage durations (seconds) and HR stats.
    Emits per-stage SleepAnalysis records abutting from `from` (light, deep, rem, awake);
    OpenVitals will collapse consecutive records into one SleepSession.
    Also emits resting HR record from session min if available.
    Returns (sleep_record_count, hr_record_count)."""
    if not path.is_file():
        return (0, 0)
    n_sleep = 0
    n_hr = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_from = parse_iso_z(row.get("from", ""))
            t_to = parse_iso_z(row.get("to", ""))
            if not t_from or not t_to:
                continue
            # Filter by session start date OR end date (catch sessions that span midnight)
            if not (in_range(t_from.date(), start_d, end_d) or in_range(t_to.date(), start_d, end_d)):
                continue
            def secs(key):
                v = row.get(key, "").strip()
                if not v:
                    return 0
                try:
                    return int(float(v))
                except ValueError:
                    return 0
            light_s = secs("light (s)")
            deep_s  = secs("deep (s)")
            rem_s   = secs("rem (s)")
            awake_s = secs("awake (s)")
            stages = [
                ("light", light_s),
                ("deep",  deep_s),
                ("rem",   rem_s),
                ("awake", awake_s),
            ]
            total_stages = sum(s for _, s in stages)
            session_s = (t_to - t_from).total_seconds()
            if total_stages <= 0 or session_s <= 0:
                continue
            # Emit each non-zero stage starting at t_from, abutting
            cursor = t_from
            for stage_name, stage_s in stages:
                if stage_s <= 0:
                    continue
                start = cursor
                end = cursor + timedelta(seconds=stage_s)
                # Don't run past t_to (defensive)
                if end > t_to:
                    end = t_to
                write_category_record(out, HK["sleep"], source, start, end,
                                      SLEEP_STAGE[stage_name])
                n_sleep += 1
                cursor = end
                if cursor >= t_to:
                    break
            # Emit RestingHeartRate from session min HR if reasonable
            try:
                min_hr = float(row.get("Heart rate (min)", "").strip() or 0)
            except ValueError:
                min_hr = 0
            if 30 <= min_hr <= 120:
                write_record(out, HK["resting_hr"], source, t_from, t_from,
                             "count/min", f"{int(min_hr)}")
                n_hr += 1
    return (n_sleep, n_hr)


def emit_activities(path: Path, out, start_d: date | None, end_d: date | None,
                    source: str, min_workout_minutes: float) -> tuple[int, int, int]:
    """activities.csv: Withings activities with JSON 'Data' blob (hr, distance, calories, etc).
    Two-pass: load all → dedup → filter → emit.

    Dedup rule: if multiple activities share identical (from, to) timestamps AND
    one is "Multi Sport", drop the Multi Sport (Withings' generic catchall that
    duplicates the typed entry). Otherwise keep all.

    Filter: drop workouts with duration <= min_workout_minutes (Withings auto-
    detects micro-activities like "walked 2 min" which pollute HC workout history).

    Emits Workout records ONLY (no embedded distance/active_energy — those would
    double-count against the daily aggregates which already include workout-time
    movement).

    Returns (emitted_count, dropped_duplicates, dropped_short)."""
    if not path.is_file():
        return (0, 0, 0)
    # Pass 1: load all rows in date range, with parsed timestamps + type
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_from = parse_iso_z(row.get("from", ""))
            t_to = parse_iso_z(row.get("to", ""))
            if not t_from or not t_to:
                continue
            if not (in_range(t_from.date(), start_d, end_d) or in_range(t_to.date(), start_d, end_d)):
                continue
            duration_s = (t_to - t_from).total_seconds()
            if duration_s <= 0 or duration_s >= 86400:
                continue
            atype_raw = (row.get("Activity type", "") or "").strip()
            rows.append({"from": t_from, "to": t_to, "duration_s": duration_s, "atype": atype_raw})

    # Pass 2: dedup by (from, to) — drop Multi Sport if a typed activity shares same window
    by_key: dict[tuple, list[dict]] = {}
    for r in rows:
        key = (r["from"], r["to"])
        by_key.setdefault(key, []).append(r)
    dedup_dropped = 0
    kept: list[dict] = []
    for key, group in by_key.items():
        if len(group) > 1:
            typed = [r for r in group if r["atype"].lower() != "multi sport"]
            if typed:
                # Keep typed, drop Multi Sport (and any other dups beyond the first typed)
                kept.append(typed[0])
                dedup_dropped += len(group) - 1
            else:
                # All Multi Sport (or all same type) — keep first, drop rest
                kept.append(group[0])
                dedup_dropped += len(group) - 1
        else:
            kept.append(group[0])

    # Pass 3: apply min-duration filter, emit
    short_dropped = 0
    n_emitted = 0
    # Emit in chronological order for readability
    kept.sort(key=lambda r: r["from"])
    for r in kept:
        duration_min = r["duration_s"] / 60.0
        if duration_min <= min_workout_minutes:
            short_dropped += 1
            continue
        atype_lower = r["atype"].lower()
        wk_type = WORKOUT_TYPE_MAP.get(atype_lower, "HKWorkoutActivityTypeOther")
        write_workout(out, wk_type, source, r["from"], r["to"], duration_min)
        n_emitted += 1
    return (n_emitted, dedup_dropped, short_dropped)


def emit_heart_rate(path: Path, out, start_d: date | None, end_d: date | None,
                    source: str, bucket_minutes: int) -> int:
    """raw_hr_hr.csv: start (ISO with TZ), duration [array seconds], value [array bpm].
    Bucket samples into bucket_minutes windows, emit one averaged record per bucket.
    bucket_minutes == 0 means no downsampling (emit every sample as-is)."""
    if not path.is_file():
        return 0
    if bucket_minutes < 0:
        bucket_minutes = 0
    # Buckets: key = (bucket_start_utc_epoch, bucket_minutes). Value = [sum, count, tz_offset_seconds].
    # tz_offset preserves the user's local offset for the first sample landing in the bucket.
    buckets: dict[int, list] = {}
    samples_seen = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t0 = parse_iso_z(row.get("start", ""))
            if not t0:
                continue
            if not in_range(t0.date(), start_d, end_d):
                continue
            durs = _parse_array(row.get("duration", ""))
            vals = _parse_array(row.get("value", ""))
            cursor = t0
            for i, v in enumerate(vals):
                if v <= 0 or v > 250:  # sanity filter on bpm
                    continue
                dur_s = durs[i] if i < len(durs) else 60
                samples_seen += 1
                if bucket_minutes == 0:
                    # Emit immediately, no downsampling
                    start = cursor
                    end = cursor + timedelta(seconds=dur_s)
                    write_record(out, HK["heart_rate"], source, start, end,
                                 "count/min", f"{int(round(v))}")
                else:
                    # Bucket by floor-to-N-minutes of UTC epoch
                    epoch = int(cursor.timestamp())
                    bucket_size = bucket_minutes * 60
                    bucket_start_epoch = epoch - (epoch % bucket_size)
                    if bucket_start_epoch not in buckets:
                        # Preserve TZ offset of first sample for this bucket
                        offset_s = int(cursor.utcoffset().total_seconds()) if cursor.utcoffset() else 0
                        buckets[bucket_start_epoch] = [0.0, 0, offset_s]
                    buckets[bucket_start_epoch][0] += v
                    buckets[bucket_start_epoch][1] += 1
                cursor = cursor + timedelta(seconds=dur_s)
    if bucket_minutes == 0:
        return samples_seen
    # Emit one record per bucket
    n = 0
    bucket_size = bucket_minutes * 60
    for bucket_start_epoch in sorted(buckets):
        total, count, offset_s = buckets[bucket_start_epoch]
        avg = total / count
        tz = timezone(timedelta(seconds=offset_s))
        start = datetime.fromtimestamp(bucket_start_epoch, tz=tz)
        end = start + timedelta(seconds=bucket_size)
        write_record(out, HK["heart_rate"], source, start, end,
                     "count/min", f"{int(round(avg))}")
        n += 1
    return n


# ---------- main ----------

def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--withings-dir", type=Path, required=True,
                   help="Path to extracted Withings export directory.")
    p.add_argument("--beurer-csv", type=Path, default=None,
                   help="Path to Beurer HealthManagerPro CSV (optional).")
    p.add_argument("--output", type=Path, required=True,
                   help="Output Apple Health XML file path.")
    p.add_argument("--date-from", type=str, default=None,
                   help="Inclusive YYYY-MM-DD (defaults to no lower bound).")
    p.add_argument("--date-to", type=str, default=None,
                   help="Inclusive YYYY-MM-DD (defaults to no upper bound).")
    p.add_argument("--hr-downsample-minutes", type=int, default=10,
                   help="HR averaging window in minutes (0 = full fidelity, default 10).")
    p.add_argument("--min-workout-minutes", type=float, default=5.0,
                   help="Drop workouts with duration <= this many minutes (default 5).")
    p.add_argument("--source-name", type=str, default=DEFAULT_SOURCE,
                   help="sourceName attribute on emitted records.")
    args = p.parse_args()

    start_d = date.fromisoformat(args.date_from) if args.date_from else None
    end_d = date.fromisoformat(args.date_to) if args.date_to else None
    wd = args.withings_dir
    if not wd.is_dir():
        print(f"ERROR: --withings-dir not found or not a directory: {wd}", file=sys.stderr)
        sys.exit(2)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    stats = {}
    with args.output.open("w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<HealthData locale="en_US">\n')

        # Withings daily aggregates
        stats["steps"]            = emit_daily_aggregate(wd / "aggregates_steps.csv", out, HK["steps"], "count", start_d, end_d, args.source_name)
        stats["distance"]         = emit_daily_aggregate(wd / "aggregates_distance.csv", out, HK["distance"], "km", start_d, end_d, args.source_name, value_xform=lambda v: v / 1000.0)
        stats["elevation"]        = emit_daily_aggregate(wd / "aggregates_elevation.csv", out, HK["elevation"], "m", start_d, end_d, args.source_name)
        stats["active_energy"]    = emit_daily_aggregate(wd / "aggregates_calories_earned.csv", out, HK["active_energy"], "kcal", start_d, end_d, args.source_name)
        stats["basal_energy"]     = emit_daily_aggregate(wd / "aggregates_calories_passive.csv", out, HK["basal_energy"], "kcal", start_d, end_d, args.source_name)

        # Withings height
        stats["height"]           = emit_height(wd / "height.csv", out, start_d, end_d, args.source_name)

        # Withings weight (sparse)
        stats["withings_weight"]  = emit_withings_weight(wd / "weight.csv", out, start_d, end_d, "Withings " + args.source_name)

        # Beurer weight + composition
        if args.beurer_csv and args.beurer_csv.is_file():
            stats["beurer_records"] = emit_beurer(args.beurer_csv, out, start_d, end_d, "Beurer " + args.source_name)
        else:
            stats["beurer_records"] = 0

        # SpO2 — manual + ScanWatch auto samples
        stats["spo2_manual"]      = emit_spo2_manual(wd / "manual_spo2.csv", out, start_d, end_d, args.source_name)
        stats["spo2_auto"]        = emit_spo2_auto(wd / "raw_spo2_auto_spo2.csv", out, start_d, end_d, args.source_name)

        # Sleep — per-stage records + resting HR per session
        sleep_n, sleep_hr_n = emit_sleep(wd / "sleep.csv", out, start_d, end_d, args.source_name)
        stats["sleep_stages"]     = sleep_n
        stats["sleep_resting_hr"] = sleep_hr_n

        # Activities — Workout records ONLY (no embedded distance/active_energy
        # to avoid double-counting against the daily aggregates above)
        wk_n, dup_dropped, short_dropped = emit_activities(
            wd / "activities.csv", out, start_d, end_d, args.source_name,
            args.min_workout_minutes,
        )
        stats["workouts"]              = wk_n
        stats["_dropped_duplicates"]   = dup_dropped
        stats["_dropped_short"]        = short_dropped

        # Heart rate — bulk file, downsampled
        stats["heart_rate"]       = emit_heart_rate(wd / "raw_hr_hr.csv", out, start_d, end_d, args.source_name, args.hr_downsample_minutes)

        out.write('</HealthData>\n')

    emitted_keys = [k for k in stats if not k.startswith("_")]
    dropped_keys = [k for k in stats if k.startswith("_")]
    total = sum(stats[k] for k in emitted_keys)
    print(f"\nWritten: {args.output}")
    print(f"Date range: {args.date_from or '(none)'} → {args.date_to or '(none)'}")
    print(f"HR downsample: {args.hr_downsample_minutes} min" + ("  (full fidelity)" if args.hr_downsample_minutes == 0 else ""))
    print(f"Min workout duration: {args.min_workout_minutes} min")
    print(f"\nRecord counts (emitted):")
    width = max(len(k) for k in stats) if stats else 0
    for k in sorted(emitted_keys):
        v = stats[k]
        bar = "▍" * min(v // 100, 60) if v > 0 else ""
        print(f"  {k.ljust(width)}  {v:>7}  {bar}")
    print(f"  {'TOTAL'.ljust(width)}  {total:>7}")
    if dropped_keys:
        print(f"\nDropped (not emitted):")
        for k in sorted(dropped_keys):
            print(f"  {k.lstrip('_').ljust(width)}  {stats[k]:>7}")
    try:
        size = args.output.stat().st_size
        print(f"\nFile size: {size / 1024:.1f} KB" if size < 1024 * 1024 else f"\nFile size: {size / 1024 / 1024:.1f} MB")
    except OSError:
        pass


if __name__ == "__main__":
    main()
