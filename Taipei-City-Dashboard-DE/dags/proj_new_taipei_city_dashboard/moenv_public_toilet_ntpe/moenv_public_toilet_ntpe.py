from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_moenv_json_data
    from utils.get_time import get_tpe_now_time
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    DATASET_CODE = "fac_p_21"
    now_time = get_tpe_now_time(is_with_tz=True)
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    res = get_moenv_json_data(
        DATASET_CODE, filters_query=None, is_proxy=True, timeout=None
    )
    raw_data = pd.DataFrame(res)

    # Transform
    data = raw_data.copy()
    data["data_time"] = convert_str_to_time_format(now_time)
    # standardize geomettry
    data["lng"] = data["longitude"]
    data["lat"] = data["latitude"]
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["longitude"], data["latitude"], from_crs=FROM_CRS
    )
    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=gdata,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    # Update lasttime_in_data
    lasttime_in_data = gdata["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="moenv_public_toilet_ntpe")
dag.create_dag(etl_func=_transfer)
