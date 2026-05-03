

在[撰寫Python程式碼](/data-end/dag-code)的宣告變數部分使用了許多動態變數，變數的來源除了全域共用的變數外，有一大部分為每個 DAG 獨立的設定檔。

本專案為了簡化與 Airflow 互動的細節，透過一個 JSON 檔案紀錄 DAG 設定。內容可分為 `dag_infos` 與 `data_infos` 兩部分。其中 `dag_infos` 紀錄 DAG 執行相關的參數，參數會直接影響實際執行的方式。`data_infos` 記錄可供前端顯示的資料資訊，僅供顯示，不影響執行方式或結果。

> **i01**
> JSON 檔案的全部內容均會傳入 pipeline 使用，當設定檔放置正確，並且被 Airflow 偵測到，可以透過以下的程式取得完整設定檔資訊。
>
> ``` python
> from airflow import DAG
> from operators.common_pipeline import CommonDag
>
> dag = CommonDag(proj_folder='tutorial', dag_folder='simple_template')
> dag.config
> ```

> **i02**
> `data_infos` 的值會被記錄於 `db:dashboard/dashboard/dataset_info`。

## 設定檔說明

範例 DAG 的設定檔位於 `/dags/tutorial/simple_template/template_dag.py`，內容如下：

``` JSON
{
    // DAG執行所需參數
    "dag_infos": {
        "dag_id": "template_test",  // 此DAG的名稱，遵守snake命名
        "start_date": "2024-03-14",  // DAG第一次執行的日期，若日期未到，將不會執行
        "schedule_interval": "0 0 1 * *",  // 執行頻率，規則同Linux的Crontab
        "catchup": false,  // 自動執行未成功的歷史任務
        "tags": ["test", "template", "衛生局", "醫院", "heal_hospital"],  // 顯示於 Airflow 網頁介面的標籤
        "description": "A DAG only contain neccesary part for tutorial.",  // 顯示於 Airflow 網頁介面的說明，建議採英文
        "default_args": {
            "owner": "airflow",  // DAG的擁有者，需對應系統設定
            "email": ["receiver_1@mail", "receiver_2@mail"],  // 失敗或重試需要寄送的收信者，後文詳述
            "email_on_retry": false,  // DAG重新嘗試時，是否需要寄信
            "email_on_failure": true,  // DAG失敗時，是否需要寄信
            "retries": 1,  // DAG失敗時，重新嘗試次數
            "retry_delay" : 60  // DAG失敗時，重新嘗試的間隔時間
        },
        "ready_data_db": "postgres_default",  // 儲存最後資料的資料庫名稱，後文詳述
        "ready_data_default_table": "heal_hospital",  // 儲存最後資料的表名稱，遵守snake命名，後文詳述
        "ready_data_history_table": "heal_hospital_history",  // 儲存最後資料的歷史表名稱，應為ready_data_default_table後加上history，後文詳述
        "raw_data_db": "postgres_default",  // 儲存原始資料的資料庫名稱，對應Airflow conncetion變數
        "raw_data_table": "",  // 儲存原始資料的表名稱，無則不填
        "load_behavior": "current+history"  // 資料儲存方式，後文詳述
    },
    // 資料參考資訊，不影響DAG執行
    "data_infos":{
        "name_cn": "臺北市醫院清冊",  // 資料的中文名稱
        "airflow_update_freq": " first day of every month",  // 比較容易理解的schedule_interval
        "source": "https://data.taipei/dataset/detail?id=ffdd5753-30db-4c38-b65f-b77892773d60",  // 資料文件位置
        "source_type": "data.taipei API",  // 資料類型，建議格式為"{來源} {檔案類型}"
        "source_dept": "衛生局",  // 資料來源權屬機關
        "gis_format": "Point",  // 資料空間資訊類型，常見的包含"Point", "LineString", "Polygon"
        "output_coordinate": "EPSG:4326",  // 最後資料的空間坐標系統
        "is_geometry": 1,  // 本資料是否有空間資訊
        "dataset_description": "臺北市所有醫院的清冊，包含座標資訊",  // 資料細節說明
        "etl_description": "standardize time, geometry",  // 資料處理的重點資訊
        "sensitivity": "public"  // 資料敏感程度，如"public", "private"
    }
}
```

**mail:**

任意 e-mail 地址，或以 `[]` 包裝的多個 e-mail 地址，也可以是 "_MAIL_LIST" 結尾的變數。例如 `["test@mail", "DEFAULT_MAIL_LIST"]`，其中的 `"DEFAULT_MAIL_LIST"` 會自動尋找 Airflow Variables符合的 Key，並取用其中的 Value。使開發者可以靈活地建立 mail 群組使用。

**ready_data_db**

儲存 `ready_data` 的資料庫，需對應 Airflow Variables 上的 Key 以取得資料庫連線。

**raw_data_db**

預留，儲存 `raw_data` 的資料庫，需對應 Airflow Variables 上的 Key 以取得資料庫連線。

**ready_data_db 與 raw_data_db**

本專案全部使用 ETL 流程，只有在資料完全處理好時儲存，也就是只儲存 `ready_data`。但不排除開發者想使用 ELT 流程或是先儲存原始資料 `raw_data` 的可能，因此預留 `raw_data_db` 供使用。

**ready_data_default_table**

儲存 `ready_data` 的表名稱，可以單一表格 `"table"` 或 `["table1", "table2"]` 表示的多個表格名稱。

**ready_data_history_table**

儲存 `ready_data` 的 history 表名稱，只有當設定為 `load_behavior="current+history"` 時生效。

**load_behavior**

控制儲存方式，必須為 `append`, `replace`, `current+history` 三者的其中一個。`append` 是將資料無條件新增至指定表格；`replace` 是將指定表格 truncate 後，再新增資料；`current+history` 共有兩個目的地，其一為 current 表，另一張為 history 表。分別對 current 表執行上面的 replace 操作，再對 history 表執行 append 操作。

> **i03**
> `current+history` 的設計，是為了同時滿足快速與留存歷史資料。例如 YouBike 站點狀態雖然只呈現當下的即時資料，但我們留存所有歷史資料以供未來分析應用。長期下來，歷史資料會變得冗餘而查詢時間過長；因此另存 current 表，只留最後一次的資料，快速回應前端需求。
