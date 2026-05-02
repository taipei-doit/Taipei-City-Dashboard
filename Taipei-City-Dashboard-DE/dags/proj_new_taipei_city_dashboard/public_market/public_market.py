from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from settings.global_config import DAG_PATH
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
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326

    # Extract
    csv_path = f"{DAG_PATH}/utils/opendata/夜市/metrotaipei_market.csv"
    raw_data = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Transform
    # 清理 item 欄位的 tab 字元
    raw_data["item"] = raw_data["item"].astype(str).str.replace("\t", "").str.strip()
    raw_data["name"] = raw_data["name"].str.strip()
    raw_data["town"] = raw_data["town"].str.strip()
    raw_data["address"] = raw_data["address"].str.strip()
    raw_data["types"] = raw_data["types"].str.strip()
    raw_data["phone"] = raw_data["phone"].fillna("").str.strip()

    data = raw_data.rename(columns={
        "item": "seq",
        "name": "name",
        "county": "county",
        "town": "district",
        "address": "address",
        "phone": "phone",
        "types": "market_type",
    })
    data = data.drop(columns=["countycode", "areacode"], errors="ignore")

    # 地址標準化與地理編碼
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    _, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output

    lng, lat = get_addr_xy_parallel(output)
    data["lng"] = lng
    data["lat"] = lat
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )

    ready_data = gdata[[
        "data_time", "seq", "name", "county", "district",
        "address", "phone", "market_type",
        "lng", "lat", "wkb_geometry",
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    lasttime_in_data = get_tpe_now_time_str()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="public_market",
)
dag.create_dag(etl_func=_transfer)
