import os

import pandas as pd
from airflow import DAG
from operators.common_pipeline import CommonDag


# --- Helper：民國年轉西元 ---
def roc_year_to_gregorian(val):
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


def _transfer(**kwargs):
    import requests
    from sqlalchemy import create_engine

    from utils.load_stage import save_dataframe_to_postgresql

    # ==========================================================
    # 1) 執行參數（由 CommonDag / job_config 注入）
    # ==========================================================
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # ==========================================================
    # 2) Extract：單次 GET 水利署 JSON（無分頁）
    # ==========================================================
    base_url = (
        "https://opendata.wra.gov.tw/api/v2/"
        "dfc12113-9e62-4185-a3e6-4a83042d0c71"
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
        raise ValueError("WRA fish water API returned no records.")

    # ==========================================================
    # 3) Transform：欄位清理、型別轉換、欄序整理
    # ==========================================================
    # 欄名統一小寫
    data = raw_data.copy()
    data.columns = [
        str(c).lower() if isinstance(c, str) else c for c in data.columns
    ]

    # 年度欄位轉換（呼叫上方 helper）
    if "year" in data.columns:
        data["year"] = data["year"].map(roc_year_to_gregorian)
        data["year"] = pd.to_numeric(data["year"], errors="coerce").astype("Int64")

    # 數值欄位
    numeric_cols = [
        "area",
        "cultivationarea",
        "cultivationkind",
        "serialnumber",
        "totalconsumptionofwater",
    ]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # 字串欄位
    str_cols = ["countycode"]
    for col in str_cols:
        if col in data.columns:
            data[col] = data[col].fillna("").astype(str)

    # 台北市 / 新北市篩選：
    # - area=1（北部）
    # - countycode: 63000=臺北市, 65000=新北市, 10001=臺北縣（舊制）
    if "area" not in data.columns or "countycode" not in data.columns:
        raise ValueError("WRA fish water response lacks area/countycode for filtering.")
    before_city = len(data)
    target_county_codes = {"63000", "65000", "10001"}
    data = data[
        (data["area"] == 1) & (data["countycode"].str.strip().isin(target_county_codes))
    ].copy()
    print(
        "Filtered by area/countycode (臺北市/新北市/臺北縣): "
        f"{before_city} -> {len(data)} rows"
    )
    if data.empty:
        raise ValueError("No fish water rows left after filtering to Taipei/New Taipei.")

    # 舊制縣市代碼正規化：10001（臺北縣）併入 65000（新北市）
    data["countycode"] = data["countycode"].str.strip()
    n_old_taipei_county = (data["countycode"] == "10001").sum()
    data.loc[data["countycode"] == "10001", "countycode"] = "65000"
    if n_old_taipei_county:
        print(f"Normalized countycode 10001 -> 65000: {int(n_old_taipei_county)} rows")
    data["countycode"] = data["countycode"].replace(
        {
            "63000": "臺北市",
            "65000": "新北市",
        }
    )

    # 不因 status 篩選：未通過審核之列仍計入用水（依業務需求全部加總）

    # API 依魚種分列，年度總用水量需按 年度+縣市 彙總
    data = (
        data.groupby(["year", "area", "countycode"], as_index=False)
        .agg(
            cultivationarea=("cultivationarea", "sum"),
            totalconsumptionofwater=("totalconsumptionofwater", "sum"),
        )
        .copy()
    )

    # 彙總後數值統一四捨五入至小數點後一位
    data["cultivationarea"] = data["cultivationarea"].round(1)
    data["totalconsumptionofwater"] = data["totalconsumptionofwater"].round(1)

    # 欄位排序並剔除無法解析年度的資料（不含 status：彙總後無單一審核狀態）
    order_cols = [
        "year",
        "area",
        "countycode",
        "cultivationarea",
        "totalconsumptionofwater",
    ]
    ready_data = data[order_cols].dropna(subset=["year"], how="any")

    # ==========================================================
    # 4) Load：寫入 ready_data（由 load_behavior 控制）
    # ==========================================================
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

# --- DAG 定義：依 job_config 建立並綁定 _transfer ---
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="fish_water",
)
dag.create_dag(etl_func=_transfer)
