from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0081(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Comfig
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=d1f9c6e0-5f72-4fc4-ac18-0b75ce0b002e"
    ENCODING = "utf-8"
    PAGE_ID = "026cc0fa-cecc-4c78-b986-ead3b0c8b95b"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "站名": "name",
            "河系": "river",
            "行政區域": "dist",
            "建置日期": "create_date",
            "X坐標": "twd97_lng",
            "Y坐標": "twd97_lat",
        }
    )
    # time
    data["create_date"] = convert_str_to_time_format(
        data["create_date"], from_format="%Y%m%d"
    )
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["twd97_lng"], data["twd97_lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "name",
            "river",
            "dist",
            "create_date",
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
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0081")
dag.create_dag(etl_func=_R0081)
