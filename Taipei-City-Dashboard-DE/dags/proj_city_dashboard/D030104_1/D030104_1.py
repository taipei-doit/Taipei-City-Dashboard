from airflow import DAG
from operators.common_pipeline import CommonDag


def D030104_1(**kwargs):
    import json

    import pandas as pd
    from numpy import nan
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_allavailable.json"
    file_name = f"{dag_id}.json"

    # Extract
    local_file = download_file(file_name, URL, is_proxy=True)
    with open(local_file) as json_file:
        res = json.load(json_file)
    raw_data = pd.DataFrame(res["data"]["park"])
    update_time = res["data"]["UPDATETIME"]

    # Transfrom
    """
    ALT_PAK1：依由近而遠之距離提供滿場替代停車場ID編號、
    ALT_PAK2：依由近而遠之距離提供滿場替代停車場ID編號、
    ALT_PAK3：依由近而遠之距離提供滿場替代停車場ID編號 
    scoketStatusList：充電座狀態集、
    spot_abrv：充電座編號、
    spot_status：充電座狀態'
    availablecar: 停車場（汽車）之剩餘車位數，數值等於-9，表示本停車場目前無法提供即時車位數資訊。
    availablemotor: 停車場（機車）之剩餘格位數，數值等於-9，表示本停車場目前無法提供即時格位數資訊。
    availablebus: 停車場（大客車）之剩餘車位數，數值等於-9，表示本停車場目前無法提供即時車位數資訊。
    """
    # colname
    data = raw_data.copy()
    data.columns = data.columns.str.lower()
    col_map = {
        "id": "station_id",
        "availablecar": "available_car",
        "availablemotor": "available_motor",
        "availablebus": "available_bus",
    }
    data = data.rename(columns=col_map)
    # cleansing
    charge_station = [
        [] if pd.isna(json) else json["scoketStatusList"]
        for json in data["chargestation"].tolist()
    ]
    data["charge_spot"] = [
        [spot["spot_abrv"] for spot in s_detail if spot["spot_status"] == "充電中"]
        for s_detail in charge_station
    ]
    data["charge_spot_count"] = data["charge_spot"].apply(len)
    data["standby_spot"] = [
        [spot["spot_abrv"] for spot in s_detail if spot["spot_status"] == "待機中"]
        for s_detail in charge_station
    ]
    data["standby_spot_count"] = data["standby_spot"].apply(len)
    # column type
    data["id"] = data["station_id"].astype(str)
    # missing value
    data.loc[data["available_car"] == -9, "available_car"] = nan
    data.loc[data["available_motor"] == -9, "available_motor"] = nan
    data.loc[data["available_bus"] == -9, "available_bus"] = nan
    # time
    data["data_time"] = update_time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # select column
    ready_data = data[
        [
            "data_time",
            "station_id",
            "available_car",
            "available_motor",
            "available_bus",
            "charge_spot_count",
            "standby_spot_count",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030104_1")
dag.create_dag(etl_func=D030104_1)
