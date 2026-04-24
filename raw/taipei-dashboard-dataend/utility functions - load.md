---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/data-end/utils-load"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Utility Functions - Load

將帶有地理資訊或不帶地理資訊的表格存入資料庫。你可以在 `/dags/utils/load_stage.py` 查看相關程式碼。

> #### Warning - 1
> 
> 務必確認你已經查看 [下載並設定專案](https://test-citydashboard.taipei/documentation/data-end/project-setup) 章節並設置完成。

> #### Warning - 2
> 
> 若開發者在 Airflow 環境想單獨測試以下程式碼，需先執行以下程式碼取得環境設定。
> 
> ```python
> from airflow import DAG
> ```

> #### Warning - 3
> 
> 若開發者需要在非 Airflow 的環境測試以下程式碼，需添加以下幾行程式，以確保將本專案的路徑加入環境變數，從而能找到 `utils` 與 `settings` 等資料夾：
> 
> ```python
> import os
> import sys
> 
> dags_path = os.path.join(os.getcwd(), 'dags') 
> sys.path.append(dags_path)
> ```

## 函式說明

由於以下函式均涉及資料庫，必須先建立資料接著建立表格，無法透過很短的程式示範，請參考具體資料流。

### \-函式 save\_dataframe\_to\_postgresql(engine, data, load\_behavior, default\_table, history\_table)

將不包含地理空間資訊的 `data` 存入 `engine` 連接的資料庫。其他參數說明如下：

looks\_one `load_behavior`: 控制儲存方式，必須為 `append`, `replace`, `current+history` 三者的其中一個。 `append` 是將資料無條件新增至指定表格； `replace` 是將指定表格 truncate 後，再新增資料； `current+history` 共有兩個目的地，其一為 current 表，另一張為 history 表。分別對 current 表執行上面的 replace 操作，再對 history 表執行 append 操作。

looks\_two `default_table`: 一般而言，是唯一的目的地表名，僅在 `load_behavior="current+history"` 時視為 current 表儲存。

looks\_3 `history_table`: 是 ready\_data 的 history 表名，只有在 `load_behavior="current+history"` 時生效。

> #### Information - 1
> 
> `current+history` 的設計，是為了同時滿足快速與留存歷史資料。例如 YouBike 站點狀態雖然只呈現當下的即時資料，但我們留存所有歷史資料以供未來分析應用。長期下來，歷史資料會變得冗餘而查詢時間過長；因此另存 current 表，只留最後一次的資料，快速回應前端需求。

### \-函式 save\_geodataframe\_to\_postgresql(engine, gdata, load\_behavior, geometry\_type, default\_table, history\_table, geometry\_col)

將包含地理空間資訊的 `gdata` 存入 `engine` 連接的資料庫。其他參數說明如下：

looks\_one `load_behavior`: 同上方函式。

looks\_two `geometry_type`: 是地理空間欄位的類型必須為 'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'LineStringZ', 'MultiLineStringZ', 'PolygonZ', 'MultiPolygonZ' 其中之一，且與資料庫內欄位一致。

looks\_3 `default_table`: 同上方函式。

looks\_4 `history_table`: 同上方函式。

looks\_5 `geometry_col`: 包含地理空間資訊的欄位名，預設為 `wkb_geometry` 。

### \-函式 update\_lasttime\_in\_data\_to\_dataset\_info(engine, airflow\_dag\_id, lasttime\_in\_data)

更新指定 DAG 的最新資料內容時間，以供前端呈現。 將 `db:dashboard/dashboard/dataset_info` 表中 `airflow_dag_id` 的 `lasttime_in_data` 欄位，值更新為 `lasttime_in_data` 。

looks\_one `airflow_dag_id`: 指定 DAG 的 ID。

looks\_two `lasttime_in_data`: 格式如 `2024-02-15 16:40:54+08` ，若無給定，則使用現在台北時間。

> #### Information - 2
> 
> `dataset_info` 是本專案用來記錄資料 meatadata 的表格，說明請見 [資料庫概覽](https://test-citydashboard.taipei/documentation/data-end/database) 。

### \-函式 drop\_duplicated\_after\_saving(engine, psql\_table, criterion, comparing\_col)

刪除重複資料。刪除 `engine` 指向的資料庫的 `psql_table` 表中， `criterion` 重複之中 `comparing_col` 較小者。

此函式是對以下 SQL 的包裝，原始的 SQL 為：

```sql
DELETE FROM test_table a USING test_table b
WHERE a.ogc_fid < b.ogc_fid
    AND a."FNumber" = b."FNumber"
```

轉換成本函式：

```python
drop_duplicated_after_saving(
    engine,
    psql_table="test_table",
    criterion='AND a."FNumber" = b."FNumber"',
    comparing_col="ogc_fid"
)
```

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/data-end-en/utils-load.md)