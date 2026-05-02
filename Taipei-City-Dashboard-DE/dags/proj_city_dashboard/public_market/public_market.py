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
    csv_path = f"{DAG_PATH}/utils/opendata/夜市/taipei_market.csv"
    raw_data = pd.read_csv(csv_path, encoding="big5")

    # Transform
    data = raw_data.rename(columns={
        "序號": "seq",
        "行政區": "district",
        "市場名稱": "name",
        "總計": "total_stalls",
        "蔬菜（數量）": "vegetable",
        "青果（數量）": "fruit",
        "獸肉（數量）": "meat",
        "漁產（數量）": "seafood",
        "家禽（數量）": "poultry",
        "糧食（數量）": "grain",
        "花卉（數量）": "flower",
        "雜貨（數量）": "grocery",
        "百貨（數量）": "department",
        "飲食（數量）": "food_drink",
        "其他": "other",
    })

    # 數值欄位可能有千分位逗號
    numeric_cols = [
        "total_stalls", "vegetable", "fruit", "meat", "seafood",
        "poultry", "grain", "flower", "grocery", "department",
        "food_drink", "other",
    ]
    for col in numeric_cols:
        data[col] = (
            data[col].astype(str).str.replace(",", "").pipe(pd.to_numeric, errors="coerce")
        )

    # 用「臺北市 + 行政區 + 市場名稱」組合地址進行地理編碼
    data["address"] = "臺北市" + data["district"] + data["name"]
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
        "data_time", "seq", "district", "name", "address",
        "total_stalls", "vegetable", "fruit", "meat", "seafood",
        "poultry", "grain", "flower", "grocery", "department",
        "food_drink", "other", "lng", "lat", "wkb_geometry",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="public_market")
dag.create_dag(etl_func=_transfer)
