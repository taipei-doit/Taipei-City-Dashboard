from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050101_2(**kwargs):
    import json

    import pandas as pd
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_mixed_type import given_string_to_none
    from utils.transform_time import convert_str_to_time_format

    # Config
    cwa_api_key = Variable.get("CWA_API_KEY")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={cwa_api_key}&format=json"
    GEOMETRY_TYPE = "Point"
    file_name = f"{dag_id}.json"
    FROM_CRS = 4326

    # Extract
    # download
    local_file = download_file(file_name, url, is_proxy=True)
    if not local_file:
        return False
    with open(local_file) as json_file:
        res = json.load(json_file)
    # parse
    station_info = res["cwaopendata"]["dataset"]["Station"]
    df_list = []
    for item in station_info:
        temp = {}
        temp["data_time"] = item["ObsTime"]["DateTime"]
        temp["lat"] = item["GeoInfo"]["Coordinates"][1]["StationLatitude"]
        temp["lng"] = item["GeoInfo"]["Coordinates"][1]["StationLongitude"]
        temp["name"] = item["StationName"]
        temp["id"] = item["StationId"]
        temp["city"] = item["GeoInfo"]["CountyName"]
        temp["town"] = item["GeoInfo"]["TownName"]
        temp["height"] = item["GeoInfo"]["StationAltitude"]
        temp["weather"] = item["WeatherElement"]["Weather"]
        temp["wind_direction"] = item["WeatherElement"]["WindDirection"]
        temp["wind_speed"] = item["WeatherElement"]["WindSpeed"]
        temp["temperature"] = item["WeatherElement"]["AirTemperature"]
        temp["humidity"] = item["WeatherElement"]["RelativeHumidity"]
        temp["pressure"] = item["WeatherElement"]["AirPressure"]
        temp["uvi_hourly"] = item["WeatherElement"]["UVIndex"]
        temp["temperature_today_max"] = item["WeatherElement"]["DailyExtreme"][
            "DailyHigh"
        ]["TemperatureInfo"]["AirTemperature"]
        temp["temperature_today_min"] = item["WeatherElement"]["DailyExtreme"][
            "DailyLow"
        ]["TemperatureInfo"]["AirTemperature"]
        temp["sunshine_duration"] = item["WeatherElement"]["SunshineDuration"]
        temp["visibility"] = item["WeatherElement"]["VisibilityDescription"]
        temp["precipitation_now"] = item["WeatherElement"]["Now"]["Precipitation"]
        df_list.append(temp)
    raw_data = pd.DataFrame(df_list)

    # Transform
    data = raw_data.copy()
    # data source use -99 for no data, replace it to None
    data = data.applymap(given_string_to_none, given_str="-99")
    # define column type
    str_columns = ["name", "id", "city", "town", "visibility", "weather"]
    for col in data.columns.tolist():
        if col in str_columns:
            data[col] = data[col].astype(str)
        elif col == "data_time":
            data["data_time"] = convert_str_to_time_format(data["data_time"])
        else:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    gdata = gdata.drop(columns="geometry")
    # select column
    ready_data = gdata[
        [
            "data_time",
            "id",
            "city",
            "town",
            "name",
            "lng",
            "lat",
            "height",
            "wkb_geometry",
            "weather",
            "temperature",
            "temperature_today_min",
            "temperature_today_max",
            "wind_direction",
            "wind_speed",
            "humidity",
            "precipitation_now",
            "pressure",
            "sunshine_duration",
            "visibility",
            "uvi_hourly",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050101_2")
dag.create_dag(etl_func=_D050101_2)
