from airflow import DAG
from operators.common_pipeline import CommonDag


def _D090100_1(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
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
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=28c5792b-3af6-4bff-8ad8-f5b5e53d4062"
    ENCODING = "big5"
    PAGE_ID = "58b4f7b9-d0c5-4de8-aa7f-981fcb625e45"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)
    raw_data = raw_data.loc[
        raw_data["school"].notnull(), ~raw_data.columns.str.startswith("Unnamed")
    ]
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID, rank=0)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "data_time": "data_time",
            "school": "type",
            "schoolname": "name",
            "postalcode": "postalcode",
            "address": "addr",
            "telephone": "phone",
        }
    )
    # define column type
    data["postalcode"] = data["postalcode"].astype(float).astype(int).astype(str)
    # standarlize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # get geometry
    # clean addr
    addr = data["addr"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["addr"] = output
    # get gis xy
    data["lng"], data["lat"] = get_addr_xy_parallel(output)
    # standarlize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "name",
            "type",
            "phone",
            "postalcode",
            "addr",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D090100_1")
dag.create_dag(etl_func=_D090100_1)
