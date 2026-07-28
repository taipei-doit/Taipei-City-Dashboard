from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _river_water_quality_ntpe(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_moenv_json_data
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "site_id": 'character varying(30) COLLATE pg_catalog."default"',
        "site_name": 'text COLLATE pg_catalog."default"',
        "county": 'character varying(20) COLLATE pg_catalog."default"',
        "township": 'character varying(30) COLLATE pg_catalog."default"',
        "basin": 'text COLLATE pg_catalog."default"',
        "river": 'text COLLATE pg_catalog."default"',
        "twd97_lon": "double precision",
        "twd97_lat": "double precision",
        "twd97_tm2x": "double precision",
        "twd97_tm2y": "double precision",
        "sample_date": "timestamp with time zone",
        "item_name": 'text COLLATE pg_catalog."default"',
        "item_eng_abbreviation": 'character varying(50) COLLATE pg_catalog."default"',
        "item_value": 'character varying(50) COLLATE pg_catalog."default"',
        "item_unit": 'character varying(50) COLLATE pg_catalog."default"',
        "note": 'text COLLATE pg_catalog."default"',
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    raw_data = pd.DataFrame(
        get_moenv_json_data(
            "WQX_P_01",
            filters_query="county,EQ,新北市",
            sort_query="SampleDate desc",
            is_proxy=False,
            timeout=60,
        )
    )
    if raw_data.empty:
        raise ValueError("MOENV WQX_P_01 returned no New Taipei records")

    data = raw_data.rename(
        columns={
            "siteid": "site_id",
            "sitename": "site_name",
            "twd97lon": "twd97_lon",
            "twd97lat": "twd97_lat",
            "twd97tm2x": "twd97_tm2x",
            "twd97tm2y": "twd97_tm2y",
            "sampledate": "sample_date",
            "itemname": "item_name",
            "itemengabbreviation": "item_eng_abbreviation",
            "itemvalue": "item_value",
            "itemunit": "item_unit",
        }
    )
    data["sample_date"] = pd.to_datetime(data["sample_date"], errors="coerce")
    data["data_time"] = data["sample_date"]
    for col in ["twd97_lon", "twd97_lat", "twd97_tm2x", "twd97_tm2y"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["sample_date", "twd97_lon", "twd97_lat"]).copy()
    gdata = add_point_wkbgeometry_column_to_df(
        data,
        x=data["twd97_lon"],
        y=data["twd97_lat"],
        from_crs=4326,
    )
    ready_data = gdata[SELECT_COLUMNS]

    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    update_lasttime_in_data_to_dataset_info(
        engine,
        dag_id,
        ready_data["data_time"].max(),
    )


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="river_water_quality_ntpe",
)
dag.create_dag(etl_func=_river_water_quality_ntpe)
