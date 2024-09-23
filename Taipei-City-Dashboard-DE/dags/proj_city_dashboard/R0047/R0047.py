from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0047(**kwargs):
    import json

    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
        drop_duplicated_after_saving,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    user_name = Variable.get("MRT_API_USER_NAME")
    password = Variable.get("MRT_API_PASSWORD")
    URL = "https://api.metro.taipei/metroapi/TUIC_TRTCOD.asmx"
    HEADERS = {
        "Connection": "keep-alive",
        "Content-Type": "text/xml;charset=utf-8",
        "Cookie": "TS01232bc6=0110b39faef392bacaf437f170d451d71a9e16444c0f2a772a60e76a013d50a51f9ce35839a015c0018de39c5554afda08544542c0",
    }
    payload = (
        '<?xml version="1.0" encoding="utf-8"?> '
        + '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        + 'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        + 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"> '
        + "<soap:Body> "
        + '<getTUIC_OD xmlns="http://tempuri.org/"> '
        + f"<userName>{user_name}</userName> "
        + f"<passWord>{password}</passWord> "
        + "</getTUIC_OD> </soap:Body> </soap:Envelope>"
    )
    TIME_OUT = 60

    # Extract
    res = requests.post(
        URL, headers=HEADERS, data=payload, proxies=proxies, timeout=TIME_OUT
    )
    res.raise_for_status()
    res_text = res.text
    r_split = res_text.split("<getTUIC_ODResult>")[1]
    r_split = r_split.split("</getTUIC_ODResult>")[0]
    r_data = json.loads(json.loads(r_split))
    raw_data = pd.DataFrame(r_data)
    if raw_data.empty:
        print("data is empty")
        return

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "STATIONID": "station_id",
            "PARM_LINENAME": "parm_line_name",
            "PARM_ALIASNAME": "parm_alias_name",
            "INCOUNT": "in_count",
            "OUTCOUNT": "out_count",
            "sDateTime": "data_time",
        }
    )
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # select columns
    ready_data = data[
        [
            "data_time",
            "station_id",
            "parm_line_name",
            "parm_alias_name",
            "in_count",
            "out_count",
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
    drop_duplicated_after_saving(
        engine,
        psql_table=history_table,
        criterion="AND a.station_id = b.station_id AND a.data_time = b.data_time",
        comparing_col="ogc_fid",
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0047")
dag.create_dag(etl_func=_R0047)
