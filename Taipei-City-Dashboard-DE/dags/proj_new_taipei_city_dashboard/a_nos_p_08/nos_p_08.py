import os
import time

from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    """
    MOENV nos_p_08 → noise_stations：Extract → Transform → Load
    (客製化：僅保留 臺北市/台北市 與 新北市 的資料)
    """
    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine
    import geopandas as gpd
    from shapely.geometry import Point

    from utils.load_stage import save_dataframe_to_postgresql
    from utils.transform_time import convert_str_to_time_format

    # --- 執行環境與 DAG 目標表（由 job_config / kwargs 注入）---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # --- Extract：以 requests 對 MOENV API 做 offset/limit 分頁，直到末頁或空結果 ---
    api_key = Variable.get("MOENV_API_KEY")  # 請於 Airflow 填入 MOENV API 金鑰
    base_url = "https://data.moenv.gov.tw/api/v2/nos_p_08"
    limit = 1000
    offset = 0
    all_records = []

    verify_ssl_env = os.getenv("MOENV_VERIFY_SSL", "true").strip().lower()
    verify_ssl = verify_ssl_env not in {"0", "false", "no"}

    while True:
        response = requests.get(
            base_url,
            params={
                "format": "json",
                "api_key": api_key,
                "offset": offset,
                "limit": limit,
            },
            timeout=120,
            proxies=proxies,
            verify=verify_ssl,
        )
        response.raise_for_status()
        body = response.json()

        if isinstance(body, list):
            batch = body
        elif isinstance(body, dict):
            batch = body.get("records") or body.get("data") or []
            if not batch and isinstance(body.get("result"), dict):
                batch = body["result"].get("records") or []
        else:
            raise TypeError(f"Unexpected MOENV JSON type: {type(body).__name__}")

        if not batch:
            break
        print(f"Fetched {len(batch)} records at offset {offset}")
        all_records.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.1)

    raw_data = pd.DataFrame(all_records)
    if raw_data.empty:
        raise ValueError("MOENV nos_p_08 returned no records.")

    # --- Transform：對齊資料庫欄位名與型別 ---
    data = raw_data.copy()
    
    # 強制將所有欄位名轉為小寫
    data.columns = [c.lower() for c in data.columns]

    # 📍=========================================📍
    #   新增過濾邏輯：只保留「雙北」的測站
    # 📍=========================================📍
    target_counties = ["臺北市", "台北市", "新北市"]
    before_filter_count = len(data)
    data = data[data["county"].isin(target_counties)].copy()
    
    print(f"🌍 縣市過濾：從全台 {before_filter_count} 筆中，篩選出雙北共 {len(data)} 筆。")
    
    if data.empty:
        print("⚠️ 警告：本次 API 回傳中沒有雙北測站，提早結束任務。")
        return  # 若無資料則提早結束，不進資料庫


    # --- 處理台灣民國年日期轉換 ---
    def convert_roc_to_gregorian(date_val):
        if pd.isna(date_val) or str(date_val).strip() == "":
            return None
        d_str = str(date_val).strip()
        # 處理連續數字的民國年 (例如 '0930101' 轉為 '2004-01-01')
        if d_str.isdigit() and len(d_str) >= 6:
            roc_year = int(d_str[:-4])
            month = d_str[-4:-2]
            day = d_str[-2:]
            gregorian_year = roc_year + 1911
            return f"{gregorian_year}-{month}-{day}"
        return d_str

    if "startdate" in data.columns:
        data["startdate"] = data["startdate"].apply(convert_roc_to_gregorian)
        data["startdate"] = convert_str_to_time_format(data["startdate"])
    if "enddate" in data.columns:
        data["enddate"] = data["enddate"].apply(convert_roc_to_gregorian)
        data["enddate"] = convert_str_to_time_format(data["enddate"])

    # --- 數值型別 (經緯度、路寬) ---
    numeric_cols = [
        "sideroadwidth",
        "longitude",
        "latitude",
    ]
    
    # --- 字串型別 ---
    str_cols = [
        "stationid", 
        "county", 
        "recordtype", 
        "stationname", 
        "areatype", 
        "noisetype", 
        "address", 
        "status", 
        "endreason", 
        "sideroad"
    ]

    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in str_cols:
        if col in data.columns:
            data[col] = data[col].fillna("").astype(str)

    # --- 欄位順序與主鍵過濾 ---
    order_cols = [
        "stationid",
        "county",
        "recordtype",
        "startdate",
        "stationname",
        "areatype",
        "noisetype",
        "address",
        "status",
        "enddate",
        "endreason",
        "sideroad",
        "sideroadwidth",
        "longitude",
        "latitude"
    ]
    exist = [c for c in order_cols if c in data.columns]
    ready_data = data[exist].dropna(subset=["stationid"], how="any")

    # 去重：同批資料若含重複 stationid，保留最後一筆
    before_n = len(ready_data)
    ready_data = ready_data.drop_duplicates(subset=["stationid"], keep="last")
    if len(ready_data) < before_n:
        print(f"noise_stations dedup by stationid: {before_n} -> {len(ready_data)} rows")

    # --- Load：寫入資料庫 ---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

    # --- 輸出 GeoJSON ---
    if {"longitude", "latitude"}.issubset(ready_data.columns):
        lon = pd.to_numeric(ready_data["longitude"], errors="coerce")
        lat = pd.to_numeric(ready_data["latitude"], errors="coerce")
        geo_data = ready_data.assign(longitude=lon, latitude=lat).dropna(
            subset=["longitude", "latitude"]
        )

        if not geo_data.empty:
            geometry = [Point(xy) for xy in zip(geo_data["longitude"], geo_data["latitude"])]
            gdata = gpd.GeoDataFrame(geo_data, geometry=geometry, crs="EPSG:4326")
            output_path = "/opt/airflow/mapData/noise_station.geojson"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            gdata.to_file(output_path, driver="GeoJSON", encoding="utf-8")
            print(f"GeoJSON file has been created: {output_path}")
        else:
            print("No valid coordinates for GeoJSON output.")
    else:
        print("Missing longitude/latitude columns; skipping GeoJSON output.")


# --- DAG 註冊 ---
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="a_nos_p_08",  
)
dag.create_dag(etl_func=_transfer)