---
title: 撰寫程式碼

---

## 前言

在一般資料流開發場景中，您需要開發的 Python 程式碼通常存放於一個 `.py` 檔案中。例如，範例 DAG 位於 `/dags/tutorial/simple_template/template_dag.py`。

> **i01**
> 要將程式轉變為一個 DAG 並在 Airflow 中執行需要進行多項設定。本專案旨在降低開發門檻，使開發者能在不需深入了解 Airflow 的情況下創建資料流。因此，在一般開發中隱藏了與 Airflow 的互動。本章僅說明一般開發場景，目的是讓開發者能以最快的速度創建資料流。更複雜的開發，如修改本專案的通用函式或修改 pipeline，請參見 `進階` 分類下的章節。


## 注意事項

在程式碼說明之前，以下是一些特殊規則或強烈建議的說明。

> **w01**
> 本專案的時間欄位均會加上時區資訊，採[ISO 8601](https://en.wikipedia.org/wiki/ISO_8601)儲存，以避免在不同系統介接時發生轉換錯誤。

> **w02**
> 本專案的地理空間欄位，均以 `WGS84` 也就是 `EPSG:4326` 坐標系，並轉換成 WKBGeometry 格式儲存。[WGS84](https://en.wikipedia.org/wiki/World_Geodetic_System)是國際通用的經緯度座標系，[WKBGeometry](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry)則是一種為較節省儲存空間的格式。

> **w03**
> 除了儲存資料外，為了讓前端可以呈現資料的資訊，如更新時間、資料內容的時間等，`db:dashboard/dashboard/dataset_info` 負責記錄每個DAG的相關資訊。

## 程式碼說明

程式碼可在`/dags/proj_city_dashboard/simple_template/template_dag.py`找到，內容如下：

``` python
from airflow import DAG
from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    from utils.extract_stage import get_data_taipei_api
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from sqlalchemy import create_engine

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_path = kwargs.get("data_path")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Manually set
    RID = "04a3d195-ee97-467a-b066-e471ff99d15d"
    PAGE_ID = "ffdd5753-30db-4c38-b65f-b77892773d60"
    FROM_CRS = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    # Rename
    data = raw_data
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "機構名稱": "name",
            "地址": "addr",
            "經度": "lng",
            "緯度": "lat",
            "data_time": "data_time",
        }
    )
    # Time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    gdata = gdata.drop(columns=["geometry", "_id"])
    ready_data = gdata[["data_time", "name", "addr", "lng", "lat", "wkb_geometry"]]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="tutorial", dag_folder="simple_template")
dag.create_dag(etl_func=etl_function)
```

全部程式碼可以大概被拆分成6個區塊理解，對應位置如下：

```python
1.pipeline設定

def etl_function(**kwargs):
    2.引入套件
    3.靜態變數宣告
    4.Extract
    5.Transform
    6.Load

1.pipeline設定
```

以下將詳細說明每個區塊的內容。

### 1. pipeline 設定

``` python
from airflow import DAG
from operators.common_pipeline import CommonDag

......

dag = CommonDag(proj_folder='tutorial', dag_folder='simple_template')
dag.create_dag(etl_func=etl_function)
```

本專案透過 `/dags/operators/common_pipeline.py` 隱藏與 Airflow 互動的細節，一般開發僅需要使用這段程式碼，並修改 `proj_folder`, `dag_folder`, `etl_func` 三個參數即可將 ETL 內容部屬至 Airflow。
ETL 相關的程式碼，務必確保包裝成一個函式並傳遞至 `dag.create_dag`。


### 2. 引入套件

``` python
    from utils.extract_stage import taipei_opendata_offset_function
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_datataipei_data_file_last_modeified_time
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
```

Import 在 top level 而非在 function level 是根據官方建議，旨在避免[Top level Python Code](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code)的問題。其中 `from utils.* import *` 是引用本專案的通用函式，這些函式的作用將在後文中詳細解釋。


> **i01**
> 全部通用函式的說明請見 `進階` 章節，或至 `/dags/utils` 查看原始碼.


### 3. 靜態變數宣告

``` python
    # 全域設定
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_path = kwargs.get("data_path")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    # DAG設定
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # ETL變數
    RID = "04a3d195-ee97-467a-b066-e471ff99d15d"
    PAGE_ID = "ffdd5753-30db-4c38-b65f-b77892773d60"
    FROM_CRS = 4326
```

建議將使用到的變數置於最上方，方便閱讀。

其中使用到的全域設定，已於[確認全域變數](/data-end/global-config)章節說明；DAG 設定在下章節[撰寫DAG設定](/data-end/dag-config)說明；ETL 變數則依開發需求給定。


### 4. Extract

``` python
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)
```

Extract 部分只應該負責取得資料或包含極少的處理。盡可能令 `raw_data` 保留原始，以利後續比較原始資料與處理後資料的差別。

> **i02**
> `get_data_taipei_api` 將根據 `RID`，自 data.taipei 的 API 取得資料。其中重要的是，data.taipei 的 API 每次最多回傳 1,000 筆資料，此函式會自動迴圈取得完整資料。

> **i03**
> `get_data_taipei_file_last_modified_time` 將根據 `PAGE_ID`，自 data.taipei 的網頁取得檔案最後更新時間。


### 5. Transfrom

``` python
    # Transform
    # Rename
    data = raw_data
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={"機構名稱": "name", "地址": "addr", "x": "lng", "y": "lat"}
    )
    # Time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    gdata = gdata.drop(columns=["geometry", "_id"])
    ready_data = gdata[["data_time", "name", "addr", "lng", "lat", "wkb_geometry"]]
```

Transfrom 是最複雜且無法制式化的部分，我們習慣的步驟是：

**_looks_one_** 複製一份原始資料，方便區分階段，也避免在開發測試時，一直重新讀資料。

**_looks_two_** 重命名成易懂的欄位名稱，也讓後續開發者能大概知道資料的內容。

**_looks_3_** 欄位型態轉換與處理

**_looks_4_** 時間標準化

**_looks_5_** 地理空間標準化。將此步驟放在最後，因為資料會被轉成 gpd.geoDataFrame。

**_looks_6_** 選取所需要的欄位。請盡可能保留資料，資料最小化的步驟由後端執行。

> **w04**
> 務必確保 `geometry` 或 `wkb_geometry` 只保留其中一個。若同時將兩個放入資料庫，可能會導致錯誤。

> **i04** 
> `convert_str_to_time_format` 將文字轉成帶有時區的時間格式。特別的是，函式能處理民國年格式，例如"111/02/31"可透過 `from_format="%TY/%m/%d"` 轉換成西元年。

> **i05**
> `add_point_wkbgeometry_column_to_df` 將 x, y 合併成名為 `geometry` 的 `Point` 欄位加入原始資料。同時對原始資料加入名為 `wkb_geometry` 的 WKBGeometry 的欄位。


### 6. Load

``` python
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine, gdata=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
        geometry_type='Point'
    )

    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )
```

本專案使用 ETL 流程，只有在資料完全處理好時儲存，也就是只儲存 `ready_data`。

> **i06** 
> `save_geodataframe_to_postgresql` 函式會將有地理空間資訊的資料存入資料庫。
> `load_behavior`: 控制儲存方式，必須為 `append`, `replace`, `current+history` 三者的其中一個。`append` 是將資料無條件新增至指定表格；`replace` 是將指定表格 truncate 後，再新增資料；`current+history` 共有兩個目的地，其一為 current 表，另一張為 history 表。分別對 current 表執行上面的 replace 操作，再對 history 表執行 append 操作。
> `default_table`: 一般而言，是唯一的目的地表名，僅在 `load_behavior="current+history"` 視為 current 表儲存。
> `ready_data_history_table`: 是 `ready_data` 的 history 表名，只有在 `load_behavior="current+history"` 時生效。
> `geometry_type`: 是地理空間欄位的類型，必須為'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'LineStringZ', 'MultiLineStringZ', 'PolygonZ', 'MultiPolygonZ' 其中之一，且與資料庫內欄位一致。

> **i07**
> `current+history` 的設計，是為了同時滿足快速與留存歷史資料。例如 YouBike 站點狀態雖然只呈現當下的即時資料，但我們留存所有歷史資料以供未來分析應用。長期下來，歷史資料會變得冗餘而查詢時間過長；因此另存 current 表，只留最後一次的資料，快速回應前端需求。

> **i08**
> `update_lasttime_in_data_to_dataset_info` 將最新的 `data_time` 更新至 `dataset_info`。`data_time` 是指資料內容的時間。例如資料可以是今天更新，但裡面的內容是上個月的資料。
