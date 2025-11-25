from airflow import DAG
from operators.common_pipeline import CommonDag


def _school_reconstruction(**kwargs):
    import requests
    import pandas as pd
    from io import StringIO
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    geometry_type = "Point"
    FROM_CRS = 4326
    URL = 'https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=b14137d5-fde6-4491-8817-2cf5f68ef0cf'
    response = requests.get(URL, verify=False)
    # 讀取 CSV
    df = pd.read_csv(StringIO(response.text))
    # Transform
    
    data = df.rename(columns={
        "_id": "id",
        "學校": "school",
        "計畫名稱": "project_name",
        "行政區": "district",
        "地址": "address",
        "建築類別": "building_type",
        "階段": "stage",
        "地上樓層數": "above_ground_floors",
        "地下樓層數": "underground_floors",
        "工程基地\n緯度": "latitude",
        "工程基地\n經度": "longitude"
    })
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    
    # 清理經緯度資料，確保為數值型態
    data["longitude"] = pd.to_numeric(data["longitude"], errors='coerce')
    data["latitude"] = pd.to_numeric(data["latitude"], errors='coerce')
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[["data_time", "id", "school", "project_name", "district", "address", "building_type", "stage", "above_ground_floors", "underground_floors", "longitude", "latitude", "wkb_geometry"]]

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
    lasttime_in_data = get_tpe_now_time_str()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="school_reconstruction")
dag.create_dag(etl_func=_school_reconstruction)
