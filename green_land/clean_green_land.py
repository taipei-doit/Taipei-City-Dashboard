"""
clean_green_land.py — 臺北市市容綠美化 清洗腳本
輸入: 臺北市市容綠美化.csv
輸出:
  output/processed/green_land_beautification.csv
  output/seed/01_dashboard_data.sql   (dashboard DB)
  output/seed/02_dashboardmanager_components.sql  (dashboardmanager DB)

組件 ID 配置:
  932  green_land_vegetation   樹木植栽培育（分組縱向長條） three_d ColumnChart  單位: 株/盆（各期原值）
  936  green_land_summary      綠美化關鍵指標（最新年份）   three_d TextUnitChart  4 格數字看板：
         • 道路綠地累計面積（平方公尺）
         • 路燈累計清洗汰換（盞）
         • 後巷美化累計巷數（條，來源已累計）
         • 田園城市示範園圃面積（平方公尺，最新快照）

累計規則（除 932 植栽五欄外）:
  • road_green_m2、streetlight_units：依 roc_year 由小到大做累加（當期值視為該期增量）。
  • alley_count：原始 CSV 欄位即「後巷美化累計巷數」，已是累計，不再二次加總。
  • demo_farm_m2：各期為示範園圃面積快照（可能遞減），不適合逐期加總，維持原值。

排除欄位: 樹木修剪數[株]、公有田園城市示範園圃/建置數[處]
"""

import os
import csv

# ── 路徑 ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_CSV  = os.path.join(BASE_DIR, "臺北市市容綠美化.csv")
OUT_DIR  = os.path.join(BASE_DIR, "output")
PROC_DIR = os.path.join(OUT_DIR, "processed")
SEED_DIR = os.path.join(OUT_DIR, "seed")
os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(SEED_DIR, exist_ok=True)

# ── 欄位對應（排除樹木修剪數、建置數） ────────────────────────────────────────
SRC_COLS = {
    "統計期":                            "stat_label",
    "道路綠地綠美化面積[平方公尺]":       "road_green_m2",
    "行道樹[株]":                        "street_trees",
    "公園內喬木數[株]":                  "park_trees",
    "鄰里公園內喬木數[株]":              "neighborhood_park_trees",
    "草花培育數[盆]":                    "flower_pots",
    "灌木培育數[株]":                    "shrub_count",
    "路燈器具清洗汰換數[盞]":            "streetlight_units",
    "後巷美化累計巷數[條]":              "alley_count",
    "公有田園城市示範園圃/面積[平方公尺]": "demo_farm_m2",
    # 排除: 樹木修剪數[株]、公有田園城市示範園圃/建置數[處]
}

OUT_COLS = [
    "stat_label", "roc_year",
    "road_green_m2", "street_trees", "park_trees",
    "neighborhood_park_trees", "flower_pots", "shrub_count",
    "streetlight_units", "alley_count", "demo_farm_m2",
]

# 對「當期增量」欄位做逐期累加（依 roc_year 排序）。
# 植栽五欄（street_trees…shrub_count）不在此列，維持原值。
CUMSUM_INCREMENTAL_COLS = ("road_green_m2", "streetlight_units")


def parse_roc_year(label: str) -> int:
    """'114年' → 114"""
    return int(label.replace("年", ""))


def load_rows():
    rows = []
    with open(SRC_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            label = r["統計期"].strip()
            year  = parse_roc_year(label)
            row = {"stat_label": label, "roc_year": year}
            for src, dst in SRC_COLS.items():
                if src == "統計期":
                    continue
                val = r.get(src, "0").strip() or "0"
                row[dst] = int(val)
            rows.append(row)
    return rows


def apply_running_totals(rows: list) -> list:
    """
    依 roc_year 排序後，對 CUMSUM_INCREMENTAL_COLS 做累加；
    植栽欄位與後巷／田園欄位規則見模組 docstring。
    """
    rows = sorted(rows, key=lambda r: r["roc_year"])
    acc = {k: 0 for k in CUMSUM_INCREMENTAL_COLS}
    for r in rows:
        for k in CUMSUM_INCREMENTAL_COLS:
            acc[k] += int(r[k])
            r[k] = acc[k]
    return rows


# ── 輸出 processed CSV ─────────────────────────────────────────────────────────
def write_processed_csv(rows):
    path = os.path.join(PROC_DIR, "green_land_beautification.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ processed CSV → {path}")


# ── 01_dashboard_data.sql ─────────────────────────────────────────────────────
def write_01_sql(rows):
    lines = [
        "-- green_land / 01_dashboard_data.sql → DB: dashboard",
        "-- 由 clean_green_land.py 自 臺北市市容綠美化.csv 產生",
        "-- 排除: 樹木修剪數[株]、公有田園城市示範園圃/建置數[處]",
        "-- 道路綠地面積、路燈汰換數: 已做逐期累加；植栽五欄為各期原值；",
        "-- 後巷為來源累計巷數；田園面積為各期快照（見 clean_green_land.py 註解）。",
        "",
        "DROP TABLE IF EXISTS public.green_land_beautification;",
        "",
        "CREATE TABLE public.green_land_beautification (",
        "    id                      SERIAL PRIMARY KEY,",
        "    stat_label              VARCHAR(20) NOT NULL,",
        "    roc_year                INTEGER NOT NULL,",
        "    road_green_m2           INTEGER NOT NULL DEFAULT 0,",
        "    street_trees            INTEGER NOT NULL DEFAULT 0,",
        "    park_trees              INTEGER NOT NULL DEFAULT 0,",
        "    neighborhood_park_trees INTEGER NOT NULL DEFAULT 0,",
        "    flower_pots             INTEGER NOT NULL DEFAULT 0,",
        "    shrub_count             INTEGER NOT NULL DEFAULT 0,",
        "    streetlight_units       INTEGER NOT NULL DEFAULT 0,",
        "    alley_count             INTEGER NOT NULL DEFAULT 0,",
        "    demo_farm_m2            INTEGER NOT NULL DEFAULT 0",
        ");",
        "",
        "CREATE INDEX IF NOT EXISTS idx_green_land_roc_year",
        "    ON public.green_land_beautification (roc_year);",
        "",
    ]
    for r in rows:
        cols = ", ".join(k for k in OUT_COLS if k != "stat_label" and k != "roc_year")
        vals = ", ".join(
            str(r[k]) for k in OUT_COLS if k != "stat_label" and k != "roc_year"
        )
        lines.append(
            f"INSERT INTO public.green_land_beautification "
            f"(stat_label, roc_year, {cols}) "
            f"VALUES ('{r['stat_label']}', {r['roc_year']}, {vals});"
        )

    path = os.path.join(SEED_DIR, "01_dashboard_data.sql")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✓ 01_dashboard_data.sql → {path}")


# ── 02_dashboardmanager_components.sql ────────────────────────────────────────
def write_02_sql():
    content = """\
-- ===========================================================================
-- green_land / 02_dashboardmanager_components.sql → DB: dashboardmanager
--
-- 兩個組件：
--   932  green_land_vegetation  樹木植栽培育（逐年分組長條）  three_d  ColumnChart  株/盆（各期原值）
--   936  green_land_summary     綠美化關鍵指標（最新年份）    three_d  TextUnitChart
--          4 格數字看板：道路綠地累計面積（㎡）、路燈累計清洗汰換（盞）、
--                       後巷美化（累計條）、田園園圃面積（最新快照㎡）
--
-- 橫軸（932）：統計期（民國年，如 89年）
-- 先執行 00_alter_component_charts_stacked.sql（加 stacked 欄），再執行 01，最後本檔
-- ===========================================================================

-- 0. 冪等清除（含舊版單指標組件 931/933/934/935）
DELETE FROM public.query_charts
 WHERE index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');
DELETE FROM public.component_charts
 WHERE index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');
DELETE FROM public.components
 WHERE id IN (930,931,932,933,934,935,936)
    OR index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');

-- ============================================================================
-- 1. components
-- ============================================================================
INSERT INTO public.components (id, index, name) VALUES
  (932, 'green_land_vegetation', '樹木植栽培育量'),
  (936, 'green_land_summary',    '綠美化關鍵指標');

-- ============================================================================
-- 2. component_charts
-- ============================================================================
INSERT INTO public.component_charts (index, color, types, unit, stacked) VALUES
  ('green_land_vegetation',
    ARRAY['#81C784','#43A047','#1B5E20','#AED581','#C5E1A5']::varchar[],
    ARRAY['ColumnChart']::varchar[], '株/盆', FALSE),
  -- TextUnitChart 使用 3 種顏色：color[0]=指標名稱, color[1]=數值, color[2]=單位
  ('green_land_summary',
    ARRAY['#A5D6A7','#F9A825','#66BB6A']::varchar[],
    ARRAY['TextUnitChart']::varchar[], '', FALSE);

-- ============================================================================
-- 3. query_charts
-- ============================================================================

-- 932 green_land_vegetation（樹木植栽培育, three_d, 5 系列, stacked=FALSE 分組長條）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter, time_from, time_to,
  update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
  links, contributors, created_at, updated_at, query_type, query_chart, query_history, city
) VALUES (
  'green_land_vegetation', NULL, '{}', NULL, 'static', NULL,
  1, 'year',
  '臺北市政府開放資料平台 / 市容綠美化統計',
  '臺北市行道樹、公園喬木、鄰里公園喬木、灌木、草花逐年培育量。',
  '各類植栽培育量以分組縱向長條圖呈現，單位：株（盆）。各期為當年度培育量原值，未做累計。',
  '城市植栽生態與綠化政策追蹤。',
  ARRAY[]::text[], ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT g.stat_label            AS x_axis,
       ''::text                AS icon,
       m.metric_label          AS y_axis,
       m.metric_value::integer AS data
  FROM public.green_land_beautification g
  CROSS JOIN LATERAL (VALUES
    (1, '行道樹[株]',          g.street_trees),
    (2, '公園內喬木數[株]',     g.park_trees),
    (3, '鄰里公園內喬木數[株]', g.neighborhood_park_trees),
    (4, '灌木培育數[株]',       g.shrub_count),
    (5, '草花培育數[盆]',       g.flower_pots)
  ) AS m(ord, metric_label, metric_value)
  ORDER BY g.roc_year, m.ord$$,
  NULL, 'taipei'
);

-- 936 green_land_summary（綠美化關鍵指標, three_d → TextUnitChart）
-- categories 只有一個空字串；每一列成為一個 series（name=指標, icon=單位, data=[數值]）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter, time_from, time_to,
  update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
  links, contributors, created_at, updated_at, query_type, query_chart, query_history, city
) VALUES (
  'green_land_summary', NULL, '{}', NULL, 'static', NULL,
  1, 'year',
  '臺北市政府開放資料平台 / 市容綠美化統計',
  '臺北市市容綠美化四項關鍵指標最新累計值。',
  '道路綠地累計面積、路燈累計清洗汰換、後巷美化累計巷數、田園城市示範園圃面積（最新年份快照）。',
  '城市市容綠美化政策成果一覽。',
  ARRAY[]::text[], ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT ''::text AS x_axis,
       m.unit  AS icon,
       m.label AS y_axis,
       m.val   AS data
  FROM (VALUES
    ('道路綠地累計面積', '平方公尺',
       (SELECT road_green_m2     FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('路燈累計清洗汰換', '盞',
       (SELECT streetlight_units FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('後巷美化累計巷數', '條',
       (SELECT alley_count       FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('田園城市示範園圃面積', '平方公尺',
       (SELECT demo_farm_m2      FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1))
  ) AS m(label, unit, val)$$,
  NULL, 'taipei'
);
"""
    path = os.path.join(SEED_DIR, "02_dashboardmanager_components.sql")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ 02_dashboardmanager_components.sql → {path}")


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rows = load_rows()
    rows = apply_running_totals(rows)
    write_processed_csv(rows)
    write_01_sql(rows)
    write_02_sql()
    print(f"\n✅ 共 {len(rows)} 筆資料清洗完成")
    print("  組件 ID: 932(植栽ColumnChart) 936(關鍵指標TextUnitChart)")
