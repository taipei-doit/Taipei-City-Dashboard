from airflow import DAG
from operators.common_pipeline import CommonDag


def _water_pull(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    proxies = kwargs.get("proxies")

    url = "https://heopublic.gov.taipei/taipei-heo-api/openapi/pumb/latest"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res = requests.get(url, proxies=proxies, timeout=60)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    raw_data = pd.DataFrame(res_json)

    # Transform
    data = raw_data.copy()

    # 時間格式轉換
    data["rec_time"] = convert_str_to_time_format(
        data["obs_time"], from_format="%Y-%m-%d %H:%M:%S"
    )

    # 加上 geometry 欄位
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lon"], data["lat"], from_crs=FROM_CRS
    )

    # 欄位篩選與命名
    ready_data = gdata[
        [
            "stn_id",
            "stn_name",
            "rec_time",
            "inner_value",
            "outer_value",
            "pumb_num",
            "door_num",
            "pumb_status",
            "door_status",
            "max_allowable_water_level",
            "lon",
            "lat",
            "wkb_geometry",
        ]
    ].rename(
        columns={
            "stn_id": "station_no",
            "stn_name": "station_name",
            "lon": "lng",
        }
    )

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    lasttime_in_data = ready_data["rec_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="water_pull")
dag.create_dag(etl_func=_water_pull)
