from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表（若不存在）。冪等，每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    sql = sql.replace(
        f"CREATE TRIGGER {table_name}_mtime",
        f"DROP TRIGGER IF EXISTS {table_name}_mtime ON public.{table_name};\n"
        f"    CREATE TRIGGER {table_name}_mtime",
    )
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _schools_ntpe(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
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

    # 新北市重要地標資訊（政府機關/學校/車站…混合），篩出學校學制
    RID = "6dcff24a-838c-40fb-a9df-f1160afafe84"
    SCHOOL_TYPES = ["國民小學", "國民中學", "完全中學", "高中職", "大專院校"]
    SOURCE_CRS = 3826  # TWD97 TM2（twd97_x / twd97_y）

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seq": "integer",
        "school_type": 'character varying(20) COLLATE pg_catalog."default"',
        "school_name": 'text COLLATE pg_catalog."default"',
        "county": 'character varying(10) COLLATE pg_catalog."default"',
        "district": 'character varying(10) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "phone": 'character varying(50) COLLATE pg_catalog."default"',
        "website": 'text COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # === Extract ===
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_data = pd.DataFrame(client.get_all_data(size=1000))

    # === Transform ===
    data = raw_data.rename(
        columns={
            "objectid": "seq",
            "地標類型": "school_type",
            "地標名稱": "school_name",
            "行政區": "district",
            "地址": "address",
            "電話": "phone",
            "網址": "website",
        }
    )
    # 篩出學校學制（其餘地標：避難收容/警察/捷運/醫院…排除）
    data = data[data["school_type"].isin(SCHOOL_TYPES)].copy()
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    data["county"] = "新北市"
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    # 座標 TWD97 TM2 (EPSG:3826) → WGS84 (EPSG:4326)，自動補 lng / lat
    tm_x = pd.to_numeric(data["twd97_x"], errors="coerce")
    tm_y = pd.to_numeric(data["twd97_y"], errors="coerce")
    data = add_point_wkbgeometry_column_to_df(
        data, x=tm_x, y=tm_y, from_crs=SOURCE_CRS, to_crs=4326, is_add_xy_columns=True
    )
    # keep-all-rows：無座標的列保留，wkb_geometry 設 null
    data.loc[tm_x.isna() | tm_y.isna(), "wkb_geometry"] = None
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata=data,
        geometry_type="Point",
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard", dag_folder="schools_ntpe"
)
dag.create_dag(etl_func=_schools_ntpe)
