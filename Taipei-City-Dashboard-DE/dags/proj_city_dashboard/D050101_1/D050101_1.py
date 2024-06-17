from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050101_1(**kwargs):
    import json
    from datetime import timedelta

    import pandas as pd
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_mixed_type import mapping_category_ignore_number
    from utils.transform_time import convert_str_to_time_format

    def get_end_date(metadata):
        end_time = metadata["temporal"]["endTime"]
        return end_time.split("T")[0]

    def get_cat_map(metadata):
        "Value category of each element."
        weather_element = metadata["weatherElements"]["weatherElement"]
        cate_map = {}
        for item in weather_element:
            temp = {}
            temp_str = []
            special_values = item["specialValues"]["specialValue"]
            for sv in special_values:
                temp[sv["value"]] = sv["description"]
                temp_str.append(str(sv["value"]) + "=" + str(sv["description"]))
            cate_map[item["tagName"]] = temp
        return cate_map

    def extract_desc_data(metadata, end_date):
        "Description of each weather element."
        weather_element = metadata["weatherElements"]["weatherElement"]
        desc = {"name": [], "desc": [], "units": [], "special_values": []}
        for item in weather_element:
            desc["name"].append(item["tagName"])
            desc["desc"].append(item["description"])
            try:
                desc["units"].append(item["units"])
            except KeyError:
                desc["units"].append(None)
            special_values = item["specialValues"]["specialValue"]
            temp = {}
            temp_str = []
            for sv in special_values:
                temp[sv["value"]] = sv["description"]
                temp_str.append(str(sv["value"]) + "=" + str(sv["description"]))
            temp_str = ",".join(temp_str)
            desc["special_values"].append(temp_str)
        desc = pd.DataFrame(desc)
        desc["data_date"] = end_date
        return desc

    def extract_station_data(
        stations, is_drop_old_kaohsiung, old_kaohsiung_id, end_date
    ):
        "Station information."
        station_data = []
        for station in stations:
            station_id = station["station"]["StationID"]
            if is_drop_old_kaohsiung:
                if station_id == old_kaohsiung_id:
                    continue
            station_name = station["station"]["StationName"]
            stat = pd.DataFrame(station["station"], index=[0])
            station_data.append(stat)
        station_data = pd.concat(station_data).reset_index(drop=True)
        station_data["data_date"] = end_date
        return station_data

    def extract_static_data(stations, is_drop_old_kaohsiung):
        "Daily statistics of each station."
        statistic_list = []
        for station in stations:
            station_id = station["station"]["StationID"]
            if is_drop_old_kaohsiung:
                if station_id == old_kaohsiung_id:
                    continue
            station_name = station["station"]["StationName"]
            # daily statistics
            if IS_ONLY_LAST_DAY_DATA:
                statistics = pd.DataFrame(
                    station["stationObsStatistics"]["AirTemperature"]["daily"][-1],
                    index=[0],
                )
            else:
                statistics = pd.DataFrame(
                    station["stationObsStatistics"]["AirTemperature"]["daily"]
                )
            statistics["station_name"] = station_name
            statistic_list.append(statistics)
        statistic_data = pd.concat(statistic_list).reset_index(drop=True)
        return statistic_data

    def extract_observe_data(stations, is_drop_old_kaohsiung):
        "Hourly observe data of each station."
        observe_list = []
        for station in stations:
            station_id = station["station"]["StationID"]
            if is_drop_old_kaohsiung:
                if station_id == old_kaohsiung_id:
                    continue
            station_name = station["station"]["StationName"]
            observes = station["stationObsTimes"]["stationObsTime"]
            obs_results = []
            if IS_ONLY_LAST_DAY_DATA:
                observes = observes[-24:]  # 24 hours
            for obs in observes:
                temp = pd.DataFrame(obs["weatherElements"], index=[0])
                temp["dataTime"] = obs["DataTime"]
                obs_results.append(temp)
            observes = pd.concat(obs_results).reset_index(drop=True)
            observes["station_name"] = station_name
            observe_list.append(observes)
        observe_data = pd.concat(observe_list).reset_index(drop=True)
        return observe_data

    # Config
    cwa_api_key = Variable.get("CWA_API_KEY")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table1, default_table2 = dag_infos.get("ready_data_default_table")
    file_name = f"{dag_id}.json"
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/C-B0024-002?Authorization={cwa_api_key}&format=json"
    # Default True, only keep the last day data. If False, all history observe will be saved.
    IS_ONLY_LAST_DAY_DATA = True
    # 有兩個高雄站(name一樣，id不一樣)，從data來看是2022/1/24開始關掉舊站啟用新站
    # 因此如果只要新的資料，排除舊高雄站資料
    if IS_ONLY_LAST_DAY_DATA:
        is_drop_old_kaohsiung = True
        old_kaohsiung_id = "467440"
    else:
        is_drop_old_kaohsiung = False

    # Extract
    # read file
    local_file = download_file(file_name, url, is_proxy=True)
    with open(local_file) as json_file:
        raw_json = json.load(json_file)
    # extract data
    metadata = raw_json["cwaopendata"]["resources"]["resource"]["metadata"]
    stations = raw_json["cwaopendata"]["resources"]["resource"]["data"]["surfaceObs"][
        "location"
    ]
    end_date = get_end_date(metadata)
    raw_desc = extract_desc_data(metadata, end_date)
    raw_cat_map = get_cat_map(metadata)
    raw_station_data = extract_station_data(
        stations, is_drop_old_kaohsiung, old_kaohsiung_id, end_date
    )
    raw_statistic_data = extract_static_data(stations, is_drop_old_kaohsiung)
    raw_observe_data = extract_observe_data(stations, is_drop_old_kaohsiung)

    # Transform
    desc = raw_desc.copy()
    cate_map = raw_cat_map.copy()
    station_data = raw_station_data.copy()
    statistic_data = raw_statistic_data.copy()
    observe_data = raw_observe_data.copy()
    # rename
    station_data = station_data.rename(
        columns={
            "StationID": "station_id",
            "StationName": "station_name",
            "StationNameEN": "station_name_en",
        }
    )
    statistic_data = statistic_data.rename(
        columns={
            "Date": "data_date",
            "Maximum": "max_temperature",
            "Minimum": "min_temperature",
            "Mean": "mean_temperature",
        }
    )
    observe_data = observe_data.rename(
        columns={
            "AirPressure": "pressure",
            "AirTemperature": "temperature",
            "RelativeHumidity": "humidity",
            "WindSpeed": "wind_speed",
            "WindDirection": "wind_direction",
            "Precipitation": "rainfall",  # 降水
            "SunshineDuration": "sunshine_duration",
            "dataTime": "data_time",
        }
    )
    # define column type
    # these columns are mixed with number and string, so we treat them as string
    station_data["station_id"] = station_data["station_id"].astype(str)
    statistic_data["max_temperature"] = (
        statistic_data["max_temperature"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["AirTemperature"])
    )
    statistic_data["min_temperature"] = (
        statistic_data["min_temperature"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["AirTemperature"])
    )
    statistic_data["mean_temperature"] = (
        statistic_data["mean_temperature"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["AirTemperature"])
    )
    observe_data["temperature"] = (
        observe_data["temperature"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["AirTemperature"])
    )
    observe_data["humidity"] = (
        observe_data["humidity"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["RelativeHumidity"])
    )
    observe_data["wind_speed"] = (
        observe_data["wind_speed"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["WindSpeed"])
    )
    observe_data["wind_direction"] = (
        observe_data["wind_direction"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["WindDirection"])
    )
    observe_data["rainfall"] = (
        observe_data["rainfall"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["Precipitation"])
    )
    observe_data["sunshine_duration"] = (
        observe_data["sunshine_duration"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["SunshineDuration"])
    )
    observe_data["pressure"] = (
        observe_data["pressure"]
        .astype(str)
        .apply(mapping_category_ignore_number, cate=cate_map["AirPressure"])
    )
    # time
    desc["data_date"] = convert_str_to_time_format(
        desc["data_date"], output_level="date"
    )
    station_data["data_date"] = convert_str_to_time_format(
        station_data["data_date"], output_level="date"
    )
    statistic_data["data_date"] = convert_str_to_time_format(
        statistic_data["data_date"], output_level="date"
    )
    # convert 24:00:00 to 00:00:00 and add 1 day
    is_hour24 = observe_data["data_time"].str.contains("24:00:00")
    observe_data["data_time"] = observe_data["data_time"].str.replace(
        "24:00:00", "00:00:00"
    )
    observe_data["data_time"] = observe_data["data_time"].str.replace(
        "+08:00", "", regex=False
    )
    observe_data["data_time"] = convert_str_to_time_format(observe_data["data_time"])
    observe_data.loc[is_hour24, "data_time"] = observe_data.loc[
        is_hour24, "data_time"
    ] + timedelta(days=1)
    # select column
    desc = desc[["data_date", "name", "desc", "units", "special_values"]]
    station_data = station_data[
        ["data_date", "station_id", "station_name", "station_name_en"]
    ]
    statistic_data = statistic_data[
        [
            "data_date",
            "station_name",
            "min_temperature",
            "mean_temperature",
            "max_temperature",
        ]
    ]
    observe_data = observe_data[
        [
            "data_time",
            "station_name",
            "temperature",
            "wind_direction",
            "wind_speed",
            "pressure",
            "humidity",
            "rainfall",
            "sunshine_duration",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=statistic_data,
        load_behavior=load_behavior,
        default_table=default_table1,
    )
    save_dataframe_to_postgresql(
        engine,
        data=observe_data,
        load_behavior=load_behavior,
        default_table=default_table2,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050101_1")
dag.create_dag(etl_func=_D050101_1)
