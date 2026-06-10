"""
One-shot patch: redistribute monthly+ DAG schedules.

Rules:
- Each monthly+ DAG runs TWICE every month: first week + last week.
- Each DAG offset 30 min from others.
- All DAGs land in Taipei off-peak: 20:00-06:00 (UTC 12:00-21:59), single band.
- @once is skipped.
- Month field always `*` — quarterly/yearly are promoted to every-month execution.
"""
import csv
import json
import re
from pathlib import Path

DAGS_ROOT = Path(__file__).resolve().parents[2] / "Taipei-City-Dashboard-DE" / "dags"
REPORT = Path(__file__).resolve().parents[1] / "output" / "schedule_redistribution.csv"

# Taipei 20:00-06:00 next day = UTC 12:00-21:59 (10 hours)
HOURS = list(range(12, 22))
# Day offsets within first week / last week (1+offset, 22+offset)
DAY_OFFSETS = list(range(0, 7))  # 0..6 → first_dom 1..7, last_dom 22..28


def is_monthly_more(s):
    if not isinstance(s, str):
        return None, None
    s = s.strip()
    if s == "@once":
        return None, None
    if s == "@monthly":
        return True, "*"
    if s == "@quarterly":
        return True, "1,4,7,10"
    if s in {"@yearly", "@annually"}:
        return True, "1"
    if s.startswith("@"):
        return False, None
    fields = s.split()
    if len(fields) != 5:
        return False, None
    _, _, dom, month, _ = fields
    if dom == "*" and month == "*":
        return False, None
    return True, month


def is_heavy(data_infos):
    if data_infos.get("is_geometry") in (1, "1", True):
        return True
    src = (data_infos.get("source_type") or "").lower()
    return any(x in src for x in ["zip", "shp", "shapefile"])


def assign_slot(idx, hours, day_offsets):
    """Slot index → (minute, hour, day_offset). Order: minute < hour < day."""
    slots_per_hour = 2
    slots_per_day = slots_per_hour * len(hours)
    day_offset = day_offsets[idx // slots_per_day]
    rem = idx % slots_per_day
    hour = hours[rem // slots_per_hour]
    minute = (rem % slots_per_hour) * 30
    return minute, hour, day_offset


def describe_cron_zh(cron):
    """Convert post-redistribution cron `MM HH D1,D2 * *` to Chinese description."""
    minute, hour, doms, _, _ = cron.split()
    tpe_hour = (int(hour) + 8) % 24
    cross_day = (int(hour) + 8) >= 24
    time_str = f"Taipei {tpe_hour:02d}:{int(minute):02d}"
    if cross_day:
        time_str += "(隔日)"
    days = "、".join(f"{d}號" for d in doms.split(","))
    return f"每月 {days} {time_str} 執行"


def build_cron(minute, hour, day_offset, months=None):
    first_dom = 1 + day_offset
    last_dom = 22 + day_offset
    return f"{minute} {hour} {first_dom},{last_dom} * *"


def main():
    candidates = []
    for cfg_path in sorted(DAGS_ROOT.rglob("job_config.json")):
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {cfg_path}: {e}")
            continue
        di = cfg.get("dag_infos", {})
        data = cfg.get("data_infos", {})
        sch = di.get("schedule_interval", "")
        flag, months = is_monthly_more(sch)
        if flag is None:
            continue  # @once
        if not flag:
            continue
        candidates.append({
            "path": cfg_path,
            "cfg": cfg,
            "dag_id": di.get("dag_id"),
            "old": sch,
            "months": months,
            "heavy": is_heavy(data),
        })

    # Heavy first (deeper night), then light. Within each group sort by proj/dag_id.
    candidates.sort(key=lambda c: (
        0 if c["heavy"] else 1,
        c["path"].parent.parent.name,
        c["dag_id"],
    ))

    capacity = len(HOURS) * 2 * len(DAY_OFFSETS)
    if len(candidates) > capacity:
        raise RuntimeError(f"Slot overflow: {len(candidates)} > {capacity}")

    for i, c in enumerate(candidates):
        minute, hour, doff = assign_slot(i, HOURS, DAY_OFFSETS)
        c["new"] = build_cron(minute, hour, doff, c["months"])
        c["band"] = "heavy" if c["heavy"] else "light"

    pattern = re.compile(r'("schedule_interval"\s*:\s*")([^"]*)(")')
    rows = []
    for c in candidates:
        text = c["path"].read_text(encoding="utf-8")
        m = pattern.search(text)
        if not m or m.group(2) != c["old"]:
            raise RuntimeError(f"schedule_interval not found or mismatch in {c['path']}")
        new_text = text[:m.start(2)] + c["new"] + text[m.end(2):]
        cfg_check = json.loads(new_text)
        assert cfg_check["dag_infos"]["schedule_interval"] == c["new"]
        c["path"].write_text(new_text, encoding="utf-8")
        rel = c["path"].relative_to(DAGS_ROOT.parent.parent)
        rows.append({
            "proj": c["path"].parent.parent.name,
            "dag_id": c["dag_id"],
            "band": c["band"],
            "old_schedule": c["old"],
            "new_schedule": c["new"],
            "執行時間說明": describe_cron_zh(c["new"]),
            "config_path": str(rel),
        })

    rows.sort(key=lambda r: (r["new_schedule"], r["dag_id"]))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    heavy_n = sum(1 for c in candidates if c["heavy"])
    print(f"Heavy: {heavy_n}, Light: {len(candidates)-heavy_n}, Total: {len(rows)}")
    print(f"Capacity: {capacity}, Used: {len(candidates)}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
