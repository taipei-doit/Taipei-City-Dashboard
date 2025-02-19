from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0051_4(**kwargs):
    import geopandas as gpd
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from geoalchemy2 import WKTElement
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    proxies = kwargs.get("proxies")
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    res = requests.get(url, timeout=60)
    res.raise_for_status()
    res_json = res.json()
    raw_data = pd.DataFrame(res_json)

    # Transform
    data = raw_data.copy()
    data = data.drop_duplicates(subset=["sno", "mday"], keep="last").reset_index(
        drop=True
    )

    data = data.rename(columns={"srcUpdateTime": "data_time"})
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )

    ready_data = gdata[["sno", "sna", "data_time", "wkb_geometry"]]

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
    engine = create_engine(ready_data_db_uri)
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0051_4")
dag.create_dag(etl_func=_R0051_4)
