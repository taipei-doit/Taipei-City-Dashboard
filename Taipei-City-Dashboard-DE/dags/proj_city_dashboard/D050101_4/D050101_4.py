from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050101_4(**kwargs):
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
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0002-001?Authorization={cwa_api_key}&format=JSON"
    file_name = f"{dag_id}.json"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

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
        temp["dept"] = item["Maintainer"]
        temp["city"] = item["GeoInfo"]["CountyName"]
        temp["town"] = item["GeoInfo"]["TownName"]
        temp["height"] = item["GeoInfo"]["StationAltitude"]
        temp["precipitation_now"] = item["RainfallElement"]["Now"]["Precipitation"]
        temp["precipitation_past_10m"] = item["RainfallElement"]["Past10Min"][
            "Precipitation"
        ]
        temp["precipitation_past_1h"] = item["RainfallElement"]["Past1hr"][
            "Precipitation"
        ]
        temp["precipitation_past_3h"] = item["RainfallElement"]["Past3hr"][
            "Precipitation"
        ]
        temp["precipitation_past_6h"] = item["RainfallElement"]["Past6hr"][
            "Precipitation"
        ]
        temp["precipitation_past_12h"] = item["RainfallElement"]["Past12hr"][
            "Precipitation"
        ]
        temp["precipitation_past_1d"] = item["RainfallElement"]["Past24hr"][
            "Precipitation"
        ]
        temp["precipitation_past_2d"] = item["RainfallElement"]["Past2days"][
            "Precipitation"
        ]
        temp["precipitation_past_3d"] = item["RainfallElement"]["Past3days"][
            "Precipitation"
        ]
        df_list.append(temp)
    raw_data = pd.DataFrame(df_list)

    # Transform
    data = raw_data.copy()
    # define column type
    str_columns = ["name", "id", "city", "town"]
    for col in data.columns.tolist():
        if col in str_columns:
            data[col] = data[col].astype(str)
        elif col == "data_time":
            data["data_time"] = convert_str_to_time_format(data["data_time"])
        else:
            # print(data[col])
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
            "name",
            "id",
            "dept",
            "city",
            "town",
            "precipitation_now",
            "precipitation_past_10m",
            "precipitation_past_1h",
            "precipitation_past_3h",
            "precipitation_past_6h",
            "precipitation_past_12h",
            "precipitation_past_1d",
            "precipitation_past_2d",
            "precipitation_past_3d",
            "height",
            "lat",
            "lng",
            "wkb_geometry",
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

    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050101_4")
dag.create_dag(etl_func=_D050101_4)
