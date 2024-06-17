from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0038_1(**kwargs):
    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    proxies = kwargs.get("proxies")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    token = Variable.get("ROAD_SECTION_INFO_TOKEN")
    url = f"https://www.ttcx.dot.gov.taipei/cpt/api/TaipeiRoadsectionInfoAll?$format=json&$top=100&$token={token}"

    # Extract
    res = requests.get(url, timeout=30)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    raw_data = pd.DataFrame(res_json)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "noData": "no_data",
            "isSlow": "is_slow",
            "isMiddle": "is_middle",
            "isFast": "is_fast",
            "infoTime": "info_time",
            "infoDate": "info_date",
        }
    )
    # time
    data["info_time"] = convert_str_to_time_format(data["info_time"])
    # select columns
    ready_data = data

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    lasttime_in_data = data["info_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0038_1")
dag.create_dag(etl_func=_R0038_1)
