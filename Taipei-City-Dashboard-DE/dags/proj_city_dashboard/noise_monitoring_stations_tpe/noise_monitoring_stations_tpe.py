from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _noise_monitoring_stations_tpe(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
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
        "station_name": 'text COLLATE pg_catalog."default"',
        "station_no": 'character varying(30) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "control_area": 'character varying(10) COLLATE pg_catalog."default"',
        "monitor_type": 'character varying(50) COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    page_id = "e2f4ebf5-bffa-40af-8056-383893721731"
    rid = get_current_rid_from_page_id(page_id)
    raw_data = get_data_taipei_api(rid, output_format="dataframe")

    data = raw_data.rename(
        columns={
            "測點名稱": "station_name",
            "測點編號": "station_no",
            "測點地址": "address",
            "管制區類別": "control_area",
            "測點性質": "monitor_type",
            "經度": "source_lng",
            "緯度": "source_lat",
        }
    )
    data["source_lng"] = pd.to_numeric(data["source_lng"], errors="coerce")
    data["source_lat"] = pd.to_numeric(data["source_lat"], errors="coerce")
    data = data.dropna(subset=["source_lng", "source_lat"]).copy()

    gdata = add_point_wkbgeometry_column_to_df(
        data,
        x=data["source_lng"],
        y=data["source_lat"],
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
    proj_folder="proj_city_dashboard",
    dag_folder="noise_monitoring_stations_tpe",
)
dag.create_dag(etl_func=_noise_monitoring_stations_tpe)
