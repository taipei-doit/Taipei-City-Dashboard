from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050102_1(**kwargs):
    import pandas as pd
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.extract_stage import get_json_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_mixed_type import given_string_to_none
    from utils.transform_time import convert_str_to_time_format

    # Config
    cwa_api_key = Variable.get("CWA_API_KEY")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={cwa_api_key}&format=json"

    # Extract
    res_json = get_json_file(url, dag_id, is_proxy=True)
    # parse json
    issueTime = res_json["cwaopendata"]["dataset"]["datasetInfo"]["issueTime"]
    updateTime = res_json["cwaopendata"]["dataset"]["datasetInfo"]["update"]
    locdata = res_json["cwaopendata"]["dataset"]["location"]
    df_list = []
    for loc in locdata:
        temp = {}
        temp["city"] = loc["locationName"]
        for we in loc["weatherElement"]:
            temp["item"] = we["elementName"].lower()
            seq = 0
            for ele in we["time"]:
                temp["seq"] = seq
                seq += 1
                temp["value"] = ele["parameter"]["parameterName"]
                temp["start_time"] = ele["startTime"]
                temp["end_time"] = ele["endTime"]
                # print(temp)
                df_list.append(temp.copy())
    raw_data = pd.DataFrame(df_list)
    raw_data = raw_data.pivot(
        index=["city", "start_time", "end_time", "seq"], columns="item", values="value"
    ).reset_index()

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "ci": "comfort",
            "maxt": "max_temperature",
            "mint": "min_temperature",
            "pop": "rainfall_probability",
            "wx": "weather",
        }
    )
    # -99 used to represent no data, convert to None
    data = data.applymap(given_string_to_none, given_str="-99")
    # define column type
    data["seq"] = data["seq"].astype(int)
    data["max_temperature"] = pd.to_numeric(data["max_temperature"], errors="coerce")
    data["min_temperature"] = pd.to_numeric(data["min_temperature"], errors="coerce")
    data["rainfall_probability"] = pd.to_numeric(
        data["rainfall_probability"], errors="coerce"
    )
    # time
    data["start_time"] = convert_str_to_time_format(data["start_time"])
    data["end_time"] = convert_str_to_time_format(data["end_time"])
    data["data_time"] = updateTime  # convet to pd.series
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # select column
    ready_data = data[
        [
            "data_time",
            "city",
            "seq",
            "weather",
            "min_temperature",
            "max_temperature",
            "rainfall_probability",
            "comfort",
            "start_time",
            "end_time",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050102_1")
dag.create_dag(etl_func=_D050102_1)
