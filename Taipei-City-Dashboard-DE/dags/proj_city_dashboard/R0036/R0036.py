from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0036(**kwargs):
    import pandas as pd
    import requests
    from airflow.models import Variable
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
    url = "https://wic.heo.taipei/OpenData/API/Pump/Get?stationNo=&loginId=pumping&dataKey=3D9A9570"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res = requests.get(url, proxies=proxies, timeout=60)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    raw_data = pd.DataFrame(res_json["data"])

    # Transform
    data = raw_data.copy()
    # rename
    col_map = {
        "stationNo": "station_no",
        "stationName": "station_name",
        "allPumbLights": "all_pumb_lights",
        "pumbNum": "pumb_num",
        "doorNum": "door_num",
    }
    data = data.rename(columns=col_map)
    # time
    data["rec_time"] = convert_str_to_time_format(
        data["recTime"], from_format="%Y%m%d%H%M"
    )
    # get pump location
    engine = create_engine(ready_data_db_uri)
    location_data = pd.read_sql(
        "SELECT * FROM work_pump_station_static_info", con=engine
    )
    loc_data = pd.DataFrame(location_data)
    loc_gdata = add_point_wkbgeometry_column_to_df(
        loc_data, loc_data["lng"], loc_data["lat"], from_crs=FROM_CRS
    )
    loc_gdata.drop(columns=["geometry", "_ctime", "_mtime"], inplace=True)
    # pump location
    col_map = {
        "站碼": "station_no",
        "站名": "station_name",
        "流域": "river_basin",
        "警戒水位": "warning_level",
        "起抽水位": "start_pumping_level",
    }
    loc_gdata = loc_gdata.rename(columns=col_map)
    join_data = data.merge(loc_gdata, how="left", on="station_name")
    join_data = join_data.rename(columns={"station_no_x": "station_no"})
    # select columns
    ready_data = join_data[
        [
            "station_no",
            "station_name",
            "rec_time",
            "all_pumb_lights",
            "pumb_num",
            "door_num",
            "river_basin",
            "warning_level",
            "start_pumping_level",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

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
    lasttime_in_data = data["rec_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0036")
dag.create_dag(etl_func=_R0036)
