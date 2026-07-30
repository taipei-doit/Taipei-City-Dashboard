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


def _organic_farm_locations(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient, get_current_rid_from_page_id, get_data_taipei_api
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
        "source_record_id": 'character varying(50) COLLATE pg_catalog."default"',
        "farm_name": 'text COLLATE pg_catalog."default"',
        "operator_name": 'text COLLATE pg_catalog."default"',
        "address": 'text COLLATE pg_catalog."default"',
        "district": 'character varying(20) COLLATE pg_catalog."default"',
        "phone": 'text COLLATE pg_catalog."default"',
        "certification_no": 'text COLLATE pg_catalog."default"',
        "certification_type": 'character varying(30) COLLATE pg_catalog."default"',
        "expire_date": "date",
        "farm_area_hectare": "double precision",
        "food_education": "boolean",
        "beekeeping": "boolean",
        "chicken_raising": "boolean",
        "note": 'text COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    TAIPEI_PAGE_ID = "32aea2da-14a7-47b6-a687-57e29c1ad4a7"
    NTPC_DATASET_ID = "fc30f585-66d9-4233-a65e-c650d177ebfe"
    FROM_CRS = 4326

    def _to_bool(value):
        if pd.isna(value):
            return False
        text = str(value).strip()
        return text in {"V", "v", "Y", "y", "是", "有", "養", "1", "true", "True"}

    # === Extract ===
    taipei_rid = get_current_rid_from_page_id(TAIPEI_PAGE_ID)
    taipei_raw = get_data_taipei_api(taipei_rid, output_format="dataframe")

    ntpc_client = NewTaipeiAPIClient(NTPC_DATASET_ID)
    ntpc_raw = pd.DataFrame(ntpc_client.get_all_data(size=1000))

    # === Transform ===
    taipei = taipei_raw.rename(
        columns={
            "_id": "source_record_id",
            "農場名稱": "farm_name",
            "農友姓名": "operator_name",
            "通訊地址": "address",
            "認證字號": "certification_no",
            "面積（公頃）": "farm_area_hectare",
            "食農教育體驗": "food_education",
            "飼養蜜蜂": "beekeeping",
            "飼養雞隻": "chicken_raising",
            "備註": "note",
        }
    )
    taipei["source_city"] = "臺北市"
    taipei["source_agency"] = "臺北市政府產業發展局"
    taipei["district"] = taipei["address"].str.extract(r"臺北市([^市縣]{2,3}區)")
    taipei["phone"] = None
    taipei["certification_type"] = "有機"
    taipei["expire_date"] = None
    taipei["farm_area_hectare"] = pd.to_numeric(taipei["farm_area_hectare"], errors="coerce")
    taipei["food_education"] = taipei["food_education"].apply(_to_bool)
    taipei["beekeeping"] = taipei["beekeeping"].apply(_to_bool)
    taipei["chicken_raising"] = taipei["chicken_raising"].apply(_to_bool)
    taipei["data_time"] = convert_str_to_time_format(taipei["data_time"])

    ntpc = ntpc_raw.rename(
        columns={
            "no": "source_record_id",
            "operators": "operator_name",
            "counties": "source_city",
            "town": "district",
            "address": "address",
            "phone": "phone",
            "produce": "farm_name",
            "date": "expire_date",
            "farm": "farm_area_hectare",
            "test": "certification_type",
        }
    )
    ntpc["source_agency"] = "新北市政府農業局"
    ntpc["certification_no"] = None
    ntpc["food_education"] = None
    ntpc["beekeeping"] = None
    ntpc["chicken_raising"] = None
    ntpc["note"] = None
    ntpc["farm_area_hectare"] = pd.to_numeric(ntpc["farm_area_hectare"], errors="coerce")
    ntpc["expire_date"] = pd.to_datetime(ntpc["expire_date"], format="%Y/%m/%d", errors="coerce").dt.date
    ntpc["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    data = pd.concat([taipei, ntpc], ignore_index=True, sort=False)
    data["data_time"] = convert_str_to_time_format(
        data["data_time"].astype(str),
        errors="coerce",
    )
    data = data.dropna(subset=["address"]).copy()
    data["address"] = data["address"].astype(str).str.strip()
    data = data[data["address"] != ""].copy()

    valid_address = data["address"].str.contains(
        r"(臺北市|台北市|新北市).{0,12}區",
        regex=True,
        na=False,
    )
    unique_addr = data.loc[valid_address, "address"].drop_duplicates()
    lng, lat = get_addr_xy_parallel(unique_addr, sleep_time=0.5)
    addr_xy = pd.DataFrame({"address": unique_addr, "lng": lng, "lat": lat})
    data = data.merge(addr_xy, on="address", how="left")
    data = data.dropna(subset=["lng", "lat"]).copy()

    data = add_point_wkbgeometry_column_to_df(
        data,
        x=data["lng"],
        y=data["lat"],
        from_crs=FROM_CRS,
    )
    data = data.drop(columns=["geometry"], errors="ignore")

    for col in SELECT_COLUMNS:
        if col not in data.columns:
            data[col] = None
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="organic_farm_locations")
dag.create_dag(etl_func=_organic_farm_locations)
