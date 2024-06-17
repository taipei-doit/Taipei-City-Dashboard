from airflow import DAG
from operators.common_pipeline import CommonDag


def D030104_2(**kwargs):
    import json

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_mixed_type import mapping_category_ignore_number
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
    GEOMETRY_TYPE = "Point"
    file_name = f"{dag_id}.json"
    FROM_CRS = 3826

    # Extract
    local_file = download_file(file_name, URL, is_proxy=True)
    with open(local_file) as json_file:
        res = json.load(json_file)
    update_time = res["data"]["UPDATETIME"]
    raw_data = pd.DataFrame(res["data"]["park"])

    # Transfrom
    # colname
    data = raw_data.copy()
    data.columns = data.columns.str.lower()
    col_map = {
        "id": "station_id",
        "area": "dist",
        "name": "name",
        "type": "data_return_type",  # 1:動態停車場(可取得目前剩餘車位數) 2:靜態停車場、
        "type2": "owner_type",  # 1:停管處經營 2:非停管處經營
        "summary": "summary",
        "address": "addr",
        "tel": "tel",
        "payex": "pay_info",  # 停車場收費資訊
        "servicetime": "opening_time",  # 開放時間
        "tw97x": "x_97",
        "tw97y": "y_97",
        "totalcar": "total_car",  # 汽車總車位數
        "totalmotor": "total_motor",  # 機車總車位數
        "totalbike": "total_bike",  # 腳踏車總車位數
        "totalbus": "total_bus",  # 大客車總車位數
        "pregnancy_first": "pregnancy_first_count",  # 孕婦優先車格位數
        "handicap_first": "handicap_first_count",  # 身障車格位數
        "taxi_onehr_free": "taxi_onehr_free_count",
        "aed_equipment": "aed_equipment",
        "cellsignal_enhancement": "cellsignal_enhancement",
        "accessibility_elevator": "accessibility_elevator",
        "phone_charge": "phone_charge",
        "child_pickup_area": "child_pickup_area",
        "fareinfo": "fare_info",  # 費率資訊
        "entrancecoord": "entrance_coord",  # 入口座標資訊
        "totallargemotor": "total_largemotor",  # 重機停車位數
        "chargingstation": "charging_station",  # 充電站數
    }
    data = data.rename(columns=col_map)
    # define str columns
    data["station_id"] = data["station_id"].astype(str)
    data["fare_info"] = data["fare_info"].astype(str)
    data["entrance_coord"] = data["entrance_coord"].astype(str)
    # define float columns
    float_cols = [
        "total_car",
        "total_motor",
        "total_bike",
        "total_bus",
        "total_largemotor",
        "pregnancy_first_count",
        "handicap_first_count",
        "taxi_onehr_free_count",
        "aed_equipment",
        "cellsignal_enhancement",
        "accessibility_elevator",
        "phone_charge",
        "child_pickup_area",
        "charging_station",
    ]
    for col in float_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
    # mapping category
    cate_map = {"1": "動態回傳剩餘車位數", "2": "靜態"}
    data["data_return_type"] = data["data_return_type"].apply(
        mapping_category_ignore_number, cate=cate_map
    )
    cate_map = {"1": "停管處經營", "2": "非停管處經營"}
    data["owner_type"] = data["owner_type"].apply(
        mapping_category_ignore_number, cate=cate_map
    )
    # time
    data["data_time"] = update_time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["x_97"], data["y_97"], from_crs=FROM_CRS
    )
    gdata = gdata.drop(columns=["geometry", "x_97", "y_97"])
    # select column
    ready_data = gdata[
        [
            "data_time",
            "station_id",
            "dist",
            "name",
            "data_return_type",
            "owner_type",
            "summary",
            "addr",
            "tel",
            "pay_info",
            "opening_time",
            "total_car",
            "total_motor",
            "total_bike",
            "total_bus",
            "total_largemotor",
            "pregnancy_first_count",
            "handicap_first_count",
            "taxi_onehr_free_count",
            "aed_equipment",
            "cellsignal_enhancement",
            "accessibility_elevator",
            "phone_charge",
            "child_pickup_area",
            "charging_station",
            "fare_info",
            "entrance_coord",
            "lng",
            "lat",
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
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030104_2")
dag.create_dag(etl_func=D030104_2)
