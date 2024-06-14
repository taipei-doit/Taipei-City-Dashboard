from airflow import DAG
from operators.common_pipeline import CommonDag
from settings.global_config import DATA_PATH


def _D050301_1(**kwargs):
    import json

    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    url = "https://farmcity.taipei/city/api/"
    filename = "D050301_1.json"
    local_filename = f"{DATA_PATH}/{filename}"
    from_crs = 4326
    geometry_type = "Point"

    # Extract
    local_file = download_file(filename, url)
    if not local_file:
        return False
    with open(local_filename) as json_file:
        res = json.load(json_file)
    raw_data = pd.DataFrame(res)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    col_map = {
        "bi_title": "name",  # 基地名稱
        "bi_category": "type",  # 基地類別
        "bi_agency": "dept",  # 管理機關
        "bi_unit": "unit",  # 所屬單位
        "bi_address": "addr",
        "bi_longitude": "lng",
        "bi_latitude": "lat",
        "bi_area": "area",  # 可耕作面積
        "bi_method": "method",  # 耕作方式
        "bi_period_s": "start_time",  # 認養期間-開始
        "bi_period_e": "end_time",  # 認養期間-結束
        "bi_introduction": "introduction",
    }
    data = data.rename(columns=col_map)
    # column type
    data["area"] = pd.to_numeric(data["area"], errors="coerce")
    # time
    data["data_time"] = get_tpe_now_time_str()
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["start_time"] = convert_str_to_time_format(data["start_time"], errors="coerce")
    data["end_time"] = convert_str_to_time_format(data["end_time"], errors="coerce")
    # geometry
    lat = data["lat"].astype(float)
    lng = data["lng"].astype(float)
    gdata = add_point_wkbgeometry_column_to_df(data, lng, lat, from_crs=from_crs)
    gdata = gdata.drop(columns=["geometry"])
    # select column
    ready_data = gdata[
        [
            "data_time",
            "name",
            "type",
            "dept",
            "unit",
            "area",
            "method",
            "start_time",
            "end_time",
            "addr",
            "lng",
            "lat",
            "introduction",
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
        geometry_type=geometry_type,
    )
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050301_1")
dag.create_dag(etl_func=_D050301_1)
