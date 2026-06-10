from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _resh_petition_monthly(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "file_tag": 'character varying(10) COLLATE pg_catalog."default"',
        "case_no": 'character varying(50) COLLATE pg_catalog."default"',
        "main_category": 'character varying(50) COLLATE pg_catalog."default"',
        "sub_category": 'character varying(50) COLLATE pg_catalog."default"',
        "assign_agency": 'character varying(50) COLLATE pg_catalog."default"',
        "assign_dept": 'character varying(100) COLLATE pg_catalog."default"',
        "accept_time": "timestamp with time zone",
        "apply_time": "timestamp with time zone",
        "close_time": "timestamp with time zone",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    PAGE_ID = "cb423c17-88eb-4231-a725-f1b93247d1bf"

    # === Extract ===
    res = requests.get(
        f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={PAGE_ID}",
        timeout=60,
    )
    res.raise_for_status()
    rid_map = {d["name"][:5]: d["rid"] for d in res.json()["payload"]["resources"]}

    raw_frames = []
    for file_tag, rid in rid_map.items():
        rd = get_data_taipei_api(rid, output_format="dataframe")
        rd["file_tag"] = file_tag
        raw_frames.append(rd)
    raw_data = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()

    # === Transform ===
    data = raw_data.rename(
        columns={
            "案件編號": "case_no",
            "案件主類別": "main_category",
            "案件次類別": "sub_category",
            "案件子類別": "sub_category",
            "受理機關": "assign_agency",
            "受理科室": "assign_dept",
            "受理日期": "accept_time",
            "送達日期": "apply_time",
            "結案日期": "close_time",
        }
    )
    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["accept_time"] = convert_str_to_time_format(data["accept_time"], errors="coerce")
    data["apply_time"] = convert_str_to_time_format(data["apply_time"])
    data["close_time"] = convert_str_to_time_format(data["close_time"])
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["close_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="resh_petition_monthly")
dag.create_dag(etl_func=_resh_petition_monthly)
