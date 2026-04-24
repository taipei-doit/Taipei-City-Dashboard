---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/data-end/dag-table"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## DAG Table

## 標準資料表

一個標準的本專案資料表如下：

| data\_time | column\_1 | column\_2 | ... | wkb\_geometry | \_ctime | \_mtime | ogc\_fid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01-01 00:00:00+08 | value | value | ... | 010101010101 | 2024-01-02 00:00:00+8 | 2024-01-03 00:00:00+8 | 15312 |

除了資料本身資訊的 `column_1`, `column_2` 等不固定欄位，其他欄位說明如下。

### data\_time

建議但非必須。此欄位用於記錄資料內容的時間。與資料回傳時間或更新時間不同，一筆資料可能是在現在回傳，但來源更新於昨天，而內容則是上個月的資訊。若資料本身無時間資訊，建議使用更新時間代替。

### wkb\_geometry

若資料無地理空間資訊，則不需此欄位。此欄位用於記錄該資料的地理空間資訊，採用國際通用的 `EPSG:4326` 坐標系，並使用 WKBGeometry 格式記錄，以減少空間占用。

### \_ctime

此欄位紀錄該列資料的 create time，可透過本專案通用函式生成，通用函式於下文說明。

### \_mtime

此欄位紀錄該列資料的 modify time，可透過本專案通用函式生成。

> #### Information - 1
> 
> \_ctime 與\_mtime 大部分時間是一樣的，只有在執行過 update 的列會有所不同。

### ogc\_fid

此欄位使用流水數字以作為 Primary Key 使用。若資料表已有 Primary Key，則不需要此欄位。可透過本專案通用函式生成。

## 利用通用函式建表

當你想創建一張本專案的標準表時，強烈建議使用 `/dags/utils/generate_sql_to_create_DB_table.py` 來生成適當的 SQL，然後利用 pgAdmin 或類似工具來建立表格。只需修改 `generate_sql_to_create_DB_table` 當中的 `table_name`, `col_map` 變數以符合你的資料，執行程式後即可生成一段 SQL。SQL 包含你所需要的資料欄位，定位自動生成以上提及的 `_ctime`, `_mtime`, `ogc_fid` 欄位及適當的權限。

詳細說明請參閱 [通用函式-建表 SQL](https://test-citydashboard.taipei/documentation/data-end/utils-generate_sql) 章節。

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/data-end-en/dag-table.md)