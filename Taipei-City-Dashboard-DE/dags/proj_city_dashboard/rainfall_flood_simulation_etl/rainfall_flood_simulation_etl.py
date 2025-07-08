from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_files_merge
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Load
    GEOMETRY_TYPE = "MultiPolygonZ"
    URL = "https://fhy.wra.gov.tw/disaster/Uploads/Download/%E6%B7%B9%E6%B0%B4%E6%BD%9B%E5%8B%A2%E5%9C%96%E5%9C%96%E7%81%BD%E8%B3%87%E6%96%99/SHP/NewTaipeiCity-SHP.zip"
    raw_data = get_shp_files_merge(URL,dag_id)
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    gdata["area"] = gdata["geometry"].apply(lambda x: x.area).round()
    gdata['city'] = "臺北市"
    gdata = gdata.rename(
        columns={
            "geometry": "wkb_geometry",
        }
    )

    df = gdata[["gridcode","category", "type", "area", "city", "wkb_geometry"]]
    df["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")


    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, df["data_time"].max()
        )
    
dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="rainfall_flood_simulation_etl")
dag.create_dag(etl_func=_transfer)
