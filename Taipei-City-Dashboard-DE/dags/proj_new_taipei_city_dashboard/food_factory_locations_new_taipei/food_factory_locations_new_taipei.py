from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表（若不存在）。冪等，每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _food_factory_locations_new_taipei(**kwargs):
    # === Imports（全部寫在函式內，避免 Airflow 3.x parse 階段 IO） ===
    import re
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "factory_id": 'character varying(20) COLLATE pg_catalog."default"',
        "name": 'character varying(200) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "district": 'character varying(20) COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # 新北市食品工廠清冊 — data.ntpc.gov.tw OpenAPI
    NTPC_RID = "c51d5111-c300-44c9-b4f1-4b28b9929ca2"

    # === Extract ===
    client = NewTaipeiAPIClient(NTPC_RID, input_format="json")
    records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(records)

    # === Transform ===
    # 1. rename 原始欄位 → snake_case；wgs84ax / wgs84ay 直接做 lng / lat
    #    API 欄位：seqno, organizer, no, address, tax_id_number,
    #              twd97x, twd97y, wgs84ax, wgs84ay, date
    data = raw_data.rename(
        columns={
            "organizer": "name",
            "no": "factory_id",
            "address": "address",
            "wgs84ax": "lng",
            "wgs84ay": "lat",
        }
    )

    # 2. city 固定為新北市，從 address 解析行政區
    data["city"] = "新北市"
    district_pattern = re.compile(r"^新北市(.+?區)")
    data["district"] = data["address"].apply(
        lambda s: (m.group(1) if (m := district_pattern.match(s or "")) else None)
    )

    # 3. 確保 lng / lat 為 float（API 可能回字串）
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data = data.dropna(subset=["lng", "lat"])

    # 4. 產生 wkb_geometry（資料已是 WGS84，不需轉換）
    data = add_point_wkbgeometry_column_to_df(
        data,
        x=data["lng"],
        y=data["lat"],
        from_crs=4326,
        to_crs=4326,
        is_add_xy_columns=False,
    )

    # 5. 補 data_time，整理欄位順序
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
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


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="food_factory_locations_new_taipei",
)
dag.create_dag(etl_func=_food_factory_locations_new_taipei)
