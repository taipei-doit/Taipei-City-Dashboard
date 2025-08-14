from airflow import DAG
from operators.common_pipeline import CommonDag


def _general_hotel_registry(**kwargs):
    import requests
    import pandas as pd
    from io import StringIO
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
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
    geometry_type = "Point"
    FROM_CRS = 4326
    URL = 'https://data.taipei/api/dataset/4d7d0b46-2e90-4ee7-b000-c0f2f3a37651/resource/3cea29db-66b1-4ab5-886c-4cafd3e1dcbc/download'
    response = requests.get(URL, verify=False)
    # 讀取 CSV
    df = pd.read_csv(StringIO(response.text))
    # Transform
    
    data = df.rename(columns={
        "專用標識編號": "license_number",
        "旅館名稱": "name",
        "營業地址": "address",
        "電話或手機號碼": "localcall",
        "客房最低定價": "button_price",
        "客房最高定價": "higher_price",
        "房間數": "room"
    })
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    # 資料格式為"108臺北市萬華區昆明街142號7-8樓", 只取區
    area_candidates = data['address'].str.slice(3, 6)
    data['area'] = area_candidates.apply(lambda x: x if x.endswith('區') else None)


    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output


    # get gis xy
    data["longitude"], data["latitude"] = get_addr_xy_parallel(output)
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[["data_time", "license_number", "name", "address", "localcall", "button_price", "higher_price", "room", "area", "longitude", "latitude", "wkb_geometry"]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )
    lasttime_in_data = get_tpe_now_time_str()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="general_hotel_registry")
dag.create_dag(etl_func=_general_hotel_registry)
