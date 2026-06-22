from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表（若不存在）。冪等，每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _food_factory_locations_taipei(**kwargs):
    # === Imports（全部寫在函式內，避免 Airflow 3.x parse 階段 IO） ===
    import os
    import re
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
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

    # 北市資料源（data.gov.tw 121252）為全行業登記工廠，需依工廠名稱過濾食品相關
    FOOD_NAME_REGEX = (
        r"食品|食材|食物|食堂|餐飲|餐盒|餐廳|餐館|空廚|團膳|廚房|"
        r"烘焙|西點|麵包|製麵|麵店|麵屋|菓子|糕點|糕餅|"
        r"油飯|製冰|冰品|醬油|醬料|釀造|茶莊|茶行|咖啡|"
        r"農產|肉品|乳品|飲料|點心|糖果|啤酒|製酒|早餐|調味"
    )

    SOURCE_URL = (
        "https://data.taipei/api/dataset/c8215f0d-20fa-4350-bcd9-da82432c2c9d/"
        "resource/db839b8c-bcbf-4b82-ab54-4d025df79b3c/download"
    )
    SOURCE_ENCODING = "utf-8"
    SOURCE_CRS = 3826  # TWD97 TM2 (北市座標系統)

    # === Extract ===
    # NOTE: 暫無對應 utils helper 處理 data.gov.tw 直接下載連結，使用 utils.extract_stage.download_file
    # 與 pandas 配合。若後續多支 DAG 共用此來源，請維護者評估升級為 utils.extract_stage.<helper>。
    local_path = os.path.join(data_path, dag_id, "raw.csv")
    download_file(os.path.join(dag_id, "raw.csv"), SOURCE_URL)
    raw_data = pd.read_csv(local_path, encoding=SOURCE_ENCODING)

    # === Transform ===
    # 1. rename 原始欄位 → snake_case
    data = raw_data.rename(
        columns={
            "REGI_ID": "factory_id",
            "FACT_NAME": "name",
            "FACT_ADDR": "address",
            "ADDR_X": "tm_x",
            "ADDR_Y": "tm_y",
        }
    )

    # 2. 過濾食品相關工廠（北市資料源無業別欄，以工廠名稱關鍵字辨識）
    data = data[data["name"].str.contains(FOOD_NAME_REGEX, na=False, regex=True)]

    # 3. 從地址解析行政區（city 固定為臺北市）
    data["city"] = "臺北市"
    district_pattern = re.compile(r"^臺北市(.+?區)")
    data["district"] = data["address"].apply(
        lambda s: (m.group(1) if (m := district_pattern.match(s or "")) else None)
    )

    # 4. 座標 TM2 (EPSG:3826) → WGS84 (EPSG:4326)，並產生 wkb_geometry
    #    add_point_wkbgeometry_column_to_df 會自動加上 lng / lat 兩欄（WGS84）。
    data = add_point_wkbgeometry_column_to_df(
        data,
        x=data["tm_x"],
        y=data["tm_y"],
        from_crs=SOURCE_CRS,
        to_crs=4326,
        is_add_xy_columns=True,
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="food_factory_locations_taipei")
dag.create_dag(etl_func=_food_factory_locations_taipei)
