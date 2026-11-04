from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _schools_distribution(**kwargs):
    """ETL for 臺北市各級學校分布圖 (dataset 121225)."""
    import io
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

    dag_infos = kwargs.get("dag_infos") or {}
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")

    # Fetch CKAN package
    pkg_url = "https://data.gov.tw/api/3/action/package_show?id=121225"
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
        resource = resources[0]
    if resource is None:
        raise RuntimeError("No resource found in CKAN package 121225")

    resource_url = resource.get("url")
    resource_format = (resource.get("format") or "").lower()

    r2 = requests.get(resource_url, timeout=10)
    r2.raise_for_status()

    geom = False
    if "geojson" in resource_format or resource_url.endswith(".geojson"):
        jobj = r2.json()
        features = jobj.get("features") if isinstance(jobj, dict) else None
        if features is not None:
            gdf = gpd.GeoDataFrame.from_features(features)
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
        data = pd.read_csv(io.StringIO(r2.text))
        geom = False

    data["data_time"] = pd.to_datetime("now", utc=True)

    # rename heuristics
    RENAME_MAP = {
        "學校名稱": "school_name",
        "機構名稱": "school_name",
        "學校類別": "school_type",
        "學校等級": "school_level",
        "地址": "address",
        "經度": "longitude",
        "緯度": "latitude",
        "lon": "longitude",
        "lat": "latitude",
    }
    data = data.rename(columns={k: v for k, v in RENAME_MAP.items() if k in data.columns})

    # COL_MAP literal for validator (column -> SQL type)
    COL_MAP = {
        "school_name": "text",
        "school_type": "text",
        "school_level": "text",
        "address": "text",
        "latitude": "double precision",
        "longitude": "double precision",
        "wkb_geometry": "geometry(Point,4326)",
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
    }

    # add geometry if lat/lon present
    if "latitude" in data.columns and "longitude" in data.columns:
        data = add_point_wkbgeometry_column_to_df(data, lat_col="latitude", lon_col="longitude")
        geom = True

    # try convert any date-like columns (best-effort)
    if "established" in data.columns:
        data["established"] = data["established"].apply(lambda x: convert_str_to_time_format(x) if pd.notna(x) else x)

    desired_cols = [c for c in COL_MAP.keys()]
    if "data_time" not in desired_cols:
        desired_cols.append("data_time")
    cols_present = [c for c in desired_cols if c in data.columns]
    if "data_time" not in cols_present:
        cols_present.append("data_time")
    ready_data = data[cols_present].copy()

    # Load
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)

    try:
        if "wkb_geometry" in ready_data.columns:
            gdf = gpd.GeoDataFrame(ready_data, geometry="wkb_geometry")
        else:
            gdf = gpd.GeoDataFrame(ready_data)
    except Exception:
        gdf = gpd.GeoDataFrame(ready_data)

    save_geodataframe_to_postgresql(engine, gdata=gdf, load_behavior=load_behavior, default_table=default_table)

    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="schools_distribution")
dag.create_dag(etl_func=_schools_distribution)
