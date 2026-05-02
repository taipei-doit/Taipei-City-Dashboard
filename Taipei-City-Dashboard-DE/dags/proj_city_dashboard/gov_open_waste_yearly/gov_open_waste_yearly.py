import requests
import pandas as pd
from sqlalchemy import create_engine

from airflow.exceptions import AirflowException

from operators.common_pipeline import CommonDag
from utils.extract_stage import download_file
from utils.get_time import get_tpe_now_time_str
from utils.load_stage import (
    save_dataframe_to_postgresql,
)

DAG_ID = "gov_open_waste_yearly"
METADATA_URL = "https://data.gov.tw/api/v2/rest/dataset/89022"


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # === Extract: 從 data.gov.tw metadata 取 CSV URL ===
    meta = requests.get(METADATA_URL, timeout=30).json()
    distribution = meta.get("result", {}).get("distribution", []) or []
    csv_url = next(
        (d.get("resourceDownloadUrl") for d in distribution
         if d.get("resourceFormat", "").upper() == "CSV"
         or (d.get("resourceDownloadUrl") or "").lower().endswith(".csv")),
        None,
    )
    if not csv_url:
        raise AirflowException(
            f"[{DAG_ID}] 89022 metadata 找不到 CSV resourceDownloadUrl，"
            "疑似 data.gov.tw schema 異動，請手動確認"
        )
    print(f"[{DAG_ID}] csv_url = {csv_url}")

    local_csv = download_file(f"{DAG_ID}.csv", csv_url)
    raw = pd.read_csv(local_csv)
    print(f"[{DAG_ID}] raw rows: {len(raw)}, columns: {list(raw.columns)}")

    # === Transform ===
    data = raw.rename(columns={
        "year": "data_year",
        "county": "county",
        "garbagegenerated": "garbage_generated",
        "garbageclearance": "garbage_clearance",
        "garbagerecycled": "garbage_recycled",
        "foodwastesrecycled": "food_wastes_recycled",
    })

    data["data_year"] = pd.to_numeric(data["data_year"], errors="coerce").astype("Int64")
    data["county"] = data["county"].astype(str).str.replace("台北市", "臺北市", regex=False)

    for col in ["garbage_generated", "garbage_clearance", "garbage_recycled", "food_wastes_recycled"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        else:
            data[col] = None

    data = data.dropna(subset=["data_year", "county"]).copy()
    # data_time 以該年度 12-31 為資料時間戳（對齊 env_srv_energy_subsidy 模式）
    data["data_time"] = data["data_year"].astype(int).astype(str) + "-12-31 23:59:59+08"

    keep = [
        "data_year", "county", "garbage_generated", "garbage_clearance",
        "garbage_recycled", "food_wastes_recycled", "data_time",
    ]
    ready_data = data[keep].reset_index(drop=True)

    if len(ready_data) == 0:
        raise AirflowException(f"[{DAG_ID}] empty data after clean — refusing to proceed")

    print(f"[{DAG_ID}] ready rows: {len(ready_data)}, year range: "
          f"{ready_data['data_year'].min()}~{ready_data['data_year'].max()}")

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    print(f"[{DAG_ID}] loaded {len(ready_data)} rows into {default_table} (+ {history_table})")


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder=DAG_ID)
dag.create_dag(etl_func=_transfer)
