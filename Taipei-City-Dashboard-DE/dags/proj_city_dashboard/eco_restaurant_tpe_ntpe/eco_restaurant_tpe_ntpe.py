import re

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

DAG_ID = "eco_restaurant_tpe_ntpe"
TPE_PAGE_ID = "845818d9-c432-44b4-85dd-03d71bd867b2"
NTPE_RID = "E90D14F8-5995-4EBB-AF19-8F8FD7D396C8"
DISTRICT_PATTERN = re.compile(r"([^市縣\s]{1,3}區)")


def _to_pg_array_literal(raw_str):
    """逗號分隔字串 → PostgreSQL array literal 字串 '{a,b,c}'。
    本資料集的中文標籤不含逗號或引號，無需額外 escape。"""
    items = [s.strip() for s in raw_str.split(",") if s.strip()]
    return "{" + ",".join(items) + "}"


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
        "餐廳名稱": "name",
        "餐廳地址": "address",
        "餐廳電話": "tel",
        "額外環保作為": "_env_actions_raw",
    })
    tpe["source_dataset"] = "tpe_00002761"
    tpe["city"] = "臺北市"
    tpe["env_actions"] = tpe["_env_actions_raw"].fillna("").apply(_to_pg_array_literal)

    # === Transform: 新北側 ===
    ntpe = ntpe.rename(columns={
        "seqno": "seq_no",
        "name": "name",
        "address": "address",
        "localcallservice": "tel",
    })
    ntpe["source_dataset"] = "ntpe_e90d14f8"
    ntpe["city"] = "新北市"
    ntpe["env_actions"] = "{}"

    # === Merge ===
    keep = ["source_dataset", "seq_no", "name", "address", "city", "tel", "env_actions"]
    df = pd.concat([tpe[keep], ntpe[keep]], ignore_index=True)
    print(f"[{DAG_ID}] merged rows: {len(df)}")
    if len(df) == 0:
        raise AirflowException(f"[{DAG_ID}] merged dataframe is empty — refusing to TRUNCATE existing table")

    df["address"] = df["address"].astype(str).str.replace("台北市", "臺北市", regex=False)
    df["district"] = df["address"].str.extract(DISTRICT_PATTERN, expand=False)
    df["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # === Geometry（暫時跳過 geocoding，待 TPGOS_GET_ADDR_XY 設定後補）===
    df["lng"] = None
    df["lat"] = None
    ready_data = df[[
        "source_dataset", "seq_no", "name", "address", "city", "district",
        "tel", "env_actions", "lng", "lat", "data_time",
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
