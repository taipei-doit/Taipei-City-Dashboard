from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _food_bank_contacts(**kwargs):
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

    PAGE_ID = "3fbc79e5-0138-4c89-8c47-39feddbd6d3f"

    COL_MAP = {
        "data_time": 'timestamp with time zone DEFAULT CURRENT_TIMESTAMP',
        "seq": "integer",
        "institution_type": 'character varying(20) COLLATE pg_catalog."default"',
        "institution_name": 'text COLLATE pg_catalog."default"',
        "district_code": 'character varying(10) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # Extract
    rid = get_current_rid_from_page_id(PAGE_ID)
    raw_data = get_data_taipei_api(rid, output_format="dataframe")

    # Transform
    data = raw_data.rename(
        columns={
            "序號": "seq",
            "機構類型": "institution_type",
            "機構名稱": "institution_name",
            "行政區代碼": "district_code",
            "地址": "address",
        }
    )
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data = data[SELECT_COLUMNS]

    # Load
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, data["data_time"].max()
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard", dag_folder="food_bank_contacts"
)
dag.create_dag(etl_func=_food_bank_contacts)
