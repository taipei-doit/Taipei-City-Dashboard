from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050502(**kwargs):
    import datetime

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_moenv_json_data
    from utils.get_time import get_tpe_now_time
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    DATASET_CODE = "AQX_P_488"
    filters_query = "county,EQ,臺北市,新北市"
    table_count = (
        create_engine(ready_data_db_uri)
        .execute(f"SELECT COUNT(1) FROM {history_table};")
        .fetchall()[0][0]
    )
    if table_count > 0:  # only get data from last 2 hours
        now_time = get_tpe_now_time(is_with_tz=True)
        now_hour = now_time.replace(minute=0, second=0)
        last_hour = str(now_hour - datetime.timedelta(hours=2))
        last_hour = last_hour.split("+", maxsplit=1)[0]
        filters_query += f"|datacreationdate,GR,{last_hour}"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    res = get_moenv_json_data(
        DATASET_CODE, filters_query=filters_query, is_proxy=True, timeout=None
    )
    raw_data = pd.DataFrame(res)
    raw_data.rename({"datacreationdate": "data_time"}, inplace=True)

    # Transform
    data = raw_data.copy()
    # Rename
    data = data.rename(
        columns={
            "siteid": "site_id",  # 測站代碼
            "sitename": "site_name",  # 測站名稱
            "county": "county",  # 縣市
            "aqi": "aqi",  # 空氣品質指標
            "pollutant": "pollutant",  # 空氣污染指標物
            "status": "status",  # 空氣品質狀態
            "so2": "so2_ppb",  # 二氧化硫(ppb)
            "co": "co_ppm",  # 一氧化碳(ppm)
            "o3": "o3_ppb",  # 臭氧(ppb)
            "o3_8hr": "o3_8hr_ppb",  # 臭氧8小時移動平均(ppb)
            "pm10": "pm10_ug_m3",  # 懸浮微粒(μg/m3)
            "pm2.5": "pm_2point5_ug_m3",  # 細懸浮微粒(μg/m3)
            "no2": "no2_ppb",  # 二氧化氮(ppb)
            "nox": "nox_ppb",  # 氮氧化物(ppb)
            "no": "no_ppb",  # 一氧化氮(ppb)
            "windspeed": "wind_speed_m_sec",  # 風速(m/sec)
            "winddirec": "wind_direction_degree",  # 風向(degrees)
            "datacreationdate": "data_time",  # 資料建置日期
            "co_8hr": "co_8hr_ppm",  # 一氧化碳8小時移動平均(ppm)
            "pm2.5_avg": "pm_2point5_avg_ug_m3",  # 細懸浮微粒移動平均值(μg/m3)
            "pm10_avg": "pm10_avg_ug_m3",  # 懸浮微粒移動平均值(μg/m3)
            "so2_avg": "so2_avg_ppb",  # 二氧化硫移動平均值(ppb)
            "longitude": "lng",
            "latitude": "lat",
            "data_time": "data_time",  # = data creation date
        }
    )
    # define data type
    data["site_id"] = pd.to_numeric(data["site_id"]).astype(int)
    float_cols = [
        "aqi",
        "so2_ppb",
        "co_ppm",
        "o3_ppb",
        "o3_8hr_ppb",
        "pm10_ug_m3",
        "pm_2point5_ug_m3",
        "no2_ppb",
        "nox_ppb",
        "no_ppb",
        "wind_speed_m_sec",
        "wind_direction_degree",
        "co_8hr_ppm",
        "pm_2point5_avg_ug_m3",
        "pm10_avg_ug_m3",
        "so2_avg_ppb",
        "lng",
        "lat",
    ]
    for col in float_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geomettry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "site_id",
            "site_name",
            "county",
            "status",
            "aqi",
            "pollutant",
            "so2_ppb",
            "co_ppm",
            "o3_ppb",
            "o3_8hr_ppb",
            "pm10_ug_m3",
            "pm_2point5_ug_m3",
            "no2_ppb",
            "nox_ppb",
            "no_ppb",
            "wind_speed_m_sec",
            "wind_direction_degree",
            "co_8hr_ppm",
            "pm_2point5_avg_ug_m3",
            "pm10_avg_ug_m3",
            "so2_avg_ppb",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050502")
dag.create_dag(etl_func=_D050502)
