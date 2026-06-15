from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from utils.ready_table_schema import ensure_ready_table

    ensure_ready_table(
        engine,
        table_name,
        col_map,
        {
            "縣市": "city",
            "項目": "year",
            "自購住宅貸款利息補貼申請戶數": "application_households",
            "自購住宅貸款利息補貼計畫戶數": "planned_households",
            "自購住宅貸款利息補貼核定戶數": "approved_households",
        },
    )


def _purchase_subsidy_application_status(**kwargs):
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
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "year": "integer",
        "application_households": "integer",
        "planned_households": "integer",
        "approved_households": "integer",
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

    # === Transform ===
    data = taipei_raw.rename(
        columns={
            "項目": "year",
            "自購住宅貸款利息補貼申請戶數": "application_households",
            "自購住宅貸款利息補貼計畫戶數": "planned_households",
            "自購住宅貸款利息補貼核定戶數": "approved_households",
        }
    )
    data["city"] = "臺北市"
    data["year"] = _to_ad_year(data["year"])
    data = data[data["year"] <= 2022]

    # === Normalize ===
    for col in [
        "application_households",
        "planned_households",
        "approved_households",
    ]:
        data[col] = _to_int(data[col])
    data["data_time"] = data_time
    data = data.sort_values("year").reset_index(drop=True)
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
    dag_folder="purchase_subsidy_application_status",
)
dag.create_dag(etl_func=_purchase_subsidy_application_status)
