from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0083(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_folder = kwargs.get("data_folder")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "586e5233-aa60-4680-8ac1-cbb9ef7f7fde"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    # data time
    data["data_time"] = data["_importdate"].apply(lambda x: x["date"])
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["經度"], data["緯度"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        ["data_time", "行政區", "站碼", "站名", "經度", "緯度", "wkb_geometry"]
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
    # Update lasttime_in_data
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0083")
dag.create_dag(etl_func=_R0083)
