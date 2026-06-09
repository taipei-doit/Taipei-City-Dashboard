from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _repair_subsidy_application_status(**kwargs):
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

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "縣市": 'character varying(10) COLLATE pg_catalog."default"',
        "項目": "integer",
        "修繕住宅貸款利息補貼申請戶數": "integer",
        "修繕住宅貸款利息補貼計畫戶數": "integer",
        "修繕住宅貸款利息補貼核定戶數": "integer",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    NEW_TAIPEI_RID = "502d1589-3693-4f2c-9c05-22e3ec37330d"

    def _to_ad_year(value):
        year = pd.to_numeric(
            pd.Series(value, dtype="string").str.extract(r"(\d+)", expand=False),
            errors="coerce",
        )
        return year.mask(year < 1911, year + 1911).astype("Int64")

    def _to_int(series):
        return pd.to_numeric(
            series.astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        ).astype("Int64")

    data_time = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S+08")

    # === Extract ===
    ntpc_client = NewTaipeiAPIClient(NEW_TAIPEI_RID, input_format="json")
    raw_data = pd.DataFrame(ntpc_client.get_all_data(size=1000))

    # === Transform ===
    data = raw_data.rename(
        columns={
            "year": "項目",
            "repair_apply_num": "修繕住宅貸款利息補貼申請戶數",
            "repair_project_num": "修繕住宅貸款利息補貼計畫戶數",
            "repair_ok_num": "修繕住宅貸款利息補貼核定戶數",
        }
    )
    data["縣市"] = "新北市"
    data["項目"] = _to_ad_year(data["項目"])
    for col in [
        "修繕住宅貸款利息補貼申請戶數",
        "修繕住宅貸款利息補貼計畫戶數",
        "修繕住宅貸款利息補貼核定戶數",
    ]:
        data[col] = _to_int(data[col])
    data["data_time"] = data_time
    data = data.sort_values("項目").reset_index(drop=True)
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


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="repair_subsidy_application_status",
)
dag.create_dag(etl_func=_repair_subsidy_application_status)
