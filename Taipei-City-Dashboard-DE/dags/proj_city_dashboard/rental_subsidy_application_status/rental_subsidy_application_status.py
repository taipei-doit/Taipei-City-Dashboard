from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _rental_subsidy_application_status(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
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
        "租金補貼申請戶數": "integer",
        "租金補貼計畫戶數": "integer",
        "租金補貼核定戶數": "integer",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    TAIPEI_PAGE_ID = "6297943a-1e71-480d-967c-635855df66fe"

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
    taipei_rid = get_current_rid_from_page_id(TAIPEI_PAGE_ID)
    taipei_raw = pd.DataFrame(get_data_taipei_api(taipei_rid))

    # === Transform: Taipei ===
    data = taipei_raw.rename(
        columns={
            "項目": "項目",
            "租金補貼申請戶數": "租金補貼申請戶數",
            "租金補貼計畫戶數": "租金補貼計畫戶數",
            "租金補貼核定戶數": "租金補貼核定戶數",
        }
    )
    data["縣市"] = "臺北市"
    data["項目"] = _to_ad_year(data["項目"])
    data = data[data["項目"] <= 2021]

    # === Normalize ===
    for col in ["租金補貼申請戶數", "租金補貼計畫戶數", "租金補貼核定戶數"]:
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
    proj_folder="proj_city_dashboard",
    dag_folder="rental_subsidy_application_status",
)
dag.create_dag(etl_func=_rental_subsidy_application_status)
