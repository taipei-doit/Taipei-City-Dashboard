from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _green_store_ntpe(**kwargs):
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

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seq": "integer",
        "store_name": 'text COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "store_code": 'character varying(20) COLLATE pg_catalog."default"',
        "contact_phone": 'character varying(50) COLLATE pg_catalog."default"',
        "store_type": 'character varying(50) COLLATE pg_catalog."default"',
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "county_code": 'character varying(10) COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    RID = "6ccd0274-0c09-43b0-98fc-4d5222a71e8b"

    # === Extract ===
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(raw_records)

    # === Transform ===
    data = raw_data.rename(
        columns={
            "seqno": "seq",
            "name": "store_name",
            "address": "address",
            "number": "store_code",
            "localcallservice": "contact_phone",
            "type": "store_type",
            "city": "city",
            "countycode": "county_code",
        }
    )
    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    # 來源地址開頭帶郵遞區號(如「220新北市…」),TPGOS 對不到 → 去掉開頭 3-6 碼郵遞區號
    data["address"] = data["address"].str.replace(r"^\s*\d{3,6}\s*", "", regex=True)
    # === Geocode(地址→經緯度;參照 food_hygiene_award)===
    data["lng"] = None
    data["lat"] = None
    if Variable.get("TPGOS_GET_ADDR_XY", default_var=None):
        _uniq = data["address"].dropna().drop_duplicates().tolist()
        if _uniq:
            _lng, _lat = get_addr_xy_parallel(_uniq, sleep_time=0.5)
            _axy = pd.DataFrame({"address": _uniq, "lng": _lng, "lat": _lat})
            data = data.drop(columns=["lng", "lat"]).merge(_axy, on="address", how="left")
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
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard", dag_folder="green_store_ntpe"
)
dag.create_dag(etl_func=_green_store_ntpe)
