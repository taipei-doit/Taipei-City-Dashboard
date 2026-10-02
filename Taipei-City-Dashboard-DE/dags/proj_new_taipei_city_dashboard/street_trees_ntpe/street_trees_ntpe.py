from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _street_trees_ntpe(**kwargs):
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
    RID = "57f99afb-94e2-4e67-9de7-961f5e9a9e18"
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(raw_records)

    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform: pick main fields
    data = raw_data.rename(columns={
        "town_na": "town",
        "road_na": "road",
        "site": "site",
        "total": "total",
    })

    SELECT_COLUMNS = [
        "data_time",
        "town",
        "road",
        "site",
        "total",
    ]

    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None

    data = data[SELECT_COLUMNS]

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "town": 'character varying(100) COLLATE pg_catalog."default"',
        "road": 'character varying(255) COLLATE pg_catalog."default"',
        "site": 'character varying(100) COLLATE pg_catalog."default"',
        "total": 'integer',
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
    dag_folder="street_trees_ntpe",
)


dag.create_dag(etl_func=_street_trees_ntpe)
