import os

import pandas as pd
from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import requests
    from sqlalchemy import create_engine

    from utils.load_stage import save_dataframe_to_postgresql

    # --- 執行參數（CommonDag / job_config 注入）---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # --- Extract：單次 GET 水利署 JSON（無分頁；data.gov.tw 資料集 8316）---
    base_url = (
        "https://opendata.wra.gov.tw/api/v2/"
        "76249361-736b-449d-9d96-2c74b5013b93"
    )
    verify_ssl_env = os.getenv("WRA_VERIFY_SSL", "true").strip().lower()
    verify_ssl = verify_ssl_env not in {"0", "false", "no"}

    response = requests.get(
        base_url,
        params={"sort": "_importdate asc", "format": "JSON"},
        timeout=120,
        proxies=proxies,
        verify=verify_ssl,
    )
    response.raise_for_status()
    body = response.json()

    if isinstance(body, list):
        records = body
    elif isinstance(body, dict):
        records = body.get("records") or body.get("data") or []
        if not records and isinstance(body.get("result"), dict):
            records = body["result"].get("records") or []
    else:
        raise TypeError(f"Unexpected WRA JSON type: {type(body).__name__}")

    print(f"Fetched {len(records)} records (full response)")

    raw_data = pd.DataFrame(records)
    if raw_data.empty:
        raise ValueError("WRA domestic water API returned no records.")

    # --- Transform：欄名小寫、年度與數值／字串型別 ---
    data = raw_data.copy()
    data.columns = [
        str(c).lower() if isinstance(c, str) else c for c in data.columns
    ]

    if "year" in data.columns:
        data["year"] = pd.to_numeric(data["year"], errors="coerce").astype("Int64")

    numeric_cols = [
        "consumptionofwater",
        "populationserved",
        "thedailydomesticconsumptionofwaterperperson",
    ]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    str_cols = ["countyname", "remarks"]
    for col in str_cols:
        if col in data.columns:
            data[col] = data[col].fillna("").astype(str)

    # --- Transform：縣市篩選（雙北 + 改制前臺北縣）---
    target_cities = {"臺北市", "新北市", "臺北縣"}
    if "countyname" not in data.columns:
        raise ValueError(
            "WRA domestic water response has no countyname column; cannot filter."
        )
    before_city = len(data)
    data = data[data["countyname"].str.strip().isin(target_cities)].copy()
    print(
        f"Filtered by county (臺北市/新北市/臺北縣): {before_city} -> {len(data)} rows"
    )
    if data.empty:
        raise ValueError(
            "No domestic water rows left after filtering to "
            "臺北市 / 新北市 / 臺北縣."
        )

    # --- Transform：臺北縣併入新北市（僅改 countyname 字串，不整併列）---
    data["countyname"] = data["countyname"].str.strip()
    n_taipei_county = (data["countyname"] == "臺北縣").sum()
    data.loc[data["countyname"] == "臺北縣", "countyname"] = "新北市"
    if n_taipei_county:
        print(f"Normalized 臺北縣 -> 新北市: {int(n_taipei_county)} rows")

    # --- Transform：輸出欄序、剔除無年度列 ---
    order_cols = [
        "year",
        "countyname",
        "consumptionofwater",
        "populationserved",
        "thedailydomesticconsumptionofwaterperperson",
        "remarks",
    ]
    exist = [c for c in order_cols if c in data.columns]
    ready_data = data[exist].dropna(subset=["year"], how="any")

    # --- Load：寫入 ready_data（truncate/replace 等由 load_behavior 控制）---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )


# --- 以 CommonDag 依 job_config 建立 DAG 並綁定 _transfer ---
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="domestic_water",
)
dag.create_dag(etl_func=_transfer)
