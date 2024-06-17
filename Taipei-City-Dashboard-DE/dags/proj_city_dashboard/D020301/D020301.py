from airflow import DAG
from operators.common_pipeline import CommonDag


def _D020301(**kwargs):
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    import requests
    from geopandas.tools import sjoin
    from settings.global_config import PROXIES
    from shapely import wkt
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://itsapi.taipei.gov.tw/TPTS_API/roadInformation/CCTVByLBS"
    PAY_LOAD = {
        "distance": 10000000,
        "lng": 121.460477,
        "lat": 25.019086,
        "language": "ZH",
    }
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    res = requests.post(URL, data=PAY_LOAD, proxies=PROXIES)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    raw_data = pd.DataFrame(res_json["locations"])
    raw_data["data_tme"] = get_tpe_now_time_str()

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "cctvId": "id",
            "cctvName": "name",
            "lat": "lat",
            "lng": "lng",
            "roadType": "road_type",
            "videoStreamURL": "stream_url",
            "videoPreviewImgUrl": "preview_img_url",
            "data_tme": "data_time",
        }
    )
    # split sequence and name
    data["id"] = data["id"].astype(str)
    data["name"] = data["name"].str.split("-").str[1:].str.join("-")
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    # add county, town
    engine = create_engine(ready_data_db_uri)
    sql = "SELECT tname AS town, ST_ASTEXT(wkb_geometry) AS geometry FROM public.tp_district"
    town = pd.read_sql(sql, engine)
    town["geometry"] = town["geometry"].apply(wkt.loads)
    town = gpd.GeoDataFrame(town, geometry="geometry", crs="EPSG:4326")
    gdata = sjoin(gdata, town, how="left", op="within")
    # add county
    gdata["county"] = np.where(gdata["town"].isna(), "新北市", "臺北市")
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "county",
            "town",
            "id",
            "name",
            "road_type",
            "stream_url",
            "preview_img_url",
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
    update_lasttime_in_data_to_dataset_info(engine, dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D020301")
dag.create_dag(etl_func=_D020301)
