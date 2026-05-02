import os

from airflow import DAG
from operators.common_pipeline import CommonDag

MOA_API_BASE = os.getenv(
    "MOA_API_BASE", "https://data.moa.gov.tw/api/v1"
).rstrip("/")
MOA_API_KEY = os.getenv("MOA_API_KEY", "").strip()


def _transfer(**kwargs):
    import json
    import urllib3
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if not MOA_API_KEY:
        raise ValueError(
            "MOA_API_KEY is not set. Configure MOA_API_KEY (and optionally MOA_API_BASE); "
            "see docker/.env.template."
        )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")

    session = requests.Session()
    all_records = []
    offset = 0
    while True:
        resp = session.get(
            f"{MOA_API_BASE}/CASProductInquiryType/",
            params={"api_key": MOA_API_KEY, "limit": 1000, "offset": offset},
            timeout=60,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("Data", [])
        all_records.extend(batch)
        if not data.get("Next") or not batch:
            break
        offset += len(batch)

    if not all_records:
        return

    now_str = get_tpe_now_time_str(is_with_tz=True)
    df = pd.DataFrame(all_records)
    df["material_name"] = df.get("Material_Name", pd.Series(dtype=str))
    df["raw_data"] = df.apply(
        lambda row: json.dumps(row.to_dict(), ensure_ascii=False, default=str),
        axis=1,
    )
    df["data_time"] = now_str
    ready_data = df[["material_name", "raw_data", "data_time"]]

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=now_str
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cas_product")
dag.create_dag(etl_func=_transfer)
