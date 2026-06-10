from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _food_bank_ntpe(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    RID = "1c1d0066-a4e7-4753-b8bc-d7728d5f3e04"

    COL_MAP = {
        "data_time": 'timestamp with time zone DEFAULT CURRENT_TIMESTAMP',
        "seq": "integer",
        "title": 'text COLLATE pg_catalog."default"',
        "county_code": 'character varying(10) COLLATE pg_catalog."default"',
        "county": 'character varying(10) COLLATE pg_catalog."default"',
        "area_code": 'character varying(10) COLLATE pg_catalog."default"',
        "area": 'character varying(10) COLLATE pg_catalog."default"',
        "postal_code": 'character varying(10) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "phone": 'character varying(50) COLLATE pg_catalog."default"',
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # Extract
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(raw_records)

    # Transform
    data = raw_data.rename(
        columns={
            "no": "seq",
            "title": "title",
            "countycode": "county_code",
            "county": "county",
            "areacode": "area_code",
            "area": "area",
            "postalcode": "postal_code",
            "address": "address",
            "localcallservice": "phone",
        }
    )
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
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
    proj_folder="proj_new_taipei_city_dashboard", dag_folder="food_bank_ntpe"
)
dag.create_dag(etl_func=_food_bank_ntpe)
