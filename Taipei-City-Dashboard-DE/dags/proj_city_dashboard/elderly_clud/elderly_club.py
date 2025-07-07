from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    from utils.extract_stage import get_data_taipei_api
    import pandas as pd
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    # raw_data_db_uri = kwargs.get('raw_data_db_uri')
    # data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    # Manually set
    rid = 'ffab5e5f-4a0f-4759-8531-5302379509cd'
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"
    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    
    # Transform
    # Rename
    data = raw_data.copy()
    data = data.drop(columns=['_id','_importdate'])

    col_map = {
        "據點名稱": "name",
        "行政區": "district",
        "行政區代碼": "zip_code",
        "據點地址": "address",
        "電話": "tel",

    }
    data = data.rename(columns=col_map)
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    # get geometry
    # clean addr
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    # get gis xy
    data["longitude"], data["latitude"] = get_addr_xy_parallel(output)
    # standarlize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "name",
            "district",
            "zip_code",
            "address",
            "tel",
            "longitude",
            "latitude",
            "wkb_geometry",
        ]
    ]


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
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='elderly_club')
dag.create_dag(etl_func=_transfer)
