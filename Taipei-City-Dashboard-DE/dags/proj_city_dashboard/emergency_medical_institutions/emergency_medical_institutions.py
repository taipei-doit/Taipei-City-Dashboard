from airflow import DAG
from operators.common_pipeline import CommonDag

def _ensure_ready_table(engine, table_name, col_map):
    """建表(若不存在)。冪等,每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    sql = sql.replace(
        f"CREATE TRIGGER {table_name}_mtime",
        f"DROP TRIGGER IF EXISTS {table_name}_mtime ON public.{table_name};\n"
        f"    CREATE TRIGGER {table_name}_mtime",
    )
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))

def _emergency_medical_institutions(**kwargs):
    # === Imports(全部寫在函式內)===
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seq": "integer",
        "institution_name": "text",
        "zipcode": "text",
        "address": "text",
        "phone": "text"
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # === Extract ===
    raw_data = pd.DataFrame(get_data_taipei_api("d03e3ca2-75f0-4ce0-b20c-4e5cda7b8e2c"))
    # === Transform ===
    data = raw_data.rename(columns={
        "序號": "seq",
        "機構名稱": "institution_name",
        "郵遞區號": "zipcode",
        "地址": "address",
        "電話": "phone"
    })
    data["data_time"] = pd.to_datetime("now")
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
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, data["data_time"].max()
    )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="emergency_medical_institutions")
dag.create_dag(etl_func=_emergency_medical_institutions)
