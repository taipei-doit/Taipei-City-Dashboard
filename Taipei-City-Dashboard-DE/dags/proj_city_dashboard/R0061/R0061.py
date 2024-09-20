from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0061(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
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
    URL = "https://hms.udd.gov.taipei/api/BigData/project"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res = requests.get(URL, timeout=30)
    res.raise_for_status()
    res_json = res.json()
    raw_data = pd.DataFrame(res_json)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    # define column type
    data["households"] = pd.to_numeric(data["households"], errors="coerce")
    data["persons"] = pd.to_numeric(data["persons"], errors="coerce")
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "name",
            "distict",
            "address",
            "households",
            "persons",
            "floors",
            "progress",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0061")
dag.create_dag(etl_func=_R0061)
