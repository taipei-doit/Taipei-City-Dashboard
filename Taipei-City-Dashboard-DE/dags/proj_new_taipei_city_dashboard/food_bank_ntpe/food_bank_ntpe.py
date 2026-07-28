from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _food_bank_ntpe(**kwargs):
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

    RID = "1c1d0066-a4e7-4753-b8bc-d7728d5f3e04"

    COL_MAP = {
        "data_time": 'timestamp with time zone DEFAULT CURRENT_TIMESTAMP',
        "seq": "integer",
        "title": 'text COLLATE pg_catalog."default"',
        "county_code": 'character varying(10) COLLATE pg_catalog."default"',
        "county": 'character varying(10) COLLATE pg_catalog."default"',
        "area_code": 'character varying(10) COLLATE pg_catalog."default"',
        "area": 'character varying(10) COLLATE pg_catalog."default"',
        "postal_code": 'character varying(10) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "phone": 'character varying(50) COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # Extract
    client = NewTaipeiAPIClient(RID, input_format="json")
    raw_records = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(raw_records)

    # Transform
    data = raw_data.rename(
        columns={
            "no": "seq",
            "title": "title",
            "countycode": "county_code",
            "county": "county",
            "areacode": "area_code",
            "area": "area",
            "postalcode": "postal_code",
            "address": "address",
            "localcallservice": "phone",
        }
    )
    data["seq"] = pd.to_numeric(data["seq"], errors="coerce").astype("Int64")
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
    # 來源地址含全形數字(如 ２５８),轉半形
    _fw = str.maketrans("０１２３４５６７８９", "0123456789")
    data["address"] = data["address"].map(lambda s: s.translate(_fw) if isinstance(s, str) else s)
    # 範圍門牌(如 550.552號 / 196&198號 / 122,124號 / 424,424之1號)TPGOS 只認單一門牌 → 取第一個號碼
    data["address"] = data["address"].str.replace(r"(\d+)\s*[．。.，,、＆&]\s*\d+(?:之\d+)?號", r"\1號", regex=True)
    # === Geocode ===
    # 來源 address 只有路段門牌、缺縣市/行政區(在 county/area 欄),需組完整地址才查得到 TPGOS
    _geo = (data["county"].fillna("") + data["area"].fillna("") + data["address"].fillna("")).str.strip()
    data["lng"] = None
    data["lat"] = None
    if Variable.get("TPGOS_GET_ADDR_XY", default_var=None):
        _uniq = _geo[_geo != ""].drop_duplicates().tolist()
        if _uniq:
            _lng, _lat = get_addr_xy_parallel(_uniq, sleep_time=0.5)
            _axy = pd.DataFrame({"_geo": _uniq, "lng": _lng, "lat": _lat})
            data = data.drop(columns=["lng", "lat"]).assign(_geo=_geo).merge(_axy, on="_geo", how="left").drop(columns=["_geo"])
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=4326, to_crs=4326, is_add_xy_columns=True
    )
    # keep-all-rows:對不到座標的列保留,wkb_geometry 設 null(非空點)
    data.loc[data["lng"].isna() | data["lat"].isna(), "wkb_geometry"] = None
    data = data[SELECT_COLUMNS]

    # Load
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
    proj_folder="proj_new_taipei_city_dashboard", dag_folder="food_bank_ntpe"
)
dag.create_dag(etl_func=_food_bank_ntpe)
