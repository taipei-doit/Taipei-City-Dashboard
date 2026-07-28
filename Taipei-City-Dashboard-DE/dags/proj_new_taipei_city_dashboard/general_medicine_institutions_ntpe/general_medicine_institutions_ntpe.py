from airflow import DAG
from operators.common_pipeline import CommonDag

def _ensure_ready_table(engine, table_name, col_map):
    """建表(若不存在)。冪等,每次 DAG run 都會跑。"""
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

def _general_medicine_institutions_ntpe(**kwargs):
    # === Imports(全部寫在函式內)===
    import pandas as pd
    from sqlalchemy import create_engine
    from airflow.models import Variable
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seqno": "integer",
        "hosp_name": "text",
        "hosp_id": "text",
        "area": "text",
        "hosp_addr": "text",
        "tel": "text",
        "division": "text",
        "remark": "text",
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # === Extract ===
    raw_data = pd.DataFrame(
        NewTaipeiAPIClient("ec49095f-7383-4008-ba4f-3208068ceaa8").get_all_data(size=1000)
    )
    # === Transform ===
    data = raw_data.rename(columns={
        "seqno": "seqno",
        "hosp_name": "hosp_name",
        "hosp_id": "hosp_id",
        "area": "area",
        "hosp_addr": "hosp_addr",
        "tel": "tel",
        "division": "division",
        "remark": "remark"
    })
    data["seqno"] = range(1, len(data) + 1)
    data["data_time"] = pd.to_datetime("now")
    # === Geocode(地址→經緯度;參照 food_hygiene_award)===
    data["lng"] = None
    data["lat"] = None
    if Variable.get("TPGOS_GET_ADDR_XY", default_var=None):
        _uniq = data["hosp_addr"].dropna().drop_duplicates().tolist()
        if _uniq:
            _lng, _lat = get_addr_xy_parallel(_uniq, sleep_time=0.5)
            _axy = pd.DataFrame({"hosp_addr": _uniq, "lng": _lng, "lat": _lat})
            data = data.drop(columns=["lng", "lat"]).merge(_axy, on="hosp_addr", how="left")
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=4326, to_crs=4326, is_add_xy_columns=True
    )
    # keep-all-rows:對不到座標的列保留,wkb_geometry 設 null(非空點)
    data.loc[data["lng"].isna() | data["lat"].isna(), "wkb_geometry"] = None
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
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, data["data_time"].max()
    )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="general_medicine_institutions_ntpe")
dag.create_dag(etl_func=_general_medicine_institutions_ntpe)
