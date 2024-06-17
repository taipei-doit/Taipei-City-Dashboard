from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0051_3(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    city = "Taipei"
    if city == "Taipei":
        url = "https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/Taipei?%24format=JSON"
    elif city == "New Taipei":
        url = "https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/NewTaipei?%24format=JSON"
    else:
        raise ValueError("Invalid city {city}.")

    # Extract
    raw_data = get_tdx_data(url, output_format='dataframe')

    # Transform
    data = raw_data.copy()
    # rename
    col_map = {
        "StationUID": "station_uid",  # 站點唯一識別代碼，規則為 {業管機關代碼} + {StationID}
        "StationID": "station_id",
        "ServiceStatus": "service_status",  #  [0:'停止營運',1:'正常營運',2:'暫停營運']
        "ServiceType": "service_type",  # [1:'YouBike1.0',2:'YouBike2.0',3:'T-Bike',4:'P-Bike',5:'K-Bike']
        "AvailableRentBikes": "available_rent_bikes",  # 可租借車數
        "AvailableReturnBikes": "available_return_bikes",  # 可歸還車數
        "SrcUpdateTime": "data_time",  # 來源端平台資料更新時間
        "UpdateTime": "tdx_update_time",  # TDX資料更新日期時間
        "AvailableRentBikesDetail": "bike_detail",  # 一般自行車可租借車數, 電動輔助車可租借車數
    }
    data = data.rename(columns=col_map)
    # 可租車數，可分解為普通、電動兩種
    data["available_rent_general_bikes"] = data["bike_detail"].apply(
        lambda x: x["GeneralBikes"]
    )
    data["available_rent_electric_bikes"] = data["bike_detail"].apply(
        lambda x: x["ElectricBikes"]
    )
    data = data.drop(columns=["available_rent_bikes", "bike_detail"])
    # define column type
    data["station_id"] = data["station_id"].astype(str)
    # numbers can't be converted to int will be set to -1
    numeric_cols = [
        "available_rent_general_bikes",
        "available_rent_electric_bikes",
        "available_return_bikes",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
        data[col] = data[col].fillna(-1).astype(int)
    # mapping category code to category name
    data["service_status"] = data["service_status"].astype(str)
    status_map = {"0": "停止營運", "1": "正常營運", "2": "暫停營運"}
    data["service_status"] = data["service_status"].map(status_map)
    data["service_type"] = data["service_type"].astype(str)
    type_map = {
        "1": "UBike1.0",
        "2": "UBike2.0",
        "3": "TBike",
        "4": "PBike",
        "5": "KBike",
    }
    data["service_type"] = data["service_type"].map(type_map)
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["tdx_update_time"] = convert_str_to_time_format(data["tdx_update_time"])
    # select column
    ready_data = data[
        [
            "data_time",
            "station_uid",
            "station_id",
            "service_status",
            "service_type",
            "available_rent_general_bikes",
            "available_return_bikes",
            "available_rent_electric_bikes",
            "tdx_update_time",
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
    engine = create_engine(ready_data_db_uri)
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0051_3")
dag.create_dag(etl_func=_R0051_3)
