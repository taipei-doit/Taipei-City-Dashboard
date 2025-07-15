from airflow import DAG
from operators.common_pipeline import CommonDag


# 定義 Airflow DAG 要執行的 ETL 任務函式
def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    import requests
    from io import StringIO
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"
    URL = 'https://data.ntpc.gov.tw/api/datasets/f531a808-4aab-4e5e-93f0-c34f9ff97a78/csv/file'
    response = requests.get(URL, verify=False)
    # 讀取 CSV
    data = pd.read_csv(StringIO(response.text))
    
    col_map = {
        "title": "name",
        "town": "district",
        "areacode": "zip_code",
    }
    data = data.rename(columns=col_map)
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    # get geometry
    # clean addr
    data["address"] = data["county"].astype(str) + data["district"].astype(str) + data["address"].astype(str)
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    # get gis xy
    data["longitude"], data["latitude"] = get_addr_xy_parallel(output)
    # standarlize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "name",
            "district",
            "zip_code",
            "address",
            "tel",
            "longitude",
            "latitude",
            "wkb_geometry",
        ]
    ]


    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
            engine,
            gdata=ready_data,
            load_behavior=load_behavior,
            default_table=default_table,
            history_table=history_table,
            geometry_type=GEOMETRY_TYPE,
        )
        # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

# 建立 DAG 物件，指定專案與 DAG 所在目錄
dag = CommonDag(
    proj_folder='proj_new_taipei_city_dashboard',
    dag_folder='elderly_club'
)

# 將 _transfer 函式掛載為 DAG 的主要 ETL 任務
dag.create_dag(etl_func=_transfer)
