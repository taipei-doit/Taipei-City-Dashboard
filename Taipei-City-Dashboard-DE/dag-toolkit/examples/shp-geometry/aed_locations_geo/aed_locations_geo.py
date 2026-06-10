from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _aed_locations_geo(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "aed_id": 'character varying(20) COLLATE pg_catalog."default"',
        "name": 'character varying(200) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    SHP_URL = "https://example.gov.tw/aed_locations.zip"
    FROM_CRS = 4326

    # === Extract ===
    raw_gdf = get_shp_file(
        url=SHP_URL,
        dag_id=dag_id,
        from_crs=FROM_CRS,
        data_path=data_path,
        proxies=proxies,
    )

    # === Transform ===
    data = raw_gdf.rename(
        columns={
            "AED_ID": "aed_id",
            "NAME": "name",
            "ADDRESS": "address",
        }
    )
    data["lng"] = data.geometry.x
    data["lat"] = data.geometry.y
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    data = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    data = data.drop(columns=["geometry"], errors="ignore")
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata=data,
        load_behavior=load_behavior,
        geometry_type="Point",
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="aed_locations_geo")
dag.create_dag(etl_func=_aed_locations_geo)
