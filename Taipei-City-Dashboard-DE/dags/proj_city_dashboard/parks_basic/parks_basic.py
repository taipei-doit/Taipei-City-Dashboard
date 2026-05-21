from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _parks_basic(**kwargs):
    """ETL for 臺北市公園基本資料 (parks.gov.taipei API)."""
    import io
    import requests
    import pandas as pd
    import geopandas as gpd
    from sqlalchemy import create_engine

    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    dag_infos = kwargs.get("dag_infos") or {}
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")

    # NOTE: 暫無對應 utils helper,使用 inline requests。
    # NOTE: 暫無對應 utils helper,使用 inline requests。後續多支 DAG 若共用此來源,請維護者升級為 utils.extract_stage.<helper>。
    api_url = "https://parks.gov.taipei/parks/api/"
    r = requests.get(api_url, timeout=10)
    r.raise_for_status()
    records = r.json()

    data = pd.DataFrame(records)

    # Add data_time
    data["data_time"] = pd.to_datetime("now", utc=True)

    # rename heuristics
    RENAME_MAP = {
        "SeqNo": "seq_no",
        "pm_name": "park_name",
        "pm_overview": "overview",
        "pm_const_year": "established_year",
        "pm_location": "address",
        "pm_unit": "managing_unit",
        "pm_LandPublicArea": "area_m2",
        "pm_opening_s": "opening_start",
        "pm_opening_e": "opening_end",
        "pm_libie": "neighborhood",
        "pm_phone": "phone",
        "pm_sports": "sports",
        "pm_recreation": "recreation",
        "pm_service": "service",
        "pm_other": "other",
        "pm_transit": "transit",
        "pm_name_eng": "name_en",
        "pm_ecology": "ecology",
        "pm_type": "park_type",
        "pm_playtype": "play_type",
        "pm_playarea": "play_area",
        "pm_playeq": "play_eq",
        "pm_Latitude": "latitude",
        "pm_Longitude": "longitude",
    }
    data = data.rename(columns={k: v for k, v in RENAME_MAP.items() if k in data.columns})

    # COL_MAP literal required by validator
    COL_MAP = {
        "seq_no": "integer",
        "park_name": "text",
        "overview": "text",
        "established_year": "integer",
        "address": "text",
        "managing_unit": "text",
        "area_m2": "double precision",
        "opening_start": "text",
        "opening_end": "text",
        "neighborhood": "text",
        "phone": "text",
        "sports": "text",
        "recreation": "text",
        "service": "text",
        "other": "text",
        "transit": "text",
        "name_en": "text",
        "ecology": "text",
        "park_type": "text",
        "play_type": "text",
        "play_area": "text",
        "play_eq": "text",
        "latitude": "double precision",
        "longitude": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
    }

    # If lat/lon present, create wkb_geometry
    if "latitude" in data.columns and "longitude" in data.columns:
        data = add_point_wkbgeometry_column_to_df(data, lat_col="latitude", lon_col="longitude")

    # Select final columns per COL_MAP
    select_cols = [c for c in COL_MAP.keys() if c in data.columns]
    if "data_time" not in select_cols:
        select_cols.append("data_time")
    ready_data = data[select_cols].copy()

    # Load
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)

    # save as geodataframe (is_geometry=1)
    try:
        if "wkb_geometry" in ready_data.columns:
            gdf = gpd.GeoDataFrame(ready_data, geometry="wkb_geometry")
        else:
            gdf = gpd.GeoDataFrame(ready_data)
    except Exception:
        gdf = gpd.GeoDataFrame(ready_data)

    save_geodataframe_to_postgresql(engine, gdata=gdf, load_behavior=load_behavior, default_table=default_table)

    # Update lasttime
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="parks_basic")
dag.create_dag(etl_func=_parks_basic)
