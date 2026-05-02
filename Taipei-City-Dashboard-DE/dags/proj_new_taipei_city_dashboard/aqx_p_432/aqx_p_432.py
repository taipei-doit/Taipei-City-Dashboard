import os
import time

from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    """
    MOENV aqx_p_432 → aqi_records：Extract（HTTP 分頁）→ Transform（欄位／型別）→ Load（PG）→ 更新資料集最後時間。
    """
    import pandas as pd
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # --- 執行環境與 DAG 目標表（由 job_config / kwargs 注入）---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # --- Extract：以 requests 對 MOENV API 做 offset/limit 分頁，直到末頁或空結果 ---
    api_key = Variable.get("MOENV_API_KEY")  # 請於 Airflow 填入 MOENV API 金鑰
    base_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
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
        raise ValueError("MOENV aqx_p_432 returned no records.")

    # --- Transform：對齊資料庫欄位名與型別（aqi_records）---
    data = raw_data.copy()
    # API 欄位 pm2.5 含句點，改為合法欄位名以便入庫
    rename_dot_cols = {}
    if "pm2.5" in data.columns:
        rename_dot_cols["pm2.5"] = "pm2_5"
    if "pm2.5_avg" in data.columns:
        rename_dot_cols["pm2.5_avg"] = "pm2_5_avg"
    data = data.rename(columns=rename_dot_cols)

    if "publishtime" in data.columns:
        data["publishtime"] = convert_str_to_time_format(data["publishtime"])

    # INTEGER（可空 Int64）、NUMERIC（float）、字串欄位補空字串
    int_cols = [
        "aqi",
        "o3",
        "o3_8hr",
        "pm10",
        "pm2_5",
        "no2",
        "pm10_avg",
        "so2_avg",
        "siteid",
    ]
    numeric_cols = [
        "so2",
        "co",
        "nox",
        "no",
        "wind_speed",
        "wind_direc",
        "co_8hr",
        "pm2_5_avg",
        "longitude",
        "latitude",
    ]
    str_cols = ["sitename", "county", "pollutant", "status"]

    for col in int_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").astype("Int64")
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in str_cols:
        if col in data.columns:
            data[col] = data[col].fillna("").astype(str)

    # 欄位順序與主鍵：剔除無 siteid 列，避免違反 PK
    order_cols = [
        "sitename",
        "county",
        "aqi",
        "pollutant",
        "status",
        "so2",
        "co",
        "o3",
        "o3_8hr",
        "pm10",
        "pm2_5",
        "no2",
        "nox",
        "no",
        "wind_speed",
        "wind_direc",
        "publishtime",
        "co_8hr",
        "pm2_5_avg",
        "pm10_avg",
        "so2_avg",
        "longitude",
        "latitude",
        "siteid",
    ]
    exist = [c for c in order_cols if c in data.columns]
    ready_data = data[exist].dropna(subset=["siteid"], how="any")

    # --- Load：依 load_behavior 寫入 ready 表（並於 current+history 時附加歷史表）---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )


# --- DAG 註冊：CommonDag 依 proj_folder + dag_folder 載入 job_config.json ---
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="aqx_p_432",
)
dag.create_dag(etl_func=_transfer)
