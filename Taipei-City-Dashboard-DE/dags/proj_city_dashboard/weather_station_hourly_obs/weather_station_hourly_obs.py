from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表(若不存在)。冪等,每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _weather_station_hourly_obs(**kwargs):
    # === Imports(全部寫在函式內)===
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

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "station_id": 'character varying(10) COLLATE pg_catalog."default"',
        "station_name": 'text COLLATE pg_catalog."default"',
        "county_name": 'text COLLATE pg_catalog."default"',
        "town_name": 'text COLLATE pg_catalog."default"',
        "obs_time": "timestamp with time zone",
        "altitude": "double precision",
        "weather": 'text COLLATE pg_catalog."default"',
        "air_temperature": "double precision",
        "relative_humidity": "double precision",
        "air_pressure": "double precision",
        "wind_speed": "double precision",
        "wind_direction": "double precision",
        "precipitation": "double precision",
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())
    FROM_CRS = 4326
    # CWA 以 -99 / -990 代表「無觀測資料」,需轉成空值
    MISSING_VALUES = [-99, -99.0, -990, -990.0, "-99", "-99.0", "-990", "-990.0"]

    # === Extract ===
    # CWA REST API 需 Authorization 金鑰(以 query string 帶入),
    # 沿用既有 CWA DAG 慣例 Variable: CWA_API_KEY。
    cwa_api_key = Variable.get("CWA_API_KEY")
    url = (
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
        f"?Authorization={cwa_api_key}&format=JSON"
    )
    local_file = download_file(f"{dag_id}.json", url)
    with open(local_file, encoding="utf-8") as json_file:
        raw_json = json.load(json_file)
    stations = raw_json["records"]["Station"]

    # === Transform ===
    rows = []
    for station in stations:
        geo_info = station.get("GeoInfo") or {}
        weather_element = station.get("WeatherElement") or {}
        obs_time = station.get("ObsTime") or {}
        now = weather_element.get("Now") or {}
        # GeoInfo.Coordinates 內含多種座標系,取 WGS84 經緯度
        lng = lat = None
        for coord in geo_info.get("Coordinates") or []:
            if coord.get("CoordinateName") == "WGS84":
                lng = coord.get("StationLongitude")
                lat = coord.get("StationLatitude")
        rows.append(
            {
                "station_id": station.get("StationId"),
                "station_name": station.get("StationName"),
                "county_name": geo_info.get("CountyName"),
                "town_name": geo_info.get("TownName"),
                "obs_time": obs_time.get("DateTime"),
                "altitude": geo_info.get("StationAltitude"),
                "weather": weather_element.get("Weather"),
                "air_temperature": weather_element.get("AirTemperature"),
                "relative_humidity": weather_element.get("RelativeHumidity"),
                "air_pressure": weather_element.get("AirPressure"),
                "wind_speed": weather_element.get("WindSpeed"),
                "wind_direction": weather_element.get("WindDirection"),
                "precipitation": now.get("Precipitation"),
                "lng": lng,
                "lat": lat,
            }
        )
    data = pd.DataFrame(rows)

    # CWA 缺值(-99 / -990)轉空值,數值欄統一轉 numeric
    numeric_columns = [
        "altitude",
        "air_temperature",
        "relative_humidity",
        "air_pressure",
        "wind_speed",
        "wind_direction",
        "precipitation",
        "lng",
        "lat",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column].replace(MISSING_VALUES, pd.NA), errors="coerce"
        )

    # 觀測時間標準化(CWA DateTime 帶 +08:00,先去除再轉);data_time 用當下時間
    data["obs_time"] = (
        data["obs_time"].astype(str).str.replace("+08:00", "", regex=False)
    )
    data["obs_time"] = convert_str_to_time_format(data["obs_time"])
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    # 無經緯度的測站無法呈現於地圖,先濾除
    data = data.dropna(subset=["lng", "lat"]).reset_index(drop=True)

    # 產生 Point wkb_geometry(WGS84)
    data = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    data = data.drop(columns=["geometry"], errors="ignore")
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata=data,
        load_behavior=load_behavior,
        geometry_type="Point",
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, data["obs_time"].max()
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard", dag_folder="weather_station_hourly_obs"
)
dag.create_dag(etl_func=_weather_station_hourly_obs)
