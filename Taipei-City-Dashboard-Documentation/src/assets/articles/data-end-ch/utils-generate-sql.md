

此檔案的函式用以生成 SQL，生成的 SQL 可以建立本專案的標準表格。

> **w01**
> 本專案並未將建表流程自動化，建議的使用方式是執行此檔案生成 SQL 後，手動至 pgAdmin 執行。這是為了遵循較嚴格的資安規範，資料庫異動應由資料庫管理人員執行，而非資料工程師任意執行。


## 函式說明

原始碼可以在 `/dags/utils/generate_sql_to_create_DB_table.py` 找到，建議直接修改下方設定並執行，即可產出 SQL。其中的重要函式說明如下。

> **i01**
> 有關本專案的標準表格，請參閱[資料流表格](/data-end/dag-table)。

### -函式 _show_smaple_column_type()

此函式無作用，僅供參考常使用的欄位類型。


### -函式 generate_sql_to_delete_db_table(table_name, col_map)

產出建表 SQL。SQL 可讓你建立一張名為 `table_name` 且符合 `col_map` 欄位，並包含適當權限。預設會自動產出欄位 `ogc_fid`, `_ctime`, `_mitme`。

```python
from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

table_name = "heal_hospital"
col_map = {
    "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
    "name": 'character varying(50) COLLATE pg_catalog."default"',
    "addr": 'text COLLATE pg_catalog."default"',
    "lng": "double precision",
    "lat": "double precision",
    "wkb_geometry": "geometry(Point,4326)"
}

create_table_sql = generate_sql_to_create_db_table(table, col_map)
print(create_table_sql)
```

> **i02**
> histroy 表以 current 表名稱加上後墜 "\_history"

> **i03**
> `current+history` 的設計，是為了同時滿足快速與留存歷史資料。例如 YouBike 站點狀態雖然只呈現當下的即時資料，但我們留存所有歷史資料以供未來分析應用。長期下來，history 表會變得冗餘而查詢時間過長；因此另存 current 表，只留最後一次的資料，快速回應前端需求。


### -函式 generate_sql_to_delete_db_table(table_name)

產出刪表 SQL。資料庫中不可存在同樣名稱的表格，可透過此函式生成刪除 `table_name` 的 SQL，同時也會刪除表中流水號的 sequnce 及 `_mtime` 的 trigger。物件不存在不會生成錯誤。

```python
from utils.generate_sql_to_create_DB_table import generate_sql_to_delete_db_table

table_name = 'heal_hospital'
drop_table_sql = generate_sql_to_delete_db_table(table_name)
```
