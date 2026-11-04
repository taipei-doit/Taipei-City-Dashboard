from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _green_point(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    RID = "5fe3a136-29cc-4695-a17e-6636a32c3342"
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(raw_records)

    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    data = raw_data.rename(
        columns={
            "name": "park_name",
            "localcallservice": "phone",
            "management": "management",
            "areacode": "area_code",
        }
    )

    SELECT_COLUMNS = [
        "data_time",
        "seqno",
        "park_name",
        "area",
        "address",
        "management",
        "phone",
        "area_code",
    ]

    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None

    data = data[SELECT_COLUMNS]

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seqno": 'character varying(50) COLLATE pg_catalog."default"',
        "park_name": 'character varying(255) COLLATE pg_catalog."default"',
        "area": 'character varying(100) COLLATE pg_catalog."default"',
        "address": 'character varying(255) COLLATE pg_catalog."default"',
        "management": 'character varying(255) COLLATE pg_catalog."default"',
        "phone": 'character varying(100) COLLATE pg_catalog."default"',
        "area_code": 'character varying(50) COLLATE pg_catalog."default"',
    }

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

    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="green_point",
)

dag.create_dag(etl_func=_green_point)
