from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0031(**kwargs):
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

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=a90ae184-c39e-4242-b2d6-d7a0403c0632"
    ENCODING = "UTF-8"
    PAGE_ID = "6c41536a-3ce2-4102-bdfc-6b5f3d13ef91"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(columns={"name": "station", "poi_addr": "address"})
    # geocoding
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    x, y = get_addr_xy_parallel(output)
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata[["data_time", "station", "address", "content", "wkb_geometry"]]

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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0031")
dag.create_dag(etl_func=_R0031)
