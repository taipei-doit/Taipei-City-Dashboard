# eco_diet_green_stores_points — 綠色商店數量

| 屬性 | 值 |
| --- | --- |
| team | `ai-plus-one` (merit03) |
| component id | 603 |
| index | `eco_diet_green_stores_points` |
| chart types | `DonutChart`, `BarChart` |
| color | `#ec7cb1` (臺北粉) / `#67baca` (新北青) |
| unit | 家 |

---

## 對應 DAG

| 城市 | 路徑 | source | 寫入表 |
| --- | --- | --- | --- |
| 臺北市 | `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/green_store/` | `data.taipei` page_id `1756cb64-0066-444a-a323-9f3b5a961045` | `public.green_store` |
| 新北市 | `Taipei-City-Dashboard-DE/dags/proj_new_taipei_city_dashboard/green_store_ntpe/` | `data.ntpc` rid `6ccd0274-0c09-43b0-98fc-4d5222a71e8b` | `public.green_store_ntpe` |

兩支 DAG 皆 `load_behavior=replace`、`schedule_interval='0 5 1 * *'`（每月 1 號 05:00 整批覆寫）。

---

## 交付檔案

```
component-meta/eco_diet_green_stores_points/
├── eco_diet_green_stores_points.xlsx                                  ← 組件設定 (4 sheet)
├── ddl_green_store.sql                                                ← 臺北表 DDL
├── ddl_green_store_ntpe.sql                                           ← 新北表 DDL
├── sample_eco_diet_green_stores_points_taipei_green_store.csv         ← 臺北 sample (10 筆)
├── sample_eco_diet_green_stores_points_newtaipei_green_store_ntpe.csv ← 新北 sample (10 筆)
├── _build_xlsx.py                                                     ← Excel 生成工具 (可重現)
├── _dump_sample.py                                                    ← Sample CSV 生成工具
└── README.md
```

---

## Excel 4 sheet 說明

| Sheet | 對應 DB 表 | 筆數 | 備註 |
| --- | --- | --- | --- |
| `components` | `components` | 1 | id=603 |
| `query_charts` | `query_charts` | 3 | metrotaipei / taipei / newtaipei |
| `components_charts` | `component_charts` | 1 | hw.md 拼寫多 `s`,匯入時 reviewer mapping |
| `component_maps` | `component_maps` | 0 (header only) | 本 component 為統計圖,無 map |

### 匯入順序（dashboardmanager DB）

1. `components_charts` sheet → `INSERT INTO component_charts`
2. `components` sheet → `INSERT INTO components`
3. `query_charts` sheet → `INSERT INTO query_charts`
4. `component_maps` sheet 為空,跳過

#### Array 欄位的字面值格式

Excel 內 array 型別（如 `color`, `types`, `links`, `contributors`）以 PostgreSQL array literal 格式儲存（`{a,b,c}`），可直接套用 `INSERT ... VALUES (..., '{...}'::text[], ...)`。

---

## 與 PR #1260 reference 的設計差異

| 項 | PR #1260 reference | 本次交付 |
| --- | --- | --- |
| DAG 數量 | 單一合併 DAG `green_store_tpe_ntpe` | 雙 DAG (`green_store` + `green_store_ntpe`) |
| 資料表 | 單張 `green_store` 含 `city` 欄位 | 兩張 `green_store` / `green_store_ntpe` |
| 地理編碼 | TPGOS API → `lng`, `lat` | 不做（無 TPGOS Key） |
| `query_charts.query_chart` (metrotaipei) | `SELECT city, COUNT(*) FROM green_store WHERE lng IS NOT NULL AND lat IS NOT NULL GROUP BY city ORDER BY city` | `SELECT '臺北市',COUNT(*) FROM green_store WHERE store_name IS NOT NULL UNION ALL SELECT '新北市',COUNT(*) FROM green_store_ntpe WHERE store_name IS NOT NULL ORDER BY x_axis` |
| `query_charts.map_config_ids` | `ARRAY[203]/[204]/[205]` | `NULL`（本次不做 map） |
| `component_maps` | 9 筆 + 9 份 GeoJSON | 0 筆（本次不做 map） |

---

## 驗證紀錄

### DAG 驗證（commit 前必過）

#### 階段 A — `validate_dag.py`

```
$ python3 Taipei-City-Dashboard-DE/dag-toolkit/scripts/validate_dag.py \
    Taipei-City-Dashboard-DE/dags/proj_city_dashboard/green_store
驗證 DAG: proj_city_dashboard/green_store

  [PASS] __init__.py 為空檔
  [PASS] job_config.json 為合法 JSON
  [PASS] dag_infos 必填鍵齊全(10 項)
  [PASS] 三名一致: dag_folder == dag_id == table_name == 'green_store'
  …(共 24 項 PASS)…

Result: PASS (0 warn, 24 pass)
```

```
$ python3 Taipei-City-Dashboard-DE/dag-toolkit/scripts/validate_dag.py \
    Taipei-City-Dashboard-DE/dags/proj_new_taipei_city_dashboard/green_store_ntpe
驗證 DAG: proj_new_taipei_city_dashboard/green_store_ntpe

  [PASS] __init__.py 為空檔
  …(共 24 項 PASS)…

Result: PASS (0 warn, 24 pass)
```

#### 階段 B — `test_<table>.py`

```
$ docker run --rm -v <dag dir>:/work -w /work \
    develop-airflow-worker-default python test_green_store.py
[green_store] source_type=data.taipei
  ✅ data.taipei reachable, 2 sample records
     keys: ['_id', '_importdate', '序號', '綠色商店名稱', '聯絡地址',
            '商店編號', '聯絡人', '聯絡電話', '分機', '手機號碼']
All tests passed
```

```
$ docker run --rm -v <dag dir>:/work -w /work \
    develop-airflow-worker-default python test_green_store_ntpe.py
[green_store_ntpe] source_type=data.ntpc
  ✅ data.ntpc reachable, 30 sample records
     keys: ['seqno', 'type', 'city', 'countycode', 'name',
            'address', 'number', 'localcallservice']
All tests passed
```

### Query SQL 驗證（postgres-data 內 `BEGIN ... ROLLBACK`）

```
=== Q1 taipei ===
 x_axis | data
--------+------
 臺北市 |    3

=== Q2 newtaipei ===
 x_axis | data
--------+------
 新北市 |    2

=== Q3 metrotaipei (UNION) ===
 x_axis | data
--------+------
 新北市 |    2
 臺北市 |    3
```

三條 query syntax 與回傳 schema (`x_axis: text, data: float`) 皆正確。

### DDL 與 DAG COL_MAP 對齊

| DDL 欄位 | `green_store.py` COL_MAP key | 一致 |
| --- | --- | --- |
| `data_time` | `data_time` | ✅ |
| `seq` | `seq` | ✅ |
| `store_name` | `store_name` | ✅ |
| `address` | `address` | ✅ |
| `store_code` | `store_code` | ✅ |
| `contact_person` | `contact_person` | ✅ |
| `contact_phone` | `contact_phone` | ✅ |
| `extension` | `extension` | ✅ |
| `mobile` | `mobile` | ✅ |
| `store_type` | `store_type` | ✅ |

`green_store_ntpe` 對齊同理。DDL 是 DAG 內 `_ensure_ready_table` 用 `generate_sql_to_create_db_table()` 動態建表的人類可讀等價版本。

---

## 後續

- 其他 2 個 component（環保餐廳數量、實物銀行數量）在其他工作分支進行。
- 全部完成後 merge 進團隊分支 `feature/team-merit03-ai-plus-one`,再對 `feature/award-dag-integration` 開單一整隊 PR。
- 泡泡圖功能（hw.md §四）走獨立 PR `feature/ai-plus-one-bubble-chart`,不在本 branch。
- 若維護者要求加 `lng`/`lat`（取得 TPGOS Key 後）,屆時 ALTER TABLE 兩張表,並把 query 還原為 `WHERE lng IS NOT NULL AND lat IS NOT NULL` 過濾。
