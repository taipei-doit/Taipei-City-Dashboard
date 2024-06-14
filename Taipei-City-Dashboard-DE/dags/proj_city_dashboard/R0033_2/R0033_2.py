from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0033_2(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=d417e957-7205-451e-bf45-a31db78f6ec8"
    ENCODING = "cp950"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "項次": "id",
            "場所名稱": "place",
            "場所地址": "address",
            "違規項目": "violation_item",
            "場所用途": "place_usage",
            "檢查日期": "date",
        }
    )
    # time
    data["date"] = data["date"].astype(str)
    data["date"] = convert_str_to_time_format(data["date"], from_format="%TY%m%d")
    # geocoding
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    x, y = get_addr_xy_parallel(output)
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata[
        [
            "id",
            "place",
            "address",
            "violation_item",
            "place_usage",
            "date",
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
    lasttime_in_data = gdata["date"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0033_2")
dag.create_dag(etl_func=_R0033_2)
