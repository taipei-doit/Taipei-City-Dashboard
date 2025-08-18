from airflow import DAG
from operators.common_pipeline import CommonDag


# 定義 Airflow DAG 要執行的 ETL 任務函式
def _transfer(**kwargs):
    
    """[
        {
                "category": "私人住宅大樓",
                "number": "D101000003",
                "village": "自強里",
                "address": "新北市板橋區自強里自強新村82號",
                "latitude": "25.012807",
                "longitude": "121.45434",
                "floor": "B01",
                "capacity": "66",
                "unit": "板橋分局",
                "note": null
            }
            ]
      """
    import pandas as pd
    from sqlalchemy import create_engine
    import requests
    from io import StringIO
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import NewTaipeiAPIClient


    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"
    RID= "3a9d87f0-9490-4021-8fc9-5045ecdd8d22"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)

    data = pd.DataFrame(res)

    col_map = {
        "capacity": "person_capacity",
        "longitude": "lng",
        "latitude": "lat",
    }
    data = data.rename(columns=col_map)
    
    # 取區
    area_candidates = data['address'].str.slice(3, 6)
    data['town'] = area_candidates.apply(lambda x: x if x.endswith('區') else None)


    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "town",
            "person_capacity",
            "address",
            "lng",
            "lat",
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
    dag_folder='urbn_air_raid_shelter'
)

# 將 _transfer 函式掛載為 DAG 的主要 ETL 任務
dag.create_dag(etl_func=_transfer)
