from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _fire_hospital_capacity(**kwargs):
    import os
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "town": 'character varying(10) COLLATE pg_catalog."default"',
        "hospital_name": 'character varying(100) COLLATE pg_catalog."default"',
        "total_beds": "integer",
        "available_beds": "integer",
        "status_note": 'text COLLATE pg_catalog."default"',
        "report_time": "timestamp with time zone",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    SOURCE_URL = "https://example.gov.tw/open-data/fire_hospital_capacity.csv"

    # === Extract ===
    local_path = os.path.join(data_path, dag_id, "raw.csv")
    download_file(local_path, SOURCE_URL)
    raw_data = pd.read_csv(local_path, encoding="big5")

    # === Transform ===
    data = raw_data.rename(
        columns={
            "鄉鎮": "town",
            "醫院名稱": "hospital_name",
            "總床數": "total_beds",
            "可用床數": "available_beds",
            "備註": "status_note",
            "資料時間": "report_time",
        }
    )
    data["report_time"] = convert_str_to_time_format(data["report_time"])
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
    data["total_beds"] = pd.to_numeric(data["total_beds"], errors="coerce").fillna(0).astype(int)
    data["available_beds"] = pd.to_numeric(data["available_beds"], errors="coerce").fillna(0).astype(int)
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
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["report_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="fire_hospital_capacity")
dag.create_dag(etl_func=_fire_hospital_capacity)
