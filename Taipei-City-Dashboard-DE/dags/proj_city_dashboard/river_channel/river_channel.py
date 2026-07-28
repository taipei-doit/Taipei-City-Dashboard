from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表(若不存在)。冪等,每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _river_channel(**kwargs):
    # === Imports(全部寫在函式內)===
    import binascii
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "river_id": "character varying(64) COLLATE pg_catalog.\"default\"",
        "river_name": "text COLLATE pg_catalog.\"default\"",
        "river_class": "text COLLATE pg_catalog.\"default\"",
        "manage_unit": "text COLLATE pg_catalog.\"default\"",
        "county": "text COLLATE pg_catalog.\"default\"",
        "source_year": "integer",
        "wkb_geometry": "geometry(MultiPolygon,4326)",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # === Extract ===
    source_url = "https://gic.wra.gov.tw/gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP"
    gdf = get_shp_file(source_url, dag_id, 3826, is_verify=False)

    # === Transform ===
    # rename common Chinese field names to snake_case English. If keys not present, leave as-is.
    rename_map = {
        # 來源 RIVERPOLY shp 實際欄位為英文(RIVER_NAME/RIVER_CODE/RIVER_TYPE/RIVER_FROM);
        # 無管理單位/年度/縣市欄 → manage_unit/source_year 留 null、county 由空間過濾後另設
        "RIVER_NAME": "river_name",
        "RIVER_CODE": "river_id",
        "RIVER_TYPE": "river_class",
        "河川編號": "river_id",
        "河川代碼": "river_id",
        "河川名稱": "river_name",
        "河名": "river_name",
        "河川等級": "river_class",
        "管理單位": "manage_unit",
        "縣市": "county",
        "縣市別": "county",
        "統計年度": "source_year",
        "年度": "source_year",
    }
    # perform rename for any matching columns
    common_cols = {k: v for k, v in rename_map.items() if k in gdf.columns}
    gdata = gdf.rename(columns=common_cols)

    # ensure CRS is EPSG:4326
    if gdata.crs is not None and gdata.crs.to_string() != "EPSG:4326":
        gdata = gdata.to_crs("EPSG:4326")

    # create wkb_geometry column from geometry
    from shapely import wkb

    def _geom_to_wkb_hex(geom):
        if geom is None:
            return None
        raw = wkb.dumps(geom)
        return binascii.hexlify(raw).decode("ascii")

    gdata["wkb_geometry"] = gdata.geometry.apply(_geom_to_wkb_hex)

    # ensure data_time
    if "data_time" not in gdata.columns:
        gdata["data_time"] = pd.to_datetime("now")

    # --- Filter to Taipei City by spatial intersect ---
    # 來源 RIVERPOLY 無縣市屬性欄,無法用欄位過濾;改用縣市界 tp_taiwan_county(SRID 4326)空間相交
    # ponytail: 單一縣市界 unary_union 即可;日後若要逐河段標多縣市,改 gpd.sjoin 保留對應
    import geopandas as gpd

    _bnd = gpd.read_postgis(
        "SELECT wkb_geometry FROM tp_taiwan_county WHERE name = %(c)s",
        create_engine(ready_data_db_uri),
        geom_col="wkb_geometry",
        params={"c": "臺北市"},
    ).to_crs("EPSG:4326")
    gdata = gdata[gdata.geometry.intersects(_bnd.geometry.unary_union)].copy()
    gdata["county"] = "臺北市"

    # final column selection/alignment
    # add missing cols if any (to keep column order consistent)
    for col in SELECT_COLUMNS:
        if col not in gdata.columns:
            gdata[col] = None

    gdata = gdata[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_geodataframe_to_postgresql(
        engine,
        gdata,
        load_behavior=load_behavior,
        geometry_type="MultiPolygon",
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, gdata["data_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="river_channel")
dag.create_dag(etl_func=_river_channel)
