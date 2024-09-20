from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0034(**kwargs):
    import geopandas as gpd
    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format

    # Config
    proxies = kwargs.get("proxies")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    login_id = Variable.get("HEO_ID")
    data_key = Variable.get("HEO_APIKEY")
    URL = f"https://wic.heo.taipei/OpenData/API/Sewer/Get?stationNo=&loginId={login_id}&dataKey={data_key}"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    res = requests.get(URL, proxies=proxies, timeout=30)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    raw_data = pd.DataFrame(res_json["data"])

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "stationNo": "station_no",
            "stationName": "station_name",
            "levelOut": "level_out",
            "groundFar": "ground_far",
        }
    )
    # time
    data["data_time"] = convert_str_to_time_format(
        data["recTime"], from_format="%Y%m%d%H%M"
    )
    # join sewer_location to get point geometry by key
    # get sewer_location data
    engine = create_engine(ready_data_db_uri)
    sql = """
        SELECT "站碼" AS station_no,
            "行政區" AS district,
            "經度" AS lng,
            "緯度" AS lat,
            ST_AsText(wkb_geometry) as geometry 
        FROM work_sewer_location
    """
    sewer_location = pd.read_sql(sql, con=engine)
    sewer_location["geometry"] = gpd.GeoSeries.from_wkt(
        sewer_location["geometry"], crs=f"EPSG:{FROM_CRS}"
    )
    # join table
    join_data = data.merge(sewer_location, how="left", on="station_no")
    # standardize geometry
    gdata = gpd.GeoDataFrame(join_data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "station_no",
            "station_name",
            "district",
            "level_out",
            "ground_far",
            "voltage",
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
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0034")
dag.create_dag(etl_func=_R0034)
