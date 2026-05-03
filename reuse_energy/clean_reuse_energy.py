#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 reuse_energy 目錄內「再生能源裝置容量」CSV 提取並清洗資料。

來源欄位：年別, 縣市, 風力（瓩）, 太陽光電（瓩）, 其他(含水力)（瓩）
- 年別：民國年（101–114）為「年度資料」；115年02月以 11502 表示「最新月度快照」。
- 縣市：台北市 / 新北市
- 三種再生能源：風力、太陽光電、其他(含水力)，單位「瓩 (kW)」

對應到 component_doc/spec.md 的圖表（與 car-type 同模式）：
- ColumnChart        三維（city × energy_type，最新期堆疊長條）
- ColumnChart        三維（年度 × energy_type，臺北市逐年堆疊長條）
- DonutChart         二維（台北市最新期三能源占比）
- TimelineStackedChart  時間（台北市逐年三能源堆疊）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

CSV_ENCODING = "utf-8-sig"
DEFAULT_INPUT = "再生能源-台北.csv"

ENERGY_TYPES = ("風力", "太陽光電", "其他(含水力)")
SOURCE_COL_MAP = {
    "風力": "風力（瓩）",
    "太陽光電": "太陽光電（瓩）",
    "其他(含水力)": "其他(含水力)（瓩）",
}

CITY_KEYS = {"台北市", "新北市"}

FE_ENERGY_LABELS = {
    "風力": "風力",
    "太陽光電": "太陽光電",
    "其他(含水力)": "其他 (含水力)",
}
FE_ENERGY_COLORS = {
    "風力": "#4cb495",
    "太陽光電": "#f5c860",
    "其他(含水力)": "#5b8def",
}
FE_CITY_LABELS = {"台北市": "臺北市", "新北市": "新北市"}

# ID 區段：避開 car-type 使用的 901–903
SEED_COMPONENT_IDS = {
    "reuse_energy_capacity_metrotaipei": 911,
    "reuse_energy_mix_taipei": 912,
    "reuse_energy_trend_taipei": 913,
    "reuse_energy_trend_column_taipei": 914,
}
SEED_DASHBOARD_ID = 902
SEED_DASHBOARD_INDEX = "renewable_energy_taipei"
SEED_DASHBOARD_NAME = "再生能源"
SEED_DASHBOARD_ICON = "solar_power"
SEED_TAIPEI_GROUP_ID = 2  # demo SQL: groups.id=2, name='taipei'

# 雙北儀表板（與 ltc_care_newtpe / ltc_care_tpe 同模式：components.id 共用、
# query_charts (index, city) 各插一筆，dashboard 掛 group_id=3 'metrotaipei'）
SEED_METROTAIPEI_DASHBOARD_ID = 903
SEED_METROTAIPEI_DASHBOARD_INDEX = "renewable_energy_metrotaipei"
SEED_METROTAIPEI_DASHBOARD_NAME = "再生能源"
SEED_METROTAIPEI_GROUP_ID = 3  # demo SQL: groups.id=3, name='metrotaipei'


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_year_cell(raw: str) -> tuple[str, str, str] | None:
    """回傳 (period_sort, period_label, iso_date)。

    - "101" → ("101-00", "101年", "2012-01-01T00:00:00+08:00")    # 年度
    - "11502" → ("115-02", "115年 2月", "2026-02-01T00:00:00+08:00")  # 月度
    """
    s = str(raw).strip()
    if not s:
        return None
    if re.fullmatch(r"\d{3}", s):  # 101 ~ 114
        roc = int(s)
        return f"{roc:03d}-00", f"{roc}年", f"{roc + 1911:04d}-01-01T00:00:00+08:00"
    m = re.fullmatch(r"(\d{3})(\d{2})", s)  # 11502
    if m:
        roc = int(m.group(1))
        mo = int(m.group(2))
        return (
            f"{roc:03d}-{mo:02d}",
            f"{roc}年 {mo}月",
            f"{roc + 1911:04d}-{mo:02d}-01T00:00:00+08:00",
        )
    return None


def parse_int_cell(raw: str) -> int:
    if raw is None:
        return 0
    s = str(raw).strip()
    if s in ("", "-", "—", "–"):
        return 0
    return int(float(s.replace(",", "")))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="清洗 reuse_energy CSV，產生 FE 組件 + 後端 seed SQL。"
    )
    parser.add_argument("-i", "--input", type=Path, default=None,
                        help=f"輸入 CSV 路徑（預設: 同目錄 {DEFAULT_INPUT}）")
    parser.add_argument("-o", "--output-dir", type=Path, default=None,
                        help="輸出目錄（預設: reuse_energy/output）")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    src = args.input if args.input else root / DEFAULT_INPUT
    out_dir = args.output_dir if args.output_dir else root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_dir = out_dir / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)

    if not src.is_file():
        raise SystemExit(f"找不到來源檔: {src}")

    rows: list[dict] = []
    with src.open("r", encoding=CSV_ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            year_info = parse_year_cell(r.get("年別", ""))
            if year_info is None:
                continue
            period_sort, period_label, iso_date = year_info
            city = (r.get("縣市") or "").strip()
            if city not in CITY_KEYS:
                continue
            for etype, col in SOURCE_COL_MAP.items():
                rows.append({
                    "period_sort": period_sort,
                    "period_label": period_label,
                    "iso_date": iso_date,
                    "city": city,
                    "energy_type": etype,
                    "capacity_kw": parse_int_cell(r.get(col, "")),
                })

    if not rows:
        raise SystemExit("解析後沒有任何資料；請確認 CSV 編碼/欄位是否正確。")

    long_path = out_dir / "reuse_energy_long.csv"
    with long_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period_sort", "period_label", "iso_date",
                    "city", "energy_type", "capacity_kw"])
        for r in sorted(rows, key=lambda x: (x["period_sort"], x["city"], x["energy_type"])):
            w.writerow([r["period_sort"], r["period_label"], r["iso_date"],
                        r["city"], r["energy_type"], r["capacity_kw"]])

    fe_components = build_fe_components(rows)
    fe_path = out_dir / "reuse_energy_components.json"
    fe_path.write_text(json.dumps(fe_components, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    sql_template_path = out_dir / "reuse_energy_components_sql_template.sql"
    sql_template_path.write_text(build_sql_template(), encoding="utf-8")

    data_sql_path = seed_dir / "01_dashboard_data.sql"
    data_sql_path.write_text(build_dashboard_data_sql(rows), encoding="utf-8")

    manager_sql_path = seed_dir / "02_dashboardmanager_components.sql"
    manager_sql_path.write_text(build_dashboardmanager_sql(), encoding="utf-8")

    summary_path = out_dir / "clean_summary.txt"
    summary_path.write_text("\n".join([
        f"來源: {src.name}",
        f"編碼: {CSV_ENCODING}",
        "年別解析: 101–114 視為年度，11502 視為民國 115 年 2 月之最新月度快照。",
        "",
        f"- {long_path.name}（長表，城市 × 年/月 × 能源類型）",
        f"- {fe_path.name}（FE 四組件 chart_data，可直接接 DashboardComponent）",
        f"- {sql_template_path.name}（後端 dashboardmanager 三表 SQL 樣板）",
        f"- seed/{data_sql_path.name}（dashboard DB 資料表 + 全部資料）",
        f"- seed/{manager_sql_path.name}（dashboardmanager 四組件 components/charts/queries；⚠️ 儀表板由 component_doc/seed/03_sustainable_env_dashboard.sql 管理）",
        f"- 總列數: {len(rows)}",
    ]), encoding="utf-8")

    print(f"Wrote {long_path}")
    print(f"Wrote {fe_path}")
    print(f"Wrote {sql_template_path}")
    print(f"Wrote {data_sql_path}")
    print(f"Wrote {manager_sql_path}")
    print(f"Wrote {summary_path}")


# ---------------------------------------------------------------------------
# FE components builder
# ---------------------------------------------------------------------------

def _latest_period(rows: list[dict]) -> str:
    return max(r["period_sort"] for r in rows)


def _latest_label(rows: list[dict], latest: str) -> str:
    for r in rows:
        if r["period_sort"] == latest:
            return r["period_label"]
    return latest


def build_fe_components(rows: list[dict]) -> list[dict]:
    latest = _latest_period(rows)
    latest_label = _latest_label(rows, latest)

    # 1. ColumnChart：x=城市（臺北市/新北市），series=三能源，最新期
    by_city_energy_latest: dict[str, dict[str, int]] = defaultdict(
        lambda: {e: 0 for e in ENERGY_TYPES}
    )
    for r in rows:
        if r["period_sort"] != latest:
            continue
        by_city_energy_latest[r["city"]][r["energy_type"]] += r["capacity_kw"]

    cities_x = ["台北市", "新北市"]
    column_chart_data = [
        {
            "name": FE_ENERGY_LABELS[etype],
            "data": [by_city_energy_latest[c][etype] for c in cities_x],
        }
        for etype in ENERGY_TYPES
    ]

    # 2. DonutChart：台北市最新期三能源占比
    taipei_latest = {e: 0 for e in ENERGY_TYPES}
    for r in rows:
        if r["period_sort"] == latest and r["city"] == "台北市":
            taipei_latest[r["energy_type"]] += r["capacity_kw"]

    donut_chart_data = [{
        "name": "",
        "data": [
            {"x": FE_ENERGY_LABELS[e], "y": taipei_latest[e]}
            for e in ENERGY_TYPES
        ],
    }]

    # 3. TimelineStackedChart：台北市逐年三能源堆疊（僅取年度列 *-00）
    timeline_rows = [r for r in rows
                     if r["city"] == "台北市" and r["period_sort"].endswith("-00")]
    iso_by_period: dict[str, str] = {}
    by_period_energy: dict[str, dict[str, int]] = defaultdict(
        lambda: {e: 0 for e in ENERGY_TYPES}
    )
    for r in timeline_rows:
        iso_by_period[r["period_sort"]] = r["iso_date"]
        by_period_energy[r["period_sort"]][r["energy_type"]] += r["capacity_kw"]

    periods_sorted = sorted(by_period_energy.keys())
    period_label_by_sort: dict[str, str] = {}
    for r in timeline_rows:
        if r["period_sort"] not in period_label_by_sort:
            period_label_by_sort[r["period_sort"]] = r["period_label"]
    year_categories = [period_label_by_sort[p] for p in periods_sorted]

    series_time = []
    for etype in ENERGY_TYPES:
        series_time.append({
            "name": FE_ENERGY_LABELS[etype],
            "data": [
                {"x": iso_by_period[p], "y": by_period_energy[p][etype]}
                for p in periods_sorted
            ],
        })

    # 4. ColumnChart：臺北市逐年三能源堆疊（three_d，X=民國年、與 car-type 縱向長條同格式）
    trend_column_chart_data = [
        {
            "name": FE_ENERGY_LABELS[etype],
            "data": [by_period_energy[p][etype] for p in periods_sorted],
        }
        for etype in ENERGY_TYPES
    ]

    common_meta = {
        "history_data": False,
        "map_config": None,
        "map_filter": None,
        "history_config": None,
        "time_to": None,
        "update_freq": 1,
        "update_freq_unit": "year",
        "source": "經濟部能源署 / 全國電力資源供需報告",
        "contributors": ["doit"],
        "links": ["https://www.moeaea.gov.tw/"],
        "tags": ["再生能源", "綠能", "風光水"],
    }

    column_component = {
        "id": SEED_COMPONENT_IDS["reuse_energy_capacity_metrotaipei"],
        "index": "reuse_energy_capacity_metrotaipei",
        "name": "再生能源裝置容量 - 雙北比較",
        # 不論進入哪個 dashboard 都需呈現雙北比較，因此 query_charts
        # 同時掛 city=taipei 與 city=metrotaipei 兩筆同 SQL。
        "city": "metrotaipei",
        "query_type": "three_d",
        "chart_config": {
            "color": [FE_ENERGY_COLORS[e] for e in ENERGY_TYPES],
            "types": ["ColumnChart"],
            "unit": "瓩 (kW)",
            "categories": [FE_CITY_LABELS[c] for c in cities_x],
        },
        "chart_data": column_chart_data,
        "time_from": "static",
        "short_desc": f"雙北 {latest_label} 再生能源（風力／太陽光電／其他(含水力)）裝置容量。",
        "long_desc": (
            f"以 {latest_label} 為例，並列臺北市與新北市三類再生能源（風力、太陽光電、"
            "其他(含水力)）的裝置容量，以堆疊縱向長條圖呈現。臺北市受地形限制，風力裝置容量為 0。"
        ),
        "use_case": "比較雙北綠能發展結構，輔助再生能源政策評估。",
        **common_meta,
    }

    donut_component = {
        "id": SEED_COMPONENT_IDS["reuse_energy_mix_taipei"],
        "index": "reuse_energy_mix_taipei",
        "name": "再生能源裝置容量 - 能源占比",
        "city": "taipei",
        "query_type": "two_d",
        "chart_config": {
            "color": [FE_ENERGY_COLORS[e] for e in ENERGY_TYPES] + ["#848c94"],
            "types": ["DonutChart", "BarChart"],
            "unit": "瓩 (kW)",
        },
        "chart_data": donut_chart_data,
        "time_from": "static",
        "short_desc": f"臺北市 {latest_label} 三類再生能源裝置容量占比。",
        "long_desc": (
            "風力：陸域與離岸；太陽光電：屋頂型與地面型合計；"
            "其他(含水力)：水力、生質能、地熱等。"
            f"以臺北市 {latest_label} 為例。"
        ),
        "use_case": "觀察臺北市再生能源結構偏向，作為綠色城市核心指標。",
        **common_meta,
    }

    trend_component = {
        "id": SEED_COMPONENT_IDS["reuse_energy_trend_taipei"],
        "index": "reuse_energy_trend_taipei",
        "name": "再生能源裝置容量 - 年趨勢",
        "city": "taipei",
        "query_type": "time",
        "chart_config": {
            "color": [FE_ENERGY_COLORS[e] for e in ENERGY_TYPES],
            "types": ["TimelineStackedChart"],
            "unit": "瓩 (kW)",
        },
        "chart_data": series_time,
        "time_from": "static",
        "short_desc": "臺北市再生能源裝置容量逐年趨勢（風力／太陽光電／其他）。",
        "long_desc": (
            "依民國 101 年起累計裝置容量逐年呈現；以堆疊面積觀察整體成長與結構變化。"
            "11502（115 年 2 月）為最新月度快照，未納入逐年趨勢。"
        ),
        "use_case": "觀察臺北市再生能源裝置容量的成長路徑與結構演進。",
        **common_meta,
    }

    trend_column_component = {
        "id": SEED_COMPONENT_IDS["reuse_energy_trend_column_taipei"],
        "index": "reuse_energy_trend_column_taipei",
        "name": "再生能源裝置容量 - 年趨勢（縱向長條）",
        "city": "taipei",
        "query_type": "three_d",
        "chart_config": {
            "color": [FE_ENERGY_COLORS[e] for e in ENERGY_TYPES],
            "types": ["ColumnChart"],
            "unit": "瓩 (kW)",
            "categories": year_categories,
        },
        "chart_data": trend_column_chart_data,
        "time_from": "static",
        "short_desc": "臺北市再生能源裝置容量逐年堆疊長條（風力／太陽光電／其他）。",
        "long_desc": (
            "與「臺北市年趨勢」折線堆疊圖相同資料來源（僅年度列）；改以縱向堆疊長條呈現，"
            "對齊 Documentation `chart-data.md` 之 three_d + ColumnChart。"
            "11502 未納入。"
        ),
        "use_case": "以長條圖比對各年度裝置容量結構，補足折線堆疊圖之外的視覺化選項。",
        **common_meta,
    }

    return [
        column_component,
        donut_component,
        trend_component,
        trend_column_component,
    ]


# ---------------------------------------------------------------------------
# SQL builders
# ---------------------------------------------------------------------------

def _sql_escape(s: str) -> str:
    return s.replace("'", "''")


def build_dashboard_data_sql(rows: list[dict]) -> str:
    values: list[str] = []
    for r in sorted(rows, key=lambda x: (x["period_sort"], x["city"], x["energy_type"])):
        values.append(
            "  ('{ps}', '{pl}', '{iso}', '{c}', '{e}', {n})".format(
                ps=_sql_escape(r["period_sort"]),
                pl=_sql_escape(r["period_label"]),
                iso=_sql_escape(r["iso_date"]),
                c=_sql_escape(r["city"]),
                e=_sql_escape(r["energy_type"]),
                n=r["capacity_kw"],
            )
        )
    body = ",\n".join(values)
    return f"""-- ===========================================================================
-- reuse_energy / 01_dashboard_data.sql
-- 目標 DB: dashboard
-- 依 components-db.md：DB: dashboard → create table {{index}} (import csv data)
-- 統一使用 reuse_energy_capacity 為各組件共用之資料表。
-- ===========================================================================

DROP TABLE IF EXISTS public.reuse_energy_capacity;

CREATE TABLE public.reuse_energy_capacity (
    period_sort  text   NOT NULL,    -- '101-00' 年度 / '115-02' 月度
    period_label text   NOT NULL,    -- '101年' / '115年 2月'
    iso_date     timestamptz NOT NULL,
    city         text   NOT NULL,    -- '台北市' / '新北市'
    energy_type  text   NOT NULL,    -- '風力' / '太陽光電' / '其他(含水力)'
    capacity_kw  integer NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rec_period
  ON public.reuse_energy_capacity (period_sort);
CREATE INDEX IF NOT EXISTS idx_rec_city_energy
  ON public.reuse_energy_capacity (city, energy_type);

INSERT INTO public.reuse_energy_capacity
  (period_sort, period_label, iso_date, city, energy_type, capacity_kw)
VALUES
{body};
"""


def build_sql_template() -> str:
    return """-- ==========================================================
-- reuse_energy: 再生能源裝置容量 靜態圖表元件 SQL 樣板
-- 對齊 Taipei-City-Dashboard-Documentation/back-end-ch/components-db.md
-- 假設長表已 import 為 public.reuse_energy_capacity：
--   period_sort  TEXT  -- '101-00' 年度 / '115-02' 月度
--   period_label TEXT
--   iso_date     TIMESTAMPTZ
--   city         TEXT  -- '台北市' / '新北市'
--   energy_type  TEXT  -- '風力' / '太陽光電' / '其他(含水力)'
--   capacity_kw  INT
-- ==========================================================

-- 1. components
INSERT INTO dashboardmanager.components (index, name) VALUES
  ('reuse_energy_capacity_metrotaipei', '再生能源裝置容量 - 雙北比較'),
  ('reuse_energy_mix_taipei',           '再生能源裝置容量 - 臺北市能源占比'),
  ('reuse_energy_trend_taipei',         '再生能源裝置容量 - 臺北市年趨勢'),
  ('reuse_energy_trend_column_taipei',  '再生能源裝置容量 - 臺北市年趨勢（縱向長條）');

-- 2. component_charts
INSERT INTO dashboardmanager.component_charts (index, color, types, unit) VALUES
  ('reuse_energy_capacity_metrotaipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)'),
  ('reuse_energy_mix_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['TimelineStackedChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_column_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)');

-- 3. query_charts
-- 3-1 ColumnChart (three_d)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_capacity_metrotaipei','three_d','static',NULL,1,'year','經濟部能源署','metrotaipei',
$$
SELECT
  CASE city WHEN '台北市' THEN '臺北市' ELSE city END AS x_axis,
  energy_type AS y_axis,
  SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY x_axis, energy_type
ORDER BY ARRAY_POSITION(ARRAY['臺北市','新北市'], x_axis),
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)
$$
);

-- 3-2 DonutChart (two_d)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_mix_taipei','two_d','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.reuse_energy_capacity WHERE city = '台北市')
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)
$$
);

-- 3-3 TimelineStackedChart (time)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_trend_taipei','time','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市' AND period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type
$$
);

-- 3-4 ColumnChart 臺北市逐年（three_d；列順序須符合後端 GetThreeDimensionalData 分組）
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_trend_column_taipei','three_d','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT p.period_label AS x_axis,
       e.energy_type AS y_axis,
       COALESCE(m.capacity_kw, 0) AS data
FROM
  (SELECT DISTINCT period_sort, period_label
   FROM public.reuse_energy_capacity
   WHERE city = '台北市' AND period_sort LIKE '%-00'
  ) AS p
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON m.period_sort = p.period_sort
   AND m.city = '台北市'
   AND m.energy_type = e.energy_type
ORDER BY p.period_sort,
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)
$$
);
"""


def build_dashboardmanager_sql() -> str:
    col_id = SEED_COMPONENT_IDS["reuse_energy_capacity_metrotaipei"]
    donut_id = SEED_COMPONENT_IDS["reuse_energy_mix_taipei"]
    trend_id = SEED_COMPONENT_IDS["reuse_energy_trend_taipei"]
    trend_col_id = SEED_COMPONENT_IDS["reuse_energy_trend_column_taipei"]

    # 雙北比較：城市為 X 軸、能源為堆疊系列（city 不論 taipei/metrotaipei 都呈現雙北）
    col_sql = """SELECT
  CASE c.city WHEN '台北市' THEN '臺北市' ELSE c.city END AS x_axis,
  e.energy_type AS y_axis,
  COALESCE(SUM(m.capacity_kw), 0) AS data
FROM
  (VALUES ('台北市'),('新北市')) AS c(city)
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON  m.city        = c.city
    AND m.energy_type = e.energy_type
    AND m.period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY c.city, e.energy_type
ORDER BY
  ARRAY_POSITION(ARRAY['台北市','新北市']::text[], c.city),
  ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)"""

    # ----- 臺北市專用 SQL（city='taipei'）-----
    donut_sql_tpe = """SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.reuse_energy_capacity WHERE city = '台北市')
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)"""

    trend_sql_tpe = """SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市' AND period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type"""

    trend_column_sql_tpe = """SELECT p.period_label AS x_axis,
       e.energy_type AS y_axis,
       COALESCE(m.capacity_kw, 0) AS data
FROM
  (SELECT DISTINCT period_sort, period_label
   FROM public.reuse_energy_capacity
   WHERE city = '台北市' AND period_sort LIKE '%-00'
  ) AS p
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON m.period_sort = p.period_sort
   AND m.city = '台北市'
   AND m.energy_type = e.energy_type
ORDER BY p.period_sort,
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)"""

    # ----- 雙北合計 SQL（city='metrotaipei'）：移除 city 過濾，sum 雙北 -----
    donut_sql_metro = """SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)"""

    trend_sql_metro = """SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type"""

    trend_column_sql_metro = """SELECT p.period_label AS x_axis,
       e.energy_type AS y_axis,
       COALESCE(SUM(m.capacity_kw), 0) AS data
FROM
  (SELECT DISTINCT period_sort, period_label
   FROM public.reuse_energy_capacity
   WHERE period_sort LIKE '%-00'
  ) AS p
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON m.period_sort = p.period_sort
   AND m.energy_type = e.energy_type
GROUP BY p.period_sort, p.period_label, e.energy_type
ORDER BY p.period_sort,
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)"""

    indices_in = (
        "('reuse_energy_capacity_metrotaipei','reuse_energy_mix_taipei',"
        "'reuse_energy_trend_taipei','reuse_energy_trend_column_taipei')"
    )
    ids_in = f"({col_id}, {donut_id}, {trend_id}, {trend_col_id})"

    return f"""-- ===========================================================================
-- reuse_energy / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
-- 說明：僅管理 components / component_charts / query_charts（不含 dashboards）。
--   ⚠️ 儀表板（永續環境 sustainable_env_taipei/metrotaipei）由
--       component_doc/seed/03_sustainable_env_dashboard.sql 統一管理。
--
-- 雙北 query_charts 作法：
--   * components.id（{col_id}/{donut_id}/{trend_id}/{trend_col_id}）共用
--   * query_charts 對每個 index 各插 city='taipei' / city='metrotaipei' 兩筆
-- ===========================================================================

DELETE FROM public.query_charts
 WHERE index IN {indices_in};
DELETE FROM public.component_charts
 WHERE index IN {indices_in};
DELETE FROM public.components
 WHERE index IN {indices_in}
    OR id IN {ids_in};

-- 1. components（共用，name 不帶城市字樣，雙北儀表板顯示也合理）
INSERT INTO public.components (id, index, name) VALUES
  ({col_id},   'reuse_energy_capacity_metrotaipei', '再生能源裝置容量 - 雙北比較'),
  ({donut_id}, 'reuse_energy_mix_taipei',           '再生能源裝置容量 - 能源占比'),
  ({trend_id}, 'reuse_energy_trend_taipei',         '再生能源裝置容量 - 年趨勢'),
  ({trend_col_id}, 'reuse_energy_trend_column_taipei',
                                                    '再生能源裝置容量 - 年趨勢（縱向長條）');

-- 2. component_charts（顏色／圖表類型／單位皆共用）
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('reuse_energy_capacity_metrotaipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)'),
  ('reuse_energy_mix_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['TimelineStackedChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_column_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)');

-- 3. query_charts（每個 index 各兩筆 city）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES
-- 3-1 雙北比較（city=metrotaipei，雙北儀表板使用）
(
  'reuse_energy_capacity_metrotaipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。',
  '並列臺北市與新北市三類再生能源裝置容量，以堆疊縱向長條圖呈現；臺北市風力為 0。',
  '比較雙北綠能發展結構，輔助再生能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $${col_sql}$$,
  NULL,
  'metrotaipei'
),
-- 3-1' 雙北比較（city=taipei，臺北儀表板使用；同一份 SQL）
(
  'reuse_energy_capacity_metrotaipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。',
  '並列臺北市與新北市三類再生能源裝置容量；本元件本身即為雙北比較，臺北儀表板亦保留同一視圖。',
  '比較雙北綠能發展結構，輔助再生能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $${col_sql}$$,
  NULL,
  'taipei'
),

-- 3-2 能源占比 city=taipei（DonutChart / BarChart）
(
  'reuse_energy_mix_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市最新期三類再生能源裝置容量占比。',
  '風力：陸域與離岸；太陽光電：屋頂型與地面型合計；其他(含水力)：水力、生質能、地熱等。',
  '觀察臺北市再生能源結構偏向，作為綠色城市核心指標。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $${donut_sql_tpe}$$,
  NULL,
  'taipei'
),
-- 3-2' 能源占比 city=metrotaipei（雙北合計）
(
  'reuse_energy_mix_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期三類再生能源裝置容量占比。',
  '臺北市與新北市裝置容量加總後再依風力／太陽光電／其他(含水力)三類計算占比。',
  '觀察雙北整體再生能源結構，協助大區能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $${donut_sql_metro}$$,
  NULL,
  'metrotaipei'
),

-- 3-3 年趨勢 city=taipei（TimelineStackedChart）
(
  'reuse_energy_trend_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市再生能源裝置容量逐年趨勢。',
  '依民國 101 年起累計裝置容量逐年呈現；以堆疊面積觀察整體成長與結構變化。',
  '觀察臺北市再生能源裝置容量的成長路徑與結構演進。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'time',
  $${trend_sql_tpe}$$,
  NULL,
  'taipei'
),
-- 3-3' 年趨勢 city=metrotaipei（雙北合計）
(
  'reuse_energy_trend_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北再生能源裝置容量逐年趨勢。',
  '雙北合計：臺北市與新北市同年加總；以堆疊面積觀察整體成長與結構變化。',
  '評估雙北作為大區之綠能成長路徑。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'time',
  $${trend_sql_metro}$$,
  NULL,
  'metrotaipei'
),

-- 3-4 年趨勢縱向長條 city=taipei
(
  'reuse_energy_trend_column_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市再生能源裝置容量逐年堆疊長條。',
  '與年趨勢折線堆疊圖相同年度資料；以縱向堆疊長條呈現。11502 未納入。',
  '以長條圖比對各年度裝置容量結構。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $${trend_column_sql_tpe}$$,
  NULL,
  'taipei'
),
-- 3-4' 年趨勢縱向長條 city=metrotaipei（雙北合計）
(
  'reuse_energy_trend_column_taipei', NULL, '{{}}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北再生能源裝置容量逐年堆疊長條。',
  '雙北合計，僅取年度列；以縱向堆疊長條呈現。',
  '以長條圖比對雙北各年度裝置容量結構。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'three_d',
  $${trend_column_sql_metro}$$,
  NULL,
  'metrotaipei'
);

-- ⚠️ dashboards / dashboard_groups 已移至：
--    component_doc/seed/03_sustainable_env_dashboard.sql
-- 請在此檔執行後，另行執行該檔以建立「永續環境」儀表板。
"""


if __name__ == "__main__":
    main()
