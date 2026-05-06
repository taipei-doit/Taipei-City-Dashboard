# [Team <team-rank>] <teamname> — DAG 整併 (N 支)

> **PR target**: `feature/award-dag-integration`(2026 雙北儀表板 DAG 整併)
> **PR source**: `feature/team-<rank>-<teamname>`(例:`feature/team-no2-transportation`、`feature/team-merit01-publicworks`)
> 請勿直接 PR 至 `sit` / `develop` / `main`,sit 同步由維護者人工進行。

## 本 PR 包含 DAG 清單

| # | proj_folder | table_name | name_cn | component_name | load_behavior | is_geometry |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | proj_city_dashboard | <table_1> | <中文名 1> | <component slug> | append/replace/current+history | 0/1 |
| 2 | ... | ... | ... | ... | ... | ... |

---

> **以下區塊請依 DAG 數量複製,每支 DAG 各填一份**

---

## DAG 1 — `<proj_folder>/<table_name>` — `<name_cn>`

### 資料來源

- **name_cn**: <中文資料名>
- **source**: <URL>
- **source_dept**: <提供機關>
- **source_type**: <data.taipei | data.ntpc | tdx | moenv | csv | csv-big5 | shp | api>
- **component_name**: <前端 component slug,可與其他排程共用>
- **schedule_interval**: <cron 或 @monthly> (queue: <realtime | default | heavy>)
- **load_behavior**: <append | replace | current+history>
- **是否含 geometry**: <yes (Point/MultiLineString/MultiPolygon) | no>

### DB Schema(由 ETL 函式內 `_ensure_ready_table` 自動建表)

```python
COL_MAP = {
    "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
    # ...
}
```

(完整 col_map 見 `<table_name>.py`,首次跑 DAG 時會用 `generate_sql_to_create_db_table` 自動建表)

### 本機驗證(必貼以下兩段輸出)

#### 階段 A — validator

```
$ python Taipei-City-Dashboard-DE/dag-toolkit/scripts/validate_dag.py \
    Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>

驗證 DAG: <proj_folder>/<table_name>
路徑: ...

  [PASS] ... (請貼 validator 完整輸出最後 5~10 行)
  ...

Result: PASS (X warn, Y pass)
```

#### 階段 B — source URL test

```
$ cd Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>
$ python test_<table_name>.py

[<table_name>] source_type=...
  ✅ ... reachable, ... records
All tests passed
```

---

## DAG 2 — `<proj_folder>/<table_name>` — `<name_cn>`

(同上格式,複製貼上後填寫該支 DAG 的內容)

---

## 待辦(整 PR 共用)

- [ ] Airflow Variable 需建立: `<NAME>`(用途:<描述>)
- [ ] Airflow Connection 需建立: `<NAME>`(用途:<描述>)
- [ ] 其他外部依賴

## Custom inline requests 通知(若有)

> 若任一支 DAG 使用 inline `requests`(規則 C 觸發),請於此處列出並 @ 維護者:
>
> - <table_name>:來源 <URL>,無對應 utils helper
> - cc: <維護者 @handle>
>
> 對應 commit message 應含 `[needs-helper-review]` 標籤。

## Reviewer Checklist(每支 DAG 都要過)

- [ ] `dag_folder == dag_id == ready_data_default_table` 三名一致
- [ ] `data_infos.component_name` 已填且為 snake_case
- [ ] `COL_MAP` 完整 vs DataFrame 最終 select 欄位對齊
- [ ] 無寫死 email / token / 連線字串
- [ ] tags 含主分類、source_dept、city tag(`Taipei-City` 或 `New-Taipei-City`)
- [ ] 排程合理(queue 落點符合預期)
- [ ] validator PASS,test PASS
- [ ] commit 切分清楚(每支 DAG 一個 commit,訊息對應)
- [ ] 維護者:可額外跑 `python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py` 一次掃完整 PR 全部 DAG 的 test
