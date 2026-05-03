#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 car-type 目錄內「機動車輛新車領牌數」CSV 提取並清洗資料。
依 doc/data_collect.txt：燃料三類（ICE/BEV/Hybrid）、車種篩選。

**僅保留月度列**（例：113年 3月）；排除整年列、115年 (1~3月) 等累計列。
來源檔預設為 big5 編碼。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

CSV_ENCODING = "big5"
DEFAULT_INPUT = "車輛類型11303_11503.csv"
COLS_PER_BLOCK = 42
VEHICLE_BLOCKS = [
    "總計",
    "汽車",
    "大客車",
    "大貨車",
    "小客車",
    "小貨車",
    "特種車",
    "機車",
]

ICE_FUELS = {"汽油", "柴油", "液化石油氣", "汽油/LPG"}
BEV_FUELS = {"電能"}
HYBRID_FUELS = {
    "汽油/電能",
    "柴油/電能",
    "電能/汽油",
    "電能/柴油",
    "電能(增程)",
    "汽油(油電)",
    "柴油(油電)",
    "汽油(電能)",
}

SKIP_VEHICLES = {"總計", "汽車", "特種車"}
KEEP_VEHICLES = {"大客車", "大貨車", "小客車", "小貨車", "機車"}

CIVILIAN = {"小客車", "機車"}
COMMERCIAL = {"大客車", "大貨車", "小貨車"}

REGIONS = ("總計", "新北市", "臺北市")


def categorize_fuel(fuel: str) -> str | None:
    if fuel in ("總計",):
        return None
    if fuel in ICE_FUELS:
        return "ICE"
    if fuel in BEV_FUELS:
        return "BEV"
    if fuel in HYBRID_FUELS:
        return "Hybrid"
    raise ValueError(f"未知燃料欄位: {fuel!r}")


def parse_int_cell(raw: str) -> int:
    if raw is None:
        return 0
    s = str(raw).strip()
    if s in ("", "-", "—", "–"):
        return 0
    return int(s.replace(",", ""))


def parse_period(period: str) -> tuple[str, str | None, str]:
    """回傳 (sort_key, granularity, 原始統計期)。月度：granularity == 'monthly'。"""
    s = period.strip()
    if not s or s.startswith("說明") or s.startswith("　　"):
        return "", None, s

    if re.match(r"^(\d+)年\s*\(\d+~\d+月\)", s):
        return "", None, s

    m_m = re.match(r"^(\d+)年\s*(\d+)月", s)
    if m_m:
        y, mo = m_m.group(1), m_m.group(2)
        return f"{y}-{mo.zfill(2)}", "monthly", s

    if re.match(r"^(\d+)年$", s):
        return "", None, s

    return "", None, s


def build_column_map(header_row: list[str]) -> list[dict]:
    if len(header_row) < 1 + COLS_PER_BLOCK * len(VEHICLE_BLOCKS):
        raise ValueError("表頭欄位數與預期不符")

    mapping: list[dict] = []
    for bi, vtype in enumerate(VEHICLE_BLOCKS):
        base = 1 + bi * COLS_PER_BLOCK
        for off in range(COLS_PER_BLOCK):
            col = base + off
            label = header_row[col].strip() if col < len(header_row) else ""
            if not label:
                continue
            parts = label.split("_", 1)
            if len(parts) != 2:
                continue
            fuel, region_suffix = parts[0], parts[1]
            if region_suffix not in REGIONS:
                continue
            mapping.append(
                {
                    "col": col,
                    "vehicle": vtype,
                    "fuel": fuel,
                    "region_key": region_suffix,
                }
            )
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="清洗 car-type 新領牌 CSV，僅輸出月度資料。")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help=f"輸入 CSV 路徑（預設: 腳本同目錄之 {DEFAULT_INPUT}）",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="輸出目錄（預設: car-type/output）",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    src = args.input if args.input else root / DEFAULT_INPUT
    out_dir = args.output_dir if args.output_dir else root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.is_file():
        raise SystemExit(f"找不到來源檔: {src}")

    with src.open("r", encoding=CSV_ENCODING, newline="") as f:
        rows = list(csv.reader(f))

    header_sub = rows[3]
    col_map = build_column_map(header_sub)

    agg: dict[tuple, int] = defaultdict(int)

    for row in rows[4:]:
        if not row or not row[0].strip():
            continue
        period_raw = row[0].strip()
        if period_raw.startswith("說明") or period_raw.startswith("　　"):
            break

        sort_key, gran, _ = parse_period(period_raw)
        if not sort_key or gran != "monthly":
            continue

        for spec in col_map:
            if spec["vehicle"] in SKIP_VEHICLES:
                continue
            if spec["vehicle"] not in KEEP_VEHICLES:
                continue

            cat = categorize_fuel(spec["fuel"])
            if cat is None:
                continue

            col = spec["col"]
            val = parse_int_cell(row[col] if col < len(row) else "")
            if val == 0:
                continue

            v = spec["vehicle"]
            group = "civilian" if v in CIVILIAN else "commercial" if v in COMMERCIAL else "other"
            region = spec["region_key"]
            key = (sort_key, period_raw, group, v, region, cat)
            agg[key] += val

    long_path = out_dir / "vehicle_registrations_monthly_long.csv"
    with long_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "period_sort",
                "period_label",
                "vehicle_group",
                "vehicle_type",
                "region",
                "fuel_category",
                "count",
            ]
        )
        for key in sorted(agg.keys(), key=lambda k: (k[0], k[1], k[2], k[3], k[4], k[5])):
            sort_key, period_raw, group, v, region, cat = key
            w.writerow([sort_key, period_raw, group, v, region, cat, agg[key]])

    monthly_rows: list[dict] = []
    for key, cnt in agg.items():
        sort_key, period_raw, group, v, region, cat = key
        if region not in ("臺北市", "新北市"):
            continue
        monthly_rows.append(
            {
                "period_sort": sort_key,
                "period_label": period_raw,
                "vehicle_group": group,
                "vehicle_type": v,
                "district_scope": region,
                "fuel_category": cat,
                "count": cnt,
            }
        )

    pivot: dict[tuple, dict[str, int]] = defaultdict(lambda: {"ICE": 0, "BEV": 0, "Hybrid": 0})
    for r in monthly_rows:
        t = (
            r["period_sort"],
            r["period_label"],
            r["vehicle_group"],
            r["vehicle_type"],
            r["district_scope"],
        )
        pivot[t][r["fuel_category"]] += r["count"]

    dash_path = out_dir / "vehicle_monthly_dashboard.json"
    dashboard: list[dict] = []
    for t in sorted(pivot.keys(), key=lambda x: x[0]):
        fuels = pivot[t]
        sort_key, label, group, vtype, district = t
        ice, bev, hyb = fuels["ICE"], fuels["BEV"], fuels["Hybrid"]
        total = ice + bev + hyb
        bev_ratio = round(100.0 * bev / total, 2) if total else 0.0
        ice_ratio = round(100.0 * ice / total, 2) if total else 0.0
        hybrid_ratio = round(100.0 * hyb / total, 2) if total else 0.0
        dashboard.append(
            {
                "period_sort": sort_key,
                "period_label": label,
                "vehicle_group": group,
                "vehicle_type": vtype,
                "district_scope": district,
                "total_by_fuel_categories": total,
                "ice": ice,
                "bev": bev,
                "hybrid": hyb,
                "bev_ratio_pct": bev_ratio,
                "ice_ratio_pct": ice_ratio,
                "hybrid_ratio_pct": hybrid_ratio,
            }
        )

    dash_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")

    timeline_path = out_dir / "vehicle_monthly_timeline_stack.json"
    timeline = build_timeline_stack(agg)
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    fe_components = build_fe_components(agg, scope="臺北市") + build_fe_components(
        agg, scope="雙北"
    )
    fe_components_path = out_dir / "vehicle_components.json"
    fe_components_path.write_text(
        json.dumps(fe_components, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    seed_dir = out_dir / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)

    data_sql_path = seed_dir / "01_dashboard_data.sql"
    data_sql_path.write_text(build_dashboard_data_sql(agg), encoding="utf-8")

    manager_sql_path = seed_dir / "02_dashboardmanager_components.sql"
    manager_sql_path.write_text(build_dashboardmanager_sql(), encoding="utf-8")

    sql_path = out_dir / "vehicle_components_sql_template.sql"
    sql_path.write_text(build_sql_template(), encoding="utf-8")

    summary_path = out_dir / "clean_summary.txt"
    summary_path.write_text(
        "\n".join(
            [
                f"來源: {src.name}",
                "編碼: big5",
                "時間粒度: 僅月度（已排除整年與 (1~3月) 等列）",
                "",
                "已套用 data_collect.txt:",
                "- 燃料: ICE / BEV / Hybrid",
                "- 車種: 大客車、大貨車、小客車、小貨車、機車（排除全體總計、汽車匯總、特種車）",
                "",
                f"- {long_path.name}（長表，含 總計/新北市/臺北市 區域）",
                f"- {dash_path.name}（臺北市+新北市，含占比）",
                f"- {timeline_path.name}（doc 之 timeline_fuel_stack 結構，依 scope+vehicle_type）",
                f"- {fe_components_path.name}（FE 六筆：臺北市+雙北 各三組件 chart_data，key=`index`+`city`）",
                f"- {sql_path.name}（後端 dashboardmanager 三表 SQL 樣板）",
                f"- seed/{data_sql_path.name}（dashboard DB 資料表 + 全部月度資料）",
                f"- seed/{manager_sql_path.name}（dashboardmanager 三組件、儀表板、群組）",
                f"- 長表鍵數: {len(agg)}",
                f"- dashboard 筆數: {len(dashboard)}",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote {long_path}")
    print(f"Wrote {dash_path}")
    print(f"Wrote {timeline_path}")
    print(f"Wrote {fe_components_path}")
    print(f"Wrote {sql_path}")
    print(f"Wrote {data_sql_path}")
    print(f"Wrote {manager_sql_path}")
    print(f"Wrote {summary_path}")


def build_timeline_stack(
    agg: dict[tuple, int],
) -> list[dict]:
    """每月 x 軸、ICE/BEV/Hybrid 三序列；每個 (scope, vehicle_type) 一筆 chart 物件。"""
    nested: dict[tuple, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"ICE": 0, "BEV": 0, "Hybrid": 0})
    )
    for key, cnt in agg.items():
        sort_key, _period_raw, _group, vtype, region, cat = key
        if region not in ("臺北市", "新北市"):
            continue
        nested[(region, vtype)][sort_key][cat] += cnt

    charts: list[dict] = []
    for (scope, vtype) in sorted(nested.keys(), key=lambda x: (x[0], x[1])):
        by_month = nested[(scope, vtype)]
        x_sorted = sorted(by_month.keys())
        ice_v = [by_month[m]["ICE"] for m in x_sorted]
        bev_v = [by_month[m]["BEV"] for m in x_sorted]
        hyb_v = [by_month[m]["Hybrid"] for m in x_sorted]
        x_labels = [f"{m.split('-')[0]}年{int(m.split('-')[1])}月" for m in x_sorted]
        charts.append(
            {
                "chart": "timeline_fuel_stack",
                "meta": {
                    "scope": scope,
                    "vehicle_type": vtype,
                    "unit": "輛",
                    "stack_mode": "absolute",
                },
                "x": x_sorted,
                "x_labels": x_labels,
                "series": [
                    {"key": "ICE", "label": "純油", "values": ice_v},
                    {"key": "BEV", "label": "純電", "values": bev_v},
                    {"key": "Hybrid", "label": "油電／混合", "values": hyb_v},
                ],
            }
        )
    return charts


FE_VEHICLE_TYPE_ORDER = ("小客車", "機車", "小貨車", "大貨車", "大客車")
FE_FUEL_ORDER = ("ICE", "BEV", "Hybrid")
FE_FUEL_LABELS = {"ICE": "純油 (ICE)", "BEV": "純電 (BEV)", "Hybrid": "油電/混合 (Hybrid)"}
FE_FUEL_COLORS = {
    "ICE": "#9b6b3e",
    "BEV": "#4cb495",
    "Hybrid": "#f5c860",
}

# 對應 component_doc/spec.md 中的圖表類型英文名（PascalCase）
FE_BAR_PALETTE = ["#4cb495", "#56b96d", "#9ac17c", "#f5c860", "#e58a4f"]
FE_DONUT_PALETTE = ["#9b6b3e", "#4cb495", "#f5c860", "#848c94"]


def _period_to_iso(period_sort: str) -> str:
    """Convert ROC sort key like '113-04' to ISO month start with +08:00."""
    y_roc, mo = period_sort.split("-")
    iso_year = int(y_roc) + 1911
    return f"{iso_year:04d}-{int(mo):02d}-01T00:00:00+08:00"


METRO_SCOPE_REGIONS = ("臺北市", "新北市")


def _latest_period(agg: dict[tuple, int], scope: str) -> str | None:
    if scope == "雙北":
        keys = {k[0] for k in agg.keys() if k[4] in METRO_SCOPE_REGIONS}
    else:
        keys = {k[0] for k in agg.keys() if k[4] == scope}
    return max(keys) if keys else None


def _latest_period_label(agg: dict[tuple, int], scope: str, latest: str) -> str:
    for k in agg.keys():
        if k[0] != latest:
            continue
        if scope == "雙北":
            if k[4] in METRO_SCOPE_REGIONS:
                return k[1]
        elif k[4] == scope:
            return k[1]
    return latest


def build_fe_components(agg: dict[tuple, int], scope: str = "臺北市") -> list[dict]:
    """產生 3 個前端 DashboardComponent 物件：BarChart / DonutChart / TimelineStackedChart。

    完全對齊 component_doc/spec.md 與 Taipei-City-Dashboard-Documentation 中
    `chart-data.md` 之 two_d / time 格式。
    """
    latest = _latest_period(agg, scope)
    if latest is None:
        return []
    latest_label = _latest_period_label(agg, scope, latest)

    by_vtype_fuel: dict[str, dict[str, int]] = {
        v: {"ICE": 0, "BEV": 0, "Hybrid": 0} for v in FE_VEHICLE_TYPE_ORDER
    }
    by_fuel: dict[str, int] = {f: 0 for f in FE_FUEL_ORDER}
    by_month_fuel: dict[str, dict[str, int]] = defaultdict(
        lambda: {"ICE": 0, "BEV": 0, "Hybrid": 0}
    )

    for (period_sort, _label, _grp, vtype, region, cat), cnt in agg.items():
        if scope == "雙北":
            if region not in METRO_SCOPE_REGIONS:
                continue
        elif region != scope:
            continue
        by_month_fuel[period_sort][cat] += cnt
        if period_sort == latest:
            if vtype in by_vtype_fuel:
                by_vtype_fuel[vtype][cat] += cnt
            by_fuel[cat] += cnt

    months_sorted = sorted(by_month_fuel.keys())
    series_time = []
    for cat in FE_FUEL_ORDER:
        series_time.append(
            {
                "name": FE_FUEL_LABELS[cat],
                "data": [
                    {"x": _period_to_iso(m), "y": by_month_fuel[m][cat]}
                    for m in months_sorted
                ],
            }
        )

    city_val = (
        "metrotaipei"
        if scope == "雙北"
        else ("taipei" if scope == "臺北市" else "newtaipei")
    )
    common_meta = {
        "source": "交通部統計查詢網（機動車輛新車領牌數）",
        "contributors": (["doit", "ntpc"] if scope == "雙北" else ["doit"]),
        "links": (
            [
                "https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100",
                "https://data.ntpc.gov.tw/",
            ]
            if scope == "雙北"
            else ["https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100"]
        ),
        "city": city_val,
        "tags": ["車輛", "綠能", "ICE/BEV/Hybrid"],
    }

    # three_d format: categories = vehicle types, series = fuel categories
    column_chart_data = []
    for cat in FE_FUEL_ORDER:
        column_chart_data.append({
            "name": FE_FUEL_LABELS[cat],
            "data": [by_vtype_fuel[v][cat] for v in FE_VEHICLE_TYPE_ORDER],
        })

    bar_component = {
        "id": 901,
        "index": "vehicle_type_count_taipei",
        "name": "新領牌車輛 - 各車種輛數",
        "history_data": False,
        "map_config": None,
        "map_filter": None,
        "history_config": None,
        "query_type": "three_d",
        "chart_config": {
            "color": [FE_FUEL_COLORS[f] for f in FE_FUEL_ORDER],
            "types": ["ColumnChart"],
            "unit": "輛",
            "categories": FE_VEHICLE_TYPE_ORDER,
        },
        "chart_data": column_chart_data,
        "time_from": "static",
        "time_to": None,
        "update_freq": 1,
        "update_freq_unit": "month",
        "short_desc": f"{scope} {latest_label} 新領牌車輛各車種燃料類別輛數。",
        "long_desc": (
            f"以 {scope} {latest_label} 為例，呈現各車種（小客車、機車、小貨車、大客車、大貨車）"
            "的 ICE / BEV / Hybrid 新領牌輛數，以堆疊縱向長條圖呈現。"
        ),
        "use_case": "比較各車種油電比例，輔助綠能轉型評估。",
        **common_meta,
    }

    donut_component = {
        "id": 902,
        "index": "vehicle_fuel_mix_taipei",
        "name": "新領牌車輛 - 燃料類別占比",
        "history_data": False,
        "map_config": None,
        "map_filter": None,
        "history_config": None,
        "query_type": "two_d",
        "chart_config": {
            "color": FE_DONUT_PALETTE,
            "types": ["DonutChart", "BarChart"],
            "unit": "輛",
        },
        "chart_data": [
            {
                "name": "",
                "data": [
                    {"x": FE_FUEL_LABELS[f], "y": by_fuel[f]} for f in FE_FUEL_ORDER
                ],
            }
        ],
        "time_from": "static",
        "time_to": None,
        "update_freq": 1,
        "update_freq_unit": "month",
        "short_desc": f"{scope} {latest_label} 新領牌車輛 ICE/BEV/Hybrid 占比。",
        "long_desc": (
            "ICE：(1)汽油、(2)柴油、(4)液化石油氣、(5)汽油/LPG；"
            "BEV：(3)電能；Hybrid：(6)~(13) 其餘混合與雙動力分類。"
            f"以 {scope} {latest_label} 為例。"
        ),
        "use_case": "觀察油轉電進度，作為綠色城市核心指標。",
        **common_meta,
    }

    trend_component = {
        "id": 903,
        "index": "vehicle_fuel_trend_taipei",
        "name": "新領牌車輛 - 燃料類別月趨勢",
        "history_data": False,
        "map_config": None,
        "map_filter": None,
        "history_config": None,
        "query_type": "time",
        "chart_config": {
            "color": [FE_FUEL_COLORS[f] for f in FE_FUEL_ORDER],
            "types": ["TimelineStackedChart"],
            "unit": "輛",
        },
        "chart_data": series_time,
        "time_from": "static",
        "time_to": None,
        "update_freq": 1,
        "update_freq_unit": "month",
        "short_desc": f"{scope} 新領牌車輛 ICE/BEV/Hybrid 之月趨勢。",
        "long_desc": (
            f"{scope} 新領牌車輛依燃料三類匯總後逐月堆疊。月度資料；已排除整年列、"
            "(1~3月) 等累計列。"
        ),
        "use_case": "觀察雙北油轉電的月度趨勢與季節性變化。",
        **common_meta,
    }

    return [bar_component, donut_component, trend_component]


def build_sql_template() -> str:
    """產生後端 dashboardmanager 三張表（components / query_charts / component_charts）的 SQL 樣板。

    搭配 Taipei-City-Dashboard-Documentation 中的 components-db.md 與
    component-data-apis.md。`query_chart` 假設後端會把清洗後的長表
    （vehicle_registrations_monthly_long.csv）載入 `dashboard.vehicle_registration_monthly`。
    """
    return """-- ==========================================================
-- car-type: 機動車輛新車領牌（月度）三張靜態圖表元件 SQL 樣板
-- 對齊 Taipei-City-Dashboard-Documentation/back-end-ch/components-db.md
-- 假設長表已 import 為 public.vehicle_registration_monthly：
--   period_sort TEXT  -- e.g. '114-06'
--   period_label TEXT -- e.g. '114年 6月'
--   vehicle_group TEXT
--   vehicle_type TEXT
--   region TEXT       -- '臺北市' / '新北市' / '總計'
--   fuel_category TEXT -- 'ICE' / 'BEV' / 'Hybrid'
--   count INT
-- ==========================================================

-- 1. components（主表）
INSERT INTO dashboardmanager.components (index, name) VALUES
  ('vehicle_type_count_taipei',   '新領牌車輛 - 各車種輛數'),
  ('vehicle_fuel_mix_taipei',     '新領牌車輛 - 燃料類別占比'),
  ('vehicle_fuel_trend_taipei',   '新領牌車輛 - 燃料類別月趨勢');

-- 2. component_charts（顏色、圖表類型、單位）
INSERT INTO dashboardmanager.component_charts (index, color, types, unit) VALUES
  ('vehicle_type_count_taipei',
    ARRAY['#4cb495','#56b96d','#9ac17c','#f5c860','#e58a4f'],
    ARRAY['BarChart'],
    '輛'),
  ('vehicle_fuel_mix_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '輛'),
  ('vehicle_fuel_trend_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['TimelineStackedChart'],
    '輛');

-- 3. query_charts（查詢設定 + SQL）
-- 3-1 vehicle_type_count_taipei: query_type=two_d
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_type_count_taipei','two_d','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT vehicle_type AS x_axis, SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region = '臺北市')
GROUP BY vehicle_type
ORDER BY data DESC
$$
);

-- 3-2 vehicle_fuel_mix_taipei: query_type=two_d
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_fuel_mix_taipei','two_d','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS x_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region = '臺北市')
GROUP BY fuel_category
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)
$$
);

-- 3-3 vehicle_fuel_trend_taipei: query_type=time
-- 注意：圖表 SQL 可以有 0 或 2 個 %s 占位符。靜態資料不需要時間範圍。
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_fuel_trend_taipei','time','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT
  to_timestamp(
    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text
    || '-' || split_part(period_sort, '-', 2) || '-01',
    'YYYY-MM-DD'
  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
GROUP BY x_axis, fuel_category
ORDER BY y_axis, x_axis
$$
);
"""


# ----- Seed SQL builders（直接可灌入 PostgreSQL 的最小可用集） -----

# 三組件、儀表板、群組對照之固定 ID（避開現有 demo SQL 之 1, 2, 60, 100~218, 355~359）
SEED_COMPONENT_IDS = {
    "vehicle_type_count_taipei": 901,
    "vehicle_fuel_mix_taipei": 902,
    "vehicle_fuel_trend_taipei": 903,
}
# ── car-type 僅管理自己的 components / query_charts ──────────────────────────
# dashboard 已由 component_doc/seed/03_sustainable_env_dashboard.sql 統一管理：
#   905 sustainable_env_taipei      → group 2 (taipei)
#   906 sustainable_env_metrotaipei → group 3 (metrotaipei)
# 以下常數保留供 build_dashboardmanager_sql 參考，但 02_*.sql 不再插 dashboards 表。
SEED_DASHBOARD_ID = 905
SEED_DASHBOARD_INDEX = "sustainable_env_taipei"
SEED_DASHBOARD_NAME = "永續環境"
SEED_DASHBOARD_ICON = "eco"
SEED_TAIPEI_GROUP_ID = 2

SEED_METROTAIPEI_DASHBOARD_ID = 906
SEED_METROTAIPEI_DASHBOARD_INDEX = "sustainable_env_metrotaipei"
SEED_METROTAIPEI_GROUP_ID = 3


def _sql_escape(s: str) -> str:
    return s.replace("'", "''")


def build_dashboard_data_sql(agg: dict[tuple, int]) -> str:
    """產生 `dashboard` DB 用的 CREATE TABLE + INSERT，灌入清洗後月度長表。"""
    rows: list[str] = []
    for key in sorted(agg.keys(), key=lambda k: (k[0], k[1], k[2], k[3], k[4], k[5])):
        period_sort, period_label, group, vtype, region, cat = key
        rows.append(
            "  ('{ps}', '{pl}', '{g}', '{v}', '{r}', '{c}', {n})".format(
                ps=_sql_escape(period_sort),
                pl=_sql_escape(period_label),
                g=_sql_escape(group),
                v=_sql_escape(vtype),
                r=_sql_escape(region),
                c=_sql_escape(cat),
                n=agg[key],
            )
        )

    body = ",\n".join(rows)
    return f"""-- ===========================================================================
-- car-type / 01_dashboard_data.sql
-- 目標 DB: dashboard（資料庫）
-- 依 components-db.md：DB: dashboard → create table {{index}} (import csv data)
-- 統一使用 vehicle_registration_monthly 為三組件共用之資料表。
-- 已套用 doc/data_collect.txt：燃料三類、車種篩選、僅月度。
-- ===========================================================================

DROP TABLE IF EXISTS public.vehicle_registration_monthly;

CREATE TABLE public.vehicle_registration_monthly (
    period_sort   text   NOT NULL,
    period_label  text   NOT NULL,
    vehicle_group text   NOT NULL,
    vehicle_type  text   NOT NULL,
    region        text   NOT NULL,
    fuel_category text   NOT NULL,
    "count"       integer NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vrm_period
  ON public.vehicle_registration_monthly (period_sort);
CREATE INDEX IF NOT EXISTS idx_vrm_region_fuel
  ON public.vehicle_registration_monthly (region, fuel_category);

INSERT INTO public.vehicle_registration_monthly
  (period_sort, period_label, vehicle_group, vehicle_type, region, fuel_category, "count")
VALUES
{body};
"""


def build_dashboardmanager_sql() -> str:
    """產生 `dashboardmanager` DB 用之 components / component_charts / query_charts /
    dashboards / dashboard_groups INSERT。
    可冪等執行（先 DELETE 再 INSERT）。"""
    bar_id = SEED_COMPONENT_IDS["vehicle_type_count_taipei"]
    donut_id = SEED_COMPONENT_IDS["vehicle_fuel_mix_taipei"]
    trend_id = SEED_COMPONENT_IDS["vehicle_fuel_trend_taipei"]

    bar_sql_tpe = """SELECT
  v.vehicle_type AS x_axis,
  CASE f.fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  COALESCE(SUM(m.count), 0) AS data
FROM
  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)
  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)
  LEFT JOIN public.vehicle_registration_monthly m
    ON  m.vehicle_type  = v.vehicle_type
    AND m.fuel_category = f.fuel_category
    AND m.region        = '臺北市'
    AND m.period_sort   = (SELECT MAX(period_sort)
                           FROM public.vehicle_registration_monthly
                           WHERE region = '臺北市')
GROUP BY v.vehicle_type, f.fuel_category
ORDER BY
  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),
  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)"""

    bar_sql_metro = """SELECT
  v.vehicle_type AS x_axis,
  CASE f.fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  COALESCE(SUM(m.count), 0) AS data
FROM
  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)
  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)
  LEFT JOIN public.vehicle_registration_monthly m
    ON  m.vehicle_type  = v.vehicle_type
    AND m.fuel_category = f.fuel_category
    AND m.region IN ('臺北市', '新北市')
    AND m.period_sort   = (SELECT MAX(period_sort)
                           FROM public.vehicle_registration_monthly
                           WHERE region IN ('臺北市', '新北市'))
GROUP BY v.vehicle_type, f.fuel_category
ORDER BY
  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),
  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)"""

    donut_sql_tpe = """SELECT
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS x_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region = '臺北市')
GROUP BY fuel_category
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)"""

    donut_sql_metro = """SELECT
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS x_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region IN ('臺北市', '新北市')
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region IN ('臺北市', '新北市'))
GROUP BY fuel_category
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)"""

    trend_sql_tpe = """SELECT
  to_timestamp(
    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text
    || '-' || split_part(period_sort, '-', 2) || '-01',
    'YYYY-MM-DD'
  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
GROUP BY x_axis, fuel_category
ORDER BY y_axis, x_axis"""

    trend_sql_metro = """SELECT
  to_timestamp(
    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text
    || '-' || split_part(period_sort, '-', 2) || '-01',
    'YYYY-MM-DD'
  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region IN ('臺北市', '新北市')
GROUP BY x_axis, fuel_category
ORDER BY y_axis, x_axis"""

    indices_in = (
        "('vehicle_type_count_taipei','vehicle_fuel_mix_taipei','vehicle_fuel_trend_taipei')"
    )
    ids_in = f"({bar_id}, {donut_id}, {trend_id})"

    return f"""-- ===========================================================================
-- car-type / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
-- 說明：僅管理 components / component_charts / query_charts（不含 dashboards）。
--   ⚠️ 儀表板（永續環境 sustainable_env_taipei/metrotaipei）由
--       component_doc/seed/03_sustainable_env_dashboard.sql 統一管理。
--
-- 雙北 query_charts 作法：
--   * components.id（{bar_id}/{donut_id}/{trend_id}）共用
--   * query_charts 每個 index 各 city='taipei' / 'metrotaipei' 一筆
-- ===========================================================================

-- 0. 移除既有相同 index/id 的舊紀錄，使本檔案可重複執行
DELETE FROM public.query_charts
 WHERE index IN {indices_in};
DELETE FROM public.component_charts
 WHERE index IN {indices_in};
DELETE FROM public.components
 WHERE index IN {indices_in}
    OR id IN {ids_in};

-- 1. components（主表）
INSERT INTO public.components (id, index, name) VALUES
  ({bar_id},   'vehicle_type_count_taipei', '新領牌車輛 - 各車種輛數'),
  ({donut_id}, 'vehicle_fuel_mix_taipei',   '新領牌車輛 - 燃料類別占比'),
  ({trend_id}, 'vehicle_fuel_trend_taipei', '新領牌車輛 - 燃料類別月趨勢');

-- 2. component_charts（顏色 / 圖表類型 / 單位）
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('vehicle_type_count_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['ColumnChart'],
    '輛'),
  ('vehicle_fuel_mix_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '輛'),
  ('vehicle_fuel_trend_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['TimelineStackedChart'],
    '輛');

-- 3. query_charts（查詢設定 + SQL 指令；每 index 兩筆 city）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES
(
  'vehicle_type_count_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛各車種輛數（最新月份）。',
  '以最新月份為例，呈現大客車、大貨車、小客車、小貨車、機車五個保留車種的新領牌輛數。已排除全體總計、汽車匯總列、特種車。',
  '比較各車種登記輛數，輔助綠能轉型／污染源評估。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $${bar_sql_tpe}$$,
  NULL,
  'taipei'
),
(
  'vehicle_type_count_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛各車種輛數（最新月份，臺北+新北合計）。',
  '以雙北共同最新月份為例，將臺北市與新北市同車種、同燃料之新領牌輛數加總後呈現。',
  '比較各車種登記輛數，輔助大臺北綠能轉型／污染源評估。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'three_d',
  $${bar_sql_metro}$$,
  NULL,
  'metrotaipei'
),
(
  'vehicle_fuel_mix_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛 ICE/BEV/Hybrid 占比（最新月份）。',
  'ICE：(1)汽油、(2)柴油、(4)液化石油氣、(5)汽油/LPG；BEV：(3)電能；Hybrid：(6)~(13) 其餘混合與雙動力分類。以最新月份為例。',
  '觀察油轉電進度，作為綠色城市核心指標。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $${donut_sql_tpe}$$,
  NULL,
  'taipei'
),
(
  'vehicle_fuel_mix_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛 ICE/BEV/Hybrid 占比（最新月份，臺北+新北合計）。',
  '將雙北同月份輛數加總後，再依燃料三類計算占比。',
  '觀察大臺北油轉電進度。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $${donut_sql_metro}$$,
  NULL,
  'metrotaipei'
),
(
  'vehicle_fuel_trend_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛 ICE/BEV/Hybrid 之月趨勢。',
  '依燃料三類匯總後逐月堆疊。月度資料；已排除整年列、(1~3月) 等累計列。',
  '觀察臺北市油轉電的月度趨勢與季節性變化。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'time',
  $${trend_sql_tpe}$$,
  NULL,
  'taipei'
),
(
  'vehicle_fuel_trend_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛 ICE/BEV/Hybrid 之月趨勢（臺北+新北合計）。',
  '同月份兩市輛數加總後逐月堆疊。',
  '觀察雙北油轉電的月度趨勢與季節性變化。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'time',
  $${trend_sql_metro}$$,
  NULL,
  'metrotaipei'
);

-- ⚠️ dashboards / dashboard_groups 已移至：
--    component_doc/seed/03_sustainable_env_dashboard.sql
-- 請在此檔執行後，另行執行該檔以建立「永續環境」儀表板。
"""


if __name__ == "__main__":
    main()
