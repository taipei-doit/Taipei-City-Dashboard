from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050401_1(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_geojson_file
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://soil.taipei/Taipei/Main/pages/TPLiquid_84.GeoJSON"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiPolygon"

    # Extract
    raw_data = get_geojson_file(URL, dag_id, FROM_CRS)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={"class": "class", "geometry": "geometry", "data_time": "data_time"
    })
    # define column type
    data["class"] = data["class"].astype(str)
    data["class"] = data["class"].map({"1": "高", "2": "中", "3": "低"})
    # standarlize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standarlize geometry
    gdata = convert_geometry_to_wkbgeometry(data, from_crs=FROM_CRS)
    # select column
    ready_data = gdata[["data_time", "class", "wkb_geometry"]]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050401_1")
dag.create_dag(etl_func=_D050401_1)
