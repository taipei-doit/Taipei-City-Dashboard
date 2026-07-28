from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _eco_friendly_restaurant(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from airflow.models import Variable
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    RID = "d706f428-b2c7-4591-9ebf-9f5cd7408f47"

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "seq": "integer",
        "restaurant_category": 'text COLLATE pg_catalog."default"',
        "restaurant_name": 'text COLLATE pg_catalog."default"',
        "phone": 'character varying(50) COLLATE pg_catalog."default"',
        "ext": 'character varying(20) COLLATE pg_catalog."default"',
        "mobile": 'character varying(50) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "extra_eco_actions": 'text COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    raw_data = get_data_taipei_api(RID, output_format="dataframe")

    data = raw_data.rename(
        columns={
            "序號": "seq",
            "餐廳類別": "restaurant_category",
            "餐廳名稱": "restaurant_name",
            "餐廳電話": "phone",
            "分機": "ext",
            "手機號碼": "mobile",
            "餐廳地址": "address",
            "額外環保作為": "extra_eco_actions",
        }
    )
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    data["data_time"] = convert_str_to_time_format(data["data_time"])
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


dag = CommonDag(
    proj_folder="proj_city_dashboard", dag_folder="eco_friendly_restaurant"
)
dag.create_dag(etl_func=_eco_friendly_restaurant)
