from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0075(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Comfig
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=b9f8154d-c627-48a8-b3ef-512ed9cde9e7"
    ENCODING = "utf-8"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)
    is_no_header = raw_data.columns[0] != "序號"
    if is_no_header:
        raw_data = pd.read_csv(
            URL,
            encoding=ENCODING,
            header=None,
            names=[
                "序號",
                "圖號",
                "編號",
                "WPID",
                "97X座標",
                "97Y座標",
                "WGS84經度",
                "WGS84緯度",
                "型式",
                "所在地區",
            ],
        )

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "序號": "rid",
            "圖號": "photo_number",
            "編號": "serial_number",
            "97X座標": "twd97_lng",
            "97Y座標": "twd97_lat",
            "WGS84經度": "wgs84_lng",
            "WGS84緯度": "wgs84_lat",
            "型式": "type",
            "所在地區": "location",
        }
    )
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["wgs84_lng"], data["wgs84_lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "rid",
            "photo_number",
            "serial_number",
            "twd97_lng",
            "twd97_lat",
            "wgs84_lng",
            "wgs84_lat",
            "type",
            "location",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0075")
dag.create_dag(etl_func=_R0075)
