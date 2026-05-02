import os
import time

import pandas as pd
from airflow import DAG
from operators.common_pipeline import CommonDag

def roc_app_year_to_gregorian(val):
    # --- app_year：民國 → 西元，再轉可空整數 ---
    if pd.isna(val):
        return pd.NA
    s = str(val).strip()
    if not s:
        return pd.NA
    try:
        n = int(float(s))
    except (TypeError, ValueError):
        return pd.NA
    if n >= 1900:
        return n
    return n + 1911


def parse_check_yn_value(v):
    # --- 是否經查證：API 為「是」/「否」 ---
    if pd.isna(v):
        return pd.NA
    t = str(v).strip()
    if t == "是":
        return True
    if t == "否":
        return False
    return pd.NA


def _transfer(**kwargs):
    import requests
    from airflow.models import Variable
    from sqlalchemy import create_engine

    from utils.load_stage import save_dataframe_to_postgresql

    # --- 執行參數（CommonDag / job_config 注入）---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    api_key = Variable.get("MOENV_API_KEY")
    base_url = "https://data.moenv.gov.tw/api/v2/ghg_p_01"
    limit = 1000
    offset = 0
    all_records = []

    verify_ssl_env = os.getenv("MOENV_VERIFY_SSL", "true").strip().lower()
    verify_ssl = verify_ssl_env not in {"0", "false", "no"}

    # --- Extract：offset/limit 取回全部 JSON 列 ---
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
        raise ValueError("MOENV ghg_p_01 returned no records.")

    # --- Transform：對齊資料表欄位名與型別 ---
    data = raw_data.copy()
    # 欄名：API 大小寫混用，統一小寫
    data.columns = [
        str(c).lower() if isinstance(c, str) else c for c in data.columns
    ]

    # app_year：民國 → 西元，再轉可空整數
    if "app_year" in data.columns:
        data["app_year"] = data["app_year"].map(roc_app_year_to_gregorian)
        data["app_year"] = pd.to_numeric(data["app_year"], errors="coerce").astype(
            "Int64"
        )

    # 排放量數值
    numeric_cols = ["tot1_value", "tot2_value", "tot_value"]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # 字串欄位
    str_cols = [
        "ban",
        "companyname",
        "scompanyno",
        "controlno",
        "city",
        "town",
        "companyaddr",
        "ccksicco1",
        "sicname1",
        "cause",
    ]
    for col in str_cols:
        if col in data.columns:
            data[col] = data[col].fillna("").astype(str)

    # 是否經查證 → boolean（可空）
    if "check_yn" in data.columns:
        data["check_yn"] = data["check_yn"].map(parse_check_yn_value)
        data["check_yn"] = data["check_yn"].astype("boolean")

    order_cols = [
        "app_year",
        "ban",
        "companyname",
        "scompanyno",
        "controlno",
        "city",
        "town",
        "companyaddr",
        "ccksicco1",
        "sicname1",
        "tot1_value",
        "tot2_value",
        "tot_value",
        "cause",
        "check_yn",
    ]
    exist = [c for c in order_cols if c in data.columns]
    # 無法還原年度者剔除；欄序依 order_cols
    ready_data = data[exist].dropna(subset=["app_year"], how="any")

    # --- Load：寫入 ready_data（truncate/replace 等由 load_behavior 控制）---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="ghg_p_01",
)
dag.create_dag(etl_func=_transfer)
