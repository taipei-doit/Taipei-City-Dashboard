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
    # rename - 新 API 使用中文欄位名稱
    col_map = {
        "溫度": "temperature",
        "露點溫度": "temperature_dew",
        "相對濕度": "humidity",
        "3小時降雨機率": "rainfall_probability_6hour",
        "風向": "wind_direction",
        "風速_0": "wind_speed",
        "風速_1": "wind_speed_level",
        "舒適度指數_0": "comfort",
        "舒適度指數_1": "comfort_level",
        "體感溫度": "temperature_body",
        "天氣現象_0": "weather",
        "天氣現象_1": "weather_code",
        "天氣預報綜合描述": "weather_summary",
    }
    for raw_col, new_col in col_map.items():
        is_target = data["item"] == raw_col
        data.loc[is_target, "item"] = new_col
        if raw_col == "風速_1":
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
    # 新 API 結構：以天氣現象的時間點為基準（32個時間點，每3小時）
    # 溫度等有更多時間點，需要對應匹配
    res = []
    for _g, gdata in data.groupby(["data_time", "city", "dist"]):
        data_time = _g[0]
        city = _g[1]
        dist = _g[2]
        
        # 以天氣現象的時間點為基準
        weather_data = gdata[gdata["item"] == "weather"].sort_values("start_time")
        max_seq = len(weather_data)
        
        for seq in range(max_seq):
            is_seq = gdata["seq"] == seq
            
            # 取得該 seq 的時間範圍
            weather_row = gdata.loc[is_seq & (gdata["item"] == "weather")]
            if weather_row.empty:
                continue
            start_time = weather_row["start_time"].iloc[0]
            end_time = weather_row["end_time"].iloc[0]
            
            # 取得各項天氣資訊（使用相同 seq）
            def get_value(item_name, default=None):
                matched = gdata.loc[is_seq & (gdata["item"] == item_name), "value"]
                return matched.iloc[0] if not matched.empty else default
            
            weather = get_value("weather")
            weather_code = get_value("weather_code")
            weather_summary = get_value("weather_summary")
            temperature = get_value("temperature")
            temperature_body = get_value("temperature_body")
            temperature_dew = get_value("temperature_dew")
            humidity = get_value("humidity")
            comfort = get_value("comfort")
            comfort_level = get_value("comfort_level")
            wind_direction = get_value("wind_direction")
            wind_speed = get_value("wind_speed")
            wind_speed_level = get_value("wind_speed_level")
            rainfall_probability = get_value("rainfall_probability_6hour")
            
            # reshape - 保留原有欄位結構，rainfall_probability_12hour 設為與 6hour 相同
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
                rainfall_probability,
                rainfall_probability,  # 12hour 使用相同值
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
