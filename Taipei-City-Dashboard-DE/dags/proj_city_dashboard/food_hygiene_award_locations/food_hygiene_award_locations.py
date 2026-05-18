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


def _food_hygiene_award_locations(**kwargs):
    import re

    import pandas as pd
    import requests
    import urllib3
    from airflow.models import Variable
    from sqlalchemy import create_engine
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

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
        "award_year": "integer",
        "grade": 'character varying(20) COLLATE pg_catalog."default"',
        "business_name": 'text COLLATE pg_catalog."default"',
        "registration_no": 'character varying(50) COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "district": 'character varying(20) COLLATE pg_catalog."default"',
        "area_code": 'character varying(20) COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "source_record_id": 'character varying(50) COLLATE pg_catalog."default"',
        "award_image_url": 'text COLLATE pg_catalog."default"',
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    TAIPEI_PAGE_ID = "59579c19-a561-4564-8c0f-545bfb32c0f6"
    NTPC_API_URL = "https://foodtracer.health.ntpc.gov.tw/FoodMap/GetFoodAwardMarkers"
    NTPC_DISTRICTS = (
        "萬里區,金山區,板橋區,汐止區,深坑區,石碇區,瑞芳區,平溪區,雙溪區,貢寮區,"
        "新店區,坪林區,烏來區,永和區,中和區,土城區,三峽區,樹林區,鶯歌區,三重區,"
        "新莊區,泰山區,林口區,蘆洲區,五股區,八里區,淡水區,三芝區,石門區"
    )
    FROM_CRS = 4326

    # === Extract ===
    taipei_rid = get_current_rid_from_page_id(TAIPEI_PAGE_ID)
    taipei_raw = get_data_taipei_api(taipei_rid, output_format="dataframe")

    # NOTE: 暫無對應 utils helper,使用 inline requests。後續多支 DAG 若共用此來源,請維護者升級為 utils.extract_stage.<helper>。
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ntpc_res = requests.post(
        NTPC_API_URL,
        data={"ZoneID": NTPC_DISTRICTS},
        timeout=60,
        proxies=kwargs.get("proxies"),
        verify=False,
    )
    ntpc_res.raise_for_status()
    ntpc_raw = pd.DataFrame(ntpc_res.json())

    # === Transform ===
    taipei = taipei_raw.rename(
        columns={
            "行政區域代碼": "area_code",
            "業者名稱店名": "business_name",
            "食品業者登錄字號": "registration_no",
            "地址": "address",
            "評核結果": "grade",
        }
    )
    taipei["source_city"] = "臺北市"
    taipei["source_agency"] = "臺北市政府衛生局"
    taipei["source_record_id"] = taipei.get("_id")
    taipei["award_year"] = None
    taipei["award_image_url"] = None
    taipei["district"] = taipei["address"].str.extract(r"臺北市([^市縣]{2}區)")
    taipei["lng"] = None
    taipei["lat"] = None
    taipei["data_time"] = convert_str_to_time_format(taipei["data_time"])

    # 臺北來源無座標；若 Airflow 有 TPGOS key，使用既有地址工具補點位。
    if Variable.get("TPGOS_GET_ADDR_XY", default_var=None):
        unique_addr = taipei["address"].dropna().drop_duplicates()
        lng, lat = get_addr_xy_parallel(unique_addr, sleep_time=0.5)
        addr_xy = pd.DataFrame({"address": unique_addr, "lng": lng, "lat": lat})
        taipei = taipei.drop(columns=["lng", "lat"]).merge(addr_xy, on="address", how="left")

    ntpc = ntpc_raw.rename(
        columns={
            "id": "source_record_id",
            "lon": "lng",
            "lat": "lat",
            "label": "business_name",
            "Address": "address",
            "Name": "grade",
            "url": "award_image_url",
        }
    )
    ntpc["source_city"] = "新北市"
    ntpc["source_agency"] = "新北市政府衛生局"
    ntpc["registration_no"] = None
    ntpc["area_code"] = None
    ntpc["district"] = ntpc["address"].str.extract(r"^([^市縣]{2,3}區)")
    ntpc["award_year"] = ntpc["grade"].apply(
        lambda value: int(re.search(r"(\d{3})年度", str(value)).group(1))
        if re.search(r"(\d{3})年度", str(value))
        else None
    )
    ntpc["grade"] = ntpc["grade"].astype(str).str.replace(r"^\d{3}年度\s*", "", regex=True)
    ntpc["award_image_url"] = ntpc["award_image_url"].apply(
        lambda value: f"https://foodtracer.health.ntpc.gov.tw{value}"
        if isinstance(value, str) and value.startswith("/")
        else value
    )
    ntpc["lng"] = pd.to_numeric(ntpc["lng"], errors="coerce")
    ntpc["lat"] = pd.to_numeric(ntpc["lat"], errors="coerce")
    ntpc["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    data = pd.concat([taipei, ntpc], ignore_index=True, sort=False)
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="food_hygiene_award_locations")
dag.create_dag(etl_func=_food_hygiene_award_locations)
