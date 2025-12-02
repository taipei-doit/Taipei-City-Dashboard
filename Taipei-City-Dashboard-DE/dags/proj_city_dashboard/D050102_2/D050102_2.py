from typing import Any, Literal
from pandas.core.frame import DataFrame
from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050102_2(**kwargs):
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

    def keys_to_lower(obj):
        """Recursively convert all keys in a dict to lowercase."""
        if isinstance(obj, dict):
            return {k.lower(): keys_to_lower(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [keys_to_lower(item) for item in obj]
        else:
            return obj

    # Config
    cwa_api_key = Variable.get("CWA_API_KEY")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-D0047-061?Authorization={cwa_api_key}&format=json"
    CITY = "臺北市"

    # Extract
    res_json: Any | DataFrame | Literal[False] = get_json_file(url, dag_id, is_proxy=False)
    res_json = keys_to_lower(res_json)
    # parse json
    issueTime = res_json["cwaopendata"]["dataset"]["datasetinfo"]["issuetime"]
    updateTime = res_json["cwaopendata"]["dataset"]["datasetinfo"]["update"]
    locdata = res_json["cwaopendata"]["dataset"]["locations"]["location"]
    df_list = []
    for loc in locdata:
        temp = {}
        temp["city"] = CITY
        temp["dist"] = loc["locationname"]
        for we in loc["weatherelement"]:
            temp["item"] = we["elementname"].lower()
            # temp['desc'] = we['description']
            seq = 0
            for ele in we["time"]:
                temp["seq"] = seq
                seq += 1
                if isinstance(ele["elementvalue"], dict):
                    ev_values = list(ele["elementvalue"].values())
                    if len(ev_values) == 1:
                        # 單一值
                        temp["value"] = ev_values[0]
                        if ele.get(
                            "datatime"
                        ):  # some data are not in a period from start to end
                            temp["start_time"] = ele["datatime"]
                            temp["end_time"] = ele["datatime"]
                        else:
                            temp["start_time"] = ele["starttime"]
                            temp["end_time"] = ele["endtime"]
                        df_list.append(temp.copy())
                    else:
                        # 多個值，每個值都要單獨處理
                        a = 0
                        for ev_val in ev_values:
                            temp["item"] = (
                                we["elementname"].lower() + "_" + str(a)
                            )  # 多個value要改名稱
                            temp["value"] = ev_val
                            if ele.get("datatime"):
                                temp["start_time"] = ele["datatime"]
                                temp["end_time"] = ""
                            else:
                                temp["start_time"] = ele["starttime"]
                                temp["end_time"] = ele["endtime"]
                            df_list.append(temp.copy())
                            a += 1
                elif isinstance(ele["elementvalue"], list):
                    a = 0
                    for ele_value in ele["elementvalue"]:
                        temp["item"] = (
                            we["elementname"].lower() + "_" + str(a)
                        )  # 多個value要改名稱
                        temp["value"] = list(ele_value.values())[0] if isinstance(ele_value, dict) else ele_value
                        if ele.get("datatime"):
                            temp["start_time"] = ele["datatime"]
                            temp["end_time"] = ""
                        else:
                            temp["start_time"] = ele["starttime"]
                            temp["end_time"] = ele["endtime"]
                        df_list.append(temp.copy())
                        a += 1
                else:
                    raise ValueError("Unexpected tpye in ele['elementValue'].")
    raw_data = pd.DataFrame(df_list)

    # Transform
    data = raw_data.copy()
    # rename
    col_map = {
        "t": "temperature",
        "td": "temperature_dew",
        "rh": "humidity",
        "pop6h": "rainfall_probability_6hour",
        "pop12h": "rainfall_probability_12hour",
        "wd": "wind_direction",
        "ws_0": "wind_speed",
        "ws_1": "wind_speed_level",
        "ci_0": "comfort",
        "ci_1": "comfort_level",
        "at": "temperature_body",
        "wx_0": "weather",
        "wx_1": "weather_code",
        "weatherdescription": "weather_summary",
    }
    for raw_col, new_col in col_map.items():
        is_target = data["item"] == raw_col
        data.loc[is_target, "item"] = new_col
        if raw_col == "ws_1":
            data.loc[is_target, "value"] = data.loc[is_target, "value"] + "級"
    # -99被用來表示無資料，全改成None
    data = data.applymap(given_string_to_none, given_str="-99")
    # define column type
    data["seq"] = data["seq"].astype(int)
    # time
    data["start_time"] = convert_str_to_time_format(data["start_time"])
    data["end_time"] = convert_str_to_time_format(data["end_time"])
    data["data_time"] = updateTime
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # restructure data by time
    # Because the original data is not aligned, the temperature is every hour, a total of 24;
    # the rainfall forecast for every 12 hours is only 6.
    res = []
    for _g, gdata in data.groupby(["data_time", "city", "dist"]):
        data_time = _g[0]
        city = _g[1]
        dist = _g[2]
        for seq in range(0, 24):
            # other attr
            is_seq = gdata["seq"] == seq
            classic = gdata.loc[is_seq & (gdata["item"] == "weather")]
            start_time = classic["start_time"].iloc[0]
            end_time = classic["end_time"].iloc[0]
            # weather attr
            comfort = gdata.loc[is_seq & (gdata["item"] == "comfort"), "value"].iloc[0]
            comfort_level = gdata.loc[
                is_seq & (gdata["item"] == "comfort_level"), "value"
            ].iloc[0]
            humidity = gdata.loc[is_seq & (gdata["item"] == "humidity"), "value"].iloc[
                0
            ]
            temperature = gdata.loc[
                is_seq & (gdata["item"] == "temperature"), "value"
            ].iloc[0]
            temperature_body = gdata.loc[
                is_seq & (gdata["item"] == "temperature_body"), "value"
            ].iloc[0]
            temperature_dew = gdata.loc[
                is_seq & (gdata["item"] == "temperature_dew"), "value"
            ].iloc[0]
            weather = gdata.loc[is_seq & (gdata["item"] == "weather"), "value"].iloc[0]
            weather_code = gdata.loc[
                is_seq & (gdata["item"] == "weather_code"), "value"
            ].iloc[0]
            weather_summary = gdata.loc[
                is_seq & (gdata["item"] == "weather_summary"), "value"
            ].iloc[0]
            wind_direction = gdata.loc[
                is_seq & (gdata["item"] == "wind_direction"), "value"
            ].iloc[0]
            wind_speed = gdata.loc[
                is_seq & (gdata["item"] == "wind_speed"), "value"
            ].iloc[0]
            wind_speed_level = gdata.loc[
                is_seq & (gdata["item"] == "wind_speed_level"), "value"
            ].iloc[0]
            twelve_seq = seq // 4
            is_twelve = (gdata["seq"] == twelve_seq) & (
                gdata["item"] == "rainfall_probability_12hour"
            )
            rainfall_probability_12hour = gdata.loc[is_twelve, "value"].iloc[0]
            six_seq = seq // 2
            is_six = (gdata["seq"] == six_seq) & (
                gdata["item"] == "rainfall_probability_6hour"
            )
            rainfall_probability_6hour = gdata.loc[is_six, "value"].iloc[0]
            # reshape
            temp_res = [
                data_time,
                city,
                dist,
                seq,
                start_time,
                end_time,
                weather,
                weather_code,
                weather_summary,
                temperature,
                temperature_body,
                temperature_dew,
                humidity,
                comfort,
                comfort_level,
                wind_direction,
                wind_speed,
                wind_speed_level,
                rainfall_probability_6hour,
                rainfall_probability_12hour,
            ]
            res.append(temp_res)
    ready_data = pd.DataFrame(res)
    # select column
    ready_data.columns = [
        "data_time",
        "city",
        "dist",
        "seq",
        "start_time",
        "end_time",
        "weather",
        "weather_code",
        "weather_summary",
        "temperature",
        "temperature_body",
        "temperature_dew",
        "humidity",
        "comfort",
        "comfort_level",
        "wind_direction",
        "wind_speed",
        "wind_speed_level",
        "rainfall_probability_6hour",
        "rainfall_probability_12hour",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050102_2")
dag.create_dag(etl_func=_D050102_2)
