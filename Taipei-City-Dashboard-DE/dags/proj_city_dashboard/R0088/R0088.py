from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0088(**kwargs):
    from datetime import datetime, timedelta, timezone

    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format
    import ast

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    user_name = Variable.get("MRT_BR_API_USER_NAME")
    password = Variable.get("MRT_BR_API_PASSWORD")
    URL = "https://api.metro.taipei/metroapi/CarWeightBR.asmx"
    HEADERS = {
        "Connection": "keep-alive",
        "Content-Type": "text/xml;charset=utf-8",
        "Cookie": "TS01232bc6=0110b39faef392bacaf437f170d451d71a9e16444c0f2a772a60e76a013d50a51f9ce35839a015c0018de39c5554afda08544542c0",
    }
    PAYLOAD = (
        '<?xml version="1.0" encoding="utf-8"?> '
        + '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        + 'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        + 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"> '
        + "<soap:Body> "
        + '<getCarWeightBRInfo xmlns="http://tempuri.org/"> '
        + f"<userName>{user_name}</userName> "
        + f"<passWord>{password}</passWord> "
        + "</getCarWeightBRInfo> </soap:Body> </soap:Envelope>"
    )
    TIME_OUT = 60

    # Extract
    res = requests.post(
        URL, headers=HEADERS, data=PAYLOAD, proxies=proxies, timeout=TIME_OUT
    )
    res.raise_for_status()
    res_text = res.text
    r_split = res_text.split("<getCarWeightBRInfoResult>")[1]
    r_split: str = r_split.split("</getCarWeightBRInfoResult>")[0]

    res_json = ast.literal_eval(r_split)
    raw_data = pd.DataFrame(res_json)
    if raw_data.empty:
        print("data is empty")
        return

    data = raw_data.copy()
    data.columns = data.columns.str.lower()
    data["stationname"] = data["stationid"].copy()
    # define columns
    str_cols = ["cid", "trainnumber", "stationid", "stationname", "cn1"]
    for col in str_cols:
        data[col] = data[col].astype(str)
    num_cols = ["car1", "car2", "car3", "car4"]
    for col in num_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    # time
    data["data_time"] = data["updatetime"]
    # select columns
    ready_data = data[
        [
            "data_time",
            "cid",
            "trainnumber",
            "stationid",
            "stationname",
            "cn1",
            "car1",
            "car2",
            "car3",
            "car4",
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
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0088")
dag.create_dag(etl_func=_R0088)
