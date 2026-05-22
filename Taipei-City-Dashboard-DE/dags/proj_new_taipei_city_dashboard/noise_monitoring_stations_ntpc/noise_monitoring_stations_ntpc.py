from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _noise_monitoring_stations_ntpc(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
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
        "road_width": "double precision",
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    source_url = (
        "https://data.ntpc.gov.tw/api/datasets/"
        "cad88b80-8230-48d4-a8d4-ce478954fddf/json"
    )
    # NOTE: This official endpoint returns records as a list in some clients
    # and under `value` in others, which is not covered by the current
    # NewTaipeiAPIClient helper.
    response = requests.get(
        source_url,
        params={"page": 0, "size": 1000},
        timeout=60,
        proxies=kwargs.get("proxies"),
    )
    response.raise_for_status()
    body = response.json()
    records = body.get("value", []) if isinstance(body, dict) else body
    raw_data = pd.DataFrame(records)

    data = raw_data.rename(
        columns={
            "name": "station_name",
            "no": "station_no",
            "address": "address",
            "control_area": "control_area",
            "road_width": "road_width",
        }
    )
    data["road_width"] = pd.to_numeric(data["road_width"], errors="coerce")
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    source_address = "新北市" + data["address"].fillna("").astype(str)

    cleaned_address = clean_data(source_address)
    standardized_address = main_process(cleaned_address)
    _, output_address = save_data(
        source_address,
        cleaned_address,
        standardized_address,
    )
    data["address"] = output_address
    data["lng"], data["lat"] = get_addr_xy_parallel(output_address)

    gdata = add_point_wkbgeometry_column_to_df(
        data,
        x=data["lng"],
        y=data["lat"],
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
    dag_folder="noise_monitoring_stations_ntpc",
)
dag.create_dag(etl_func=_noise_monitoring_stations_ntpc)
