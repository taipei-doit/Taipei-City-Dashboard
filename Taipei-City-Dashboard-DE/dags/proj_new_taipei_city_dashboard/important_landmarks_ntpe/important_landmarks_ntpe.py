from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _important_landmarks_ntpe(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    RID = "6dcff24a-838c-40fb-a9df-f1160afafe84"
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw = pd.DataFrame(raw_records)

    # Normalize columns and basic transform
    col_rename = {
        "地標名稱": "name",
        "地標類型": "landmark_type",
        "地址": "address",
        "網址": "url",
        "行政區": "district",
        "電話": "tel",
        "更新日期": "update_time",
        "objectid": "objectid",
        "twd97_x": "twd97_x",
        "twd97_y": "twd97_y",
    }
    data = raw.rename(columns=col_rename)
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # ensure numeric coordinates
    data["twd97_x"] = pd.to_numeric(data.get("twd97_x"), errors="coerce")
    data["twd97_y"] = pd.to_numeric(data.get("twd97_y"), errors="coerce")

    # create geometry (from TWD97 EPSG:3826 -> EPSG:4326)
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Point"
    gdata = add_point_wkbgeometry_column_to_df(data, data["twd97_x"], data["twd97_y"], from_crs=FROM_CRS)

    # select and order columns
    ready_data = gdata[
        [
            "data_time",
            "objectid",
            "name",
            "landmark_type",
            "district",
            "address",
            "tel",
            "url",
            "update_time",
            "wkb_geometry",
        ]
    ]

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "objectid": "integer",
        "name": 'character varying(255) COLLATE pg_catalog."default"',
        "landmark_type": 'character varying(100) COLLATE pg_catalog."default"',
        "district": 'character varying(100) COLLATE pg_catalog."default"',
        "address": 'character varying(255) COLLATE pg_catalog."default"',
        "tel": 'character varying(50) COLLATE pg_catalog."default"',
        "url": 'character varying(255) COLLATE pg_catalog."default"',
        "update_time": 'timestamp without time zone',
        "wkb_geometry": 'geometry(Point,4326)'
    }

    # Load
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    update_lasttime_in_data_to_dataset_info(engine, dag_id, ready_data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="important_landmarks_ntpe",
)


dag.create_dag(etl_func=_important_landmarks_ntpe)
