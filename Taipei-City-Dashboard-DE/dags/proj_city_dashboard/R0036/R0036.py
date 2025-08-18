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
    url = "https://heopublic.gov.taipei/taipei-heo-api/openapi/pumb/latest"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res = requests.get(url, proxies=proxies, timeout=60)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    
    # Debug: Check the structure of the response
    print(f"Response type: {type(res_json)}")
    if isinstance(res_json, dict):
        print(f"Available keys: {list(res_json.keys())}")
    elif isinstance(res_json, list):
        print(f"Response is a list with {len(res_json)} items")
        if len(res_json) > 0:
            print(f"First item type: {type(res_json[0])}")
            if isinstance(res_json[0], dict):
                print(f"First item keys: {list(res_json[0].keys())}")
    
    # Handle different response structures
    if isinstance(res_json, list):
        raw_data = pd.DataFrame(res_json)
    elif isinstance(res_json, dict) and "data" in res_json:
        raw_data = pd.DataFrame(res_json["data"])
    else:
        raise ValueError(f"Unexpected response structure: {type(res_json)}")

    # Transform
    data = raw_data.copy()
    # rename
    
    # "stn_id": "208",
    # "stn_name": "經貿",
    # "lon": 121.6209,
    # "lat": 25.05629,
    # "obs_time": "2025-08-18 16:50:00",
    # "inner_value": "7.33",
    # "outer_value": "1.4",
    # "pumb_num": 2,
    # "door_num": 1,
    # "pumb_status": "停止",
    # "door_status": "閘門開啟",
    # "max_allowable_water_level": 9.1
    col_map = {
        "stn_id": "station_no",
        "stn_name": "station_name",
        "obs_time": "recTime",
        "max_allowable_water_level":"warning_level",
        "pumb_status":"all_pumb_lights",
        "lon":"lng"
    }
    data = data.rename(columns=col_map)
    # time
    data["rec_time"] = convert_str_to_time_format(
        data["recTime"], from_format="%Y%m%d%H%M"
    )
    # get pump location
    engine = create_engine(ready_data_db_uri)

    data = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    # pump location
    data["start_pumping_level"] = ""
    data['river_basin'] = ""
    
    # select columns
    ready_data = data[
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
