from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from settings.global_config import DAG_PATH
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    xlsx_path = f"{DAG_PATH}/utils/opendata/溯源餐廳/台北市溯源餐廳.xlsx"
    raw_data = pd.read_excel(xlsx_path)

    col_map = {
        "餐廳名稱": "name",
        "地址": "address",
        "電話": "tel",
        "料理種類": "cuisine_type",
        "星級數": "star_rating",
    }
    data = raw_data.rename(columns=col_map)

    data["star_rating"] = data["star_rating"].apply(lambda x: "★" * int(x))
    data["district"] = data["address"].str.extract(r"[台臺]北市(\S{2,3}區)")
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    data["longitude"], data["latitude"] = get_addr_xy_parallel(output)

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )

    ready_data = gdata[
        [
            "data_time",
            "district",
            "name",
            "cuisine_type",
            "star_rating",
            "tel",
            "address",
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
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="traceable_restaurant")
dag.create_dag(etl_func=_transfer)
