from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _green_store(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_current_rid_from_page_id,
        get_data_taipei_api,
    )
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
        "seq": "integer",
        "store_name": 'text COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "store_code": 'character varying(20) COLLATE pg_catalog."default"',
        "contact_person": 'text COLLATE pg_catalog."default"',
        "contact_phone": 'character varying(50) COLLATE pg_catalog."default"',
        "extension": 'character varying(20) COLLATE pg_catalog."default"',
        "mobile": 'character varying(20) COLLATE pg_catalog."default"',
        "store_type": 'character varying(50) COLLATE pg_catalog."default"',
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    PAGE_ID = "1756cb64-0066-444a-a323-9f3b5a961045"

    # === Extract ===
    rid = get_current_rid_from_page_id(PAGE_ID)
    raw_data = get_data_taipei_api(rid, output_format="dataframe")

    # === Transform ===
    data = raw_data.rename(
        columns={
            "序號": "seq",
            "綠色商店名稱": "store_name",
            "聯絡地址": "address",
            "商店編號": "store_code",
            "聯絡人": "contact_person",
            "聯絡電話": "contact_phone",
            "分機": "extension",
            "手機號碼": "mobile",
            "綠色商店類型": "store_type",
        }
    )
    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
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
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="green_store")
dag.create_dag(etl_func=_green_store)
