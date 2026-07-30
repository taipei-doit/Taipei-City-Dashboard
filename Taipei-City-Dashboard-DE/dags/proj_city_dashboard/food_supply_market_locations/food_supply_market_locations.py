from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
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


def _food_supply_market_locations(**kwargs):
    import re

    import pandas as pd
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        NewTaipeiAPIClient,
        download_file,
        get_current_rid_from_page_id,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "source_city": 'character varying(20) COLLATE pg_catalog."default"',
        "source_agency": 'character varying(50) COLLATE pg_catalog."default"',
        "source_record_id": 'character varying(50) COLLATE pg_catalog."default"',
        "district": 'character varying(20) COLLATE pg_catalog."default"',
        "area_code": 'character varying(20) COLLATE pg_catalog."default"',
        "market_name": 'text COLLATE pg_catalog."default"',
        "market_type": 'character varying(50) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "phone": 'character varying(50) COLLATE pg_catalog."default"',
        "description": 'text COLLATE pg_catalog."default"',
        "opened_date": 'character varying(30) COLLATE pg_catalog."default"',
        "total_stalls": "integer",
        "vegetable_stalls": "integer",
        "fruit_stalls": "integer",
        "meat_stalls": "integer",
        "seafood_stalls": "integer",
        "poultry_stalls": "integer",
        "grain_stalls": "integer",
        "flower_stalls": "integer",
        "grocery_stalls": "integer",
        "department_store_stalls": "integer",
        "food_stalls": "integer",
        "other_stalls": "integer",
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    TAIPEI_STALLS_PAGE_ID = "f490476d-d156-4492-a463-cf3405de3b55"
    TAIPEI_BASIC_PAGE_ID = "89bebb3a-990d-4070-bd67-631a575f6d4a"
    NTPC_RID = "785be91a-caaf-4e1c-91d6-f7d616d31a45"
    FROM_CRS = 4326

    def normalize_market_name(value):
        if pd.isna(value):
            return None
        text = str(value)
        text = re.sub(r"\(.*?\)", "", text)
        text = text.replace("臺北市", "").replace("台北市", "")
        text = text.replace("公有", "").replace("市場", "")
        return text.strip()

    def to_integer(series):
        return pd.to_numeric(series, errors="coerce").astype("Int64")

    def geocode_missing_coordinates(data):
        if not Variable.get("TPGOS_GET_ADDR_XY", default_var=None):
            return data

        missing = data["address"].notna() & (data["lng"].isna() | data["lat"].isna())
        valid_address = data["address"].astype(str).str.contains(
            r"(臺北市|台北市|新北市).{0,12}區",
            regex=True,
            na=False,
        )
        missing = missing & valid_address
        if not missing.any():
            return data

        unique_addr = data.loc[missing, "address"].dropna().drop_duplicates()
        lng, lat = get_addr_xy_parallel(unique_addr, sleep_time=0.5)
        addr_xy = pd.DataFrame({"address": unique_addr, "geocoded_lng": lng, "geocoded_lat": lat})
        data = data.merge(addr_xy, on="address", how="left")
        data["lng"] = data["lng"].fillna(pd.to_numeric(data["geocoded_lng"], errors="coerce"))
        data["lat"] = data["lat"].fillna(pd.to_numeric(data["geocoded_lat"], errors="coerce"))
        return data.drop(columns=["geocoded_lng", "geocoded_lat"])

    # === Extract ===
    taipei_stalls_rid = get_current_rid_from_page_id(TAIPEI_STALLS_PAGE_ID)
    taipei_basic_rid = get_current_rid_from_page_id(TAIPEI_BASIC_PAGE_ID)
    taipei_stalls_url = (
        f"https://data.taipei/api/dataset/{TAIPEI_STALLS_PAGE_ID}"
        f"/resource/{taipei_stalls_rid}/download"
    )
    taipei_basic_url = (
        f"https://data.taipei/api/dataset/{TAIPEI_BASIC_PAGE_ID}"
        f"/resource/{taipei_basic_rid}/download"
    )

    taipei_stalls_file = download_file(
        "food_supply_market_locations_taipei_stalls.csv",
        taipei_stalls_url,
        is_proxy=False,
    )
    taipei_basic_file = download_file(
        "food_supply_market_locations_taipei_basic.csv",
        taipei_basic_url,
        is_proxy=False,
    )
    taipei_stalls_raw = pd.read_csv(taipei_stalls_file, encoding="big5")
    taipei_basic_raw = pd.read_csv(taipei_basic_file, encoding="big5")

    ntpc_client = NewTaipeiAPIClient(NTPC_RID, input_format="json")
    ntpc_raw = pd.DataFrame(ntpc_client.get_all_data(size=1000))

    # === Transform: Taipei ===
    taipei_stalls = taipei_stalls_raw.rename(
        columns={
            "序號": "source_record_id",
            "行政區": "district",
            "市場名稱": "market_name",
            "總計": "total_stalls",
            "蔬菜（數量）": "vegetable_stalls",
            "青果（數量）": "fruit_stalls",
            "獸肉（數量）": "meat_stalls",
            "漁產（數量）": "seafood_stalls",
            "家禽（數量）": "poultry_stalls",
            "糧食（數量）": "grain_stalls",
            "花卉（數量）": "flower_stalls",
            "雜貨（數量）": "grocery_stalls",
            "百貨（數量）": "department_store_stalls",
            "飲食（數量）": "food_stalls",
            "其他": "other_stalls",
        }
    )
    taipei_basic = taipei_basic_raw.rename(
        columns={
            "stitle": "basic_market_name",
            "xbody": "description",
            "xcreatedDate": "opened_date",
            "xAddress": "address",
            "GTag_longitude": "lng",
            "GTag_latitude": "lat",
        }
    )
    taipei_stalls["market_key"] = taipei_stalls["market_name"].apply(normalize_market_name)
    taipei_basic["market_key"] = taipei_basic["basic_market_name"].apply(normalize_market_name)
    taipei = taipei_stalls.merge(
        taipei_basic[
            ["market_key", "description", "opened_date", "address", "lng", "lat"]
        ],
        on="market_key",
        how="left",
    )
    taipei["source_city"] = "臺北市"
    taipei["source_agency"] = "臺北市市場處"
    taipei["area_code"] = None
    taipei["market_type"] = "公有零售市(商)場"
    taipei["phone"] = None

    stall_cols = [
        "total_stalls",
        "vegetable_stalls",
        "fruit_stalls",
        "meat_stalls",
        "seafood_stalls",
        "poultry_stalls",
        "grain_stalls",
        "flower_stalls",
        "grocery_stalls",
        "department_store_stalls",
        "food_stalls",
        "other_stalls",
    ]
    for col in stall_cols:
        taipei[col] = to_integer(taipei[col])

    # === Transform: New Taipei ===
    ntpc = ntpc_raw.rename(
        columns={
            "item": "source_record_id",
            "name": "market_name",
            "town": "district",
            "areacode": "area_code",
            "address": "address",
            "phone": "phone",
            "types": "market_type",
        }
    )
    ntpc["source_record_id"] = ntpc["source_record_id"].astype(str).str.strip()
    ntpc["source_city"] = "新北市"
    ntpc["source_agency"] = "新北市政府市場處"
    ntpc["description"] = None
    ntpc["opened_date"] = None
    ntpc["lng"] = None
    ntpc["lat"] = None
    for col in stall_cols:
        ntpc[col] = None

    data = pd.concat([taipei, ntpc], ignore_index=True, sort=False)
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data = geocode_missing_coordinates(data)
    data = data.dropna(subset=["lng", "lat"]).copy()

    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None

    data = add_point_wkbgeometry_column_to_df(
        data,
        x=data["lng"],
        y=data["lat"],
        from_crs=FROM_CRS,
    )
    data = data.drop(columns=["geometry"], errors="ignore")
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="food_supply_market_locations")
dag.create_dag(etl_func=_food_supply_market_locations)
