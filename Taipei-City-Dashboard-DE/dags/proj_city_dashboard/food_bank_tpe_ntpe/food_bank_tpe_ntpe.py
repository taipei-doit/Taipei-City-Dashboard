import re
import concurrent.futures

import requests
import pandas as pd
from sqlalchemy import create_engine

from airflow.exceptions import AirflowException

from operators.common_pipeline import CommonDag
from utils.extract_stage import (
    NewTaipeiAPIClient,
    get_current_rid_from_page_id,
    get_data_taipei_api,
)
from utils.get_time import get_tpe_now_time_str
from utils.load_stage import (
    save_dataframe_to_postgresql,
)

ARCGIS_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"


def _geocode_one(addr):
    try:
        r = requests.get(ARCGIS_URL, params={
            "SingleLine": addr, "f": "json",
            "outSR": '{"wkid":4326}', "maxLocations": 1,
        }, timeout=15)
        candidates = r.json().get("candidates", [])
        if candidates and candidates[0].get("score", 0) >= 80:
            loc = candidates[0]["location"]
            return loc["x"], loc["y"]
    except Exception:
        pass
    return None, None


def _geocode_parallel(addresses, max_workers=6):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_geocode_one, addresses))
    return [r[0] for r in results], [r[1] for r in results]

DAG_ID = "food_bank_tpe_ntpe"
TPE_PAGE_ID = "3fbc79e5-0138-4c89-8c47-39feddbd6d3f"
NTPE_RID = "1C1D0066-A4E7-4753-B8BC-D7728D5F3E04"
DISTRICT_PATTERN = re.compile(r"([^市縣\s]{1,3}區)")


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # === Extract ===
    tpe_raw = get_data_taipei_api(get_current_rid_from_page_id(TPE_PAGE_ID))
    tpe = pd.DataFrame(tpe_raw)
    print(f"[{DAG_ID}] tpe raw rows: {len(tpe)}")

    ntpe_client = NewTaipeiAPIClient(NTPE_RID, input_format="json")
    ntpe = pd.DataFrame(ntpe_client.get_all_data(size=1000))
    print(f"[{DAG_ID}] ntpe raw rows: {len(ntpe)}")

    # === Transform: 臺北側 ===
    tpe = tpe.rename(columns={
        "序號": "seq_no",
        "機構類型": "org_type",
        "機構名稱": "name",
        "行政區代碼": "district_code",
        "地址": "address",
    })
    tpe["source_dataset"] = "tpe_00003431"
    tpe["city"] = "臺北市"
    tpe["tel"] = tpe.get("電話", pd.Series(dtype=str))
    tpe["district"] = tpe["address"].astype(str).str.extract(DISTRICT_PATTERN, expand=False)
    tpe["postal_code"] = None

    # === Transform: 新北側（S6 注意：key 是 `no` 而非 `seqno`，§11 #6） ===
    # 新北側 address 缺「新北市OO區」前綴，必須在 rename 前先拼接（§6.5.3）
    ntpe["address"] = (
        ntpe["county"].fillna("").astype(str)
        + ntpe["area"].fillna("").astype(str)
        + ntpe["address"].fillna("").astype(str)
    )
    ntpe = ntpe.rename(columns={
        "no": "seq_no",
        "title": "name",
        "countycode": "county_code",
        "county": "city",
        "areacode": "district_code",
        "area": "district",
        "postalcode": "postal_code",
        "localcallservice": "tel",
    })
    ntpe["source_dataset"] = "ntpe_1c1d0066"
    ntpe["org_type"] = None

    # === Merge ===
    keep = [
        "source_dataset", "seq_no", "name", "org_type", "city",
        "district", "district_code", "postal_code", "address", "tel",
    ]
    df = pd.concat([tpe[keep], ntpe[keep]], ignore_index=True)
    print(f"[{DAG_ID}] merged rows: {len(df)}")
    if len(df) == 0:
        raise AirflowException(f"[{DAG_ID}] merged dataframe is empty — refusing to TRUNCATE existing table")

    df["address"] = df["address"].astype(str).str.replace("台北市", "臺北市", regex=False)
    # 補齊臺北側可能漏掉或新北側 regex 覆寫 — 統一 regex 抽一次
    df["district"] = df["district"].fillna(
        df["address"].str.extract(DISTRICT_PATTERN, expand=False)
    )
    df["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # === Geocode via ArcGIS ===
    unique_addr = pd.Series(df["address"].unique())
    x, y = _geocode_parallel(unique_addr)
    geo = pd.DataFrame({"lng": x, "lat": y, "address": unique_addr})
    df = df.merge(geo, on="address", how="left")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    rate = df["lng"].notna().sum() / len(df)
    print(f"[{DAG_ID}] geocode success rate: {rate:.2%}")
    ready_data = df[[
        "source_dataset", "seq_no", "name", "org_type", "city", "district",
        "district_code", "postal_code", "address", "tel",
        "lng", "lat", "data_time",
    ]]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    print(f"[{DAG_ID}] loaded {len(ready_data)} rows into {default_table}")


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder=DAG_ID)
dag.create_dag(etl_func=_transfer)
