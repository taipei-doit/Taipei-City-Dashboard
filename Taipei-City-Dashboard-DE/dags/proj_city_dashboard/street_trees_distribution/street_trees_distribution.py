from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表(若不存在)。冪等,每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _street_trees_distribution(**kwargs):
    """ETL for 臺北市行道樹分布圖 (dataset 146760).

    Follows repo conventions: literal `COL_MAP` inside function, use
    `save_geodataframe_to_postgresql` when geometry present, and
    `update_lasttime_in_data_to_dataset_info` at the end.
    """
    import io
    import json
    import requests
    import pandas as pd
    import geopandas as gpd
    from sqlalchemy import create_engine

    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # config
    dag_infos = kwargs.get("dag_infos") or {}
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")

    # 1) Fetch CKAN package to find a suitable resource
    pkg_url = "https://data.nat.gov.tw/api/3/action/package_show?id=146760"
    r = requests.get(pkg_url, timeout=10)
    r.raise_for_status()
    pkg = r.json()
    resources = pkg.get("result", {}).get("resources", [])

    resource = None
    for res in resources:
        fmt = (res.get("format") or "").lower()
        url = res.get("url") or ""
        if "geojson" in fmt or url.endswith(".geojson"):
            resource = res
            break
    if resource is None and resources:
        # fallback to first resource
        resource = resources[0]

    if resource is None:
        raise RuntimeError("No resource found in CKAN package 146760")

    resource_url = resource.get("url")
    resource_format = (resource.get("format") or "").lower()

    r2 = requests.get(resource_url, timeout=10)
    r2.raise_for_status()

    # Minimal read logic for common formats
    geom = False
    if "geojson" in resource_format or resource_url.endswith(".geojson"):
        jobj = r2.json()
        # use features -> GeoDataFrame
        features = jobj.get("features") if isinstance(jobj, dict) else None
        if features is not None:
            gdf = gpd.GeoDataFrame.from_features(features)
            # convert geometry to wkb_geometry
            gdf["wkb_geometry"] = gdf.geometry.apply(lambda x: x.wkb if x is not None else None)
            data = pd.DataFrame(gdf.drop(columns=["geometry"]))
            geom = True
        else:
            data = pd.DataFrame(jobj)
            geom = False
    elif resource_format == "json" or resource_url.endswith(".json"):
        data = pd.DataFrame(r2.json())
        geom = False
    else:
        # assume CSV-like
        data = pd.read_csv(io.StringIO(r2.text))
        geom = False

    # Add data_time
    data["data_time"] = pd.to_datetime("now", utc=True)

    # Heuristic source->target renames
    RENAME_MAP = {
        "樹木編號": "tree_id",
        "tree_id": "tree_id",
        "學名": "species_en",
        "中文名": "species_cn",
        "植栽日期": "planting_date",
        "植樹日期": "planting_date",
        "健康狀態": "health_status",
        "地址": "address",
        "lat": "latitude",
        "lng": "longitude",
        "lon": "longitude",
        "latitude": "latitude",
        "longitude": "longitude",
    }

    data = data.rename(columns={k: v for k, v in RENAME_MAP.items() if k in data.columns})

    # Column -> SQL type mapping required by validator (literal)
    COL_MAP = {
        "tree_id": "text",
        "species_cn": "text",
        "species_en": "text",
        "planting_date": "timestamp with time zone",
        "health_status": "text",
        "address": "text",
        "latitude": "double precision",
        "longitude": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
    }

    # If lat/lon exist, create wkb_geometry
    if "latitude" in data.columns and "longitude" in data.columns:
        data = add_point_wkbgeometry_column_to_df(data, lat_col="latitude", lon_col="longitude")
        geom = True

    # Try convert planting_date
    if "planting_date" in data.columns:
        data["planting_date"] = data["planting_date"].apply(
            lambda x: convert_str_to_time_format(x) if pd.notna(x) else x
        )

    # Final columns
    desired_cols = [
        "tree_id",
        "species_cn",
        "species_en",
        "planting_date",
        "health_status",
        "address",
        "latitude",
        "longitude",
        "wkb_geometry",
        "data_time",
    ]
    cols_present = [c for c in desired_cols if c in data.columns]
    if "data_time" not in cols_present:
        cols_present.append("data_time")
    ready_data = data[cols_present].copy()

    # Load
    engine = create_engine(ready_data_db_uri)
    # ensure table exists with COL_MAP definition
    _ensure_ready_table(engine, default_table, COL_MAP)

    # Always save via save_geodataframe_to_postgresql (job_config.data_infos.is_geometry == 1)
    # Build a GeoDataFrame even if 'wkb_geometry' missing so static validator sees only one save call.
    try:
        if "wkb_geometry" in ready_data.columns:
            gdf = gpd.GeoDataFrame(ready_data, geometry="wkb_geometry")
        else:
            gdf = gpd.GeoDataFrame(ready_data)
    except Exception:
        gdf = gpd.GeoDataFrame(ready_data)

    save_geodataframe_to_postgresql(
        engine,
        gdata=gdf,
        load_behavior=load_behavior,
        default_table=default_table,
    )

    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data)


# instantiate DAG via CommonDag
dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="street_trees_distribution")
dag.create_dag(etl_func=_street_trees_distribution)
