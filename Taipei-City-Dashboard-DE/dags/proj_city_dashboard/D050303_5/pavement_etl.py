from airflow import DAG
from operators.common_pipeline import CommonDag

PROJ_FOLDER = "proj_city_dashboard"

# 加一段回填資料


def pavement_etl(file_name, web_url, page_id, rank_index, geometry_type, **kwargs):
    from utils.extract_stage import download_file
    import pandas as pd
    import geopandas as gpd
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from sqlalchemy import create_engine

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_path = kwargs.get("data_path")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Manually set
    PAGE_ID = page_id
    SET_CRS = 3826
    FROM_CRS = 4326
    filename = file_name
    url = web_url
    encoding = "UTF-8"

    # Extract
    local_file = download_file(filename, url, is_proxy=False)
    raw_data = gpd.read_file(local_file, encoding=encoding)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID, rank=rank_index)

    # colname
    # Read
    data = raw_data.copy()
    # Drop columns
    drop_col = ['id', '項次', '體積', '圖形']
    data.drop(columns=drop_col, inplace=True)
    # Rename
    name_dict = {'名稱': 'name', '面積': 'area'}
    data.rename(columns=name_dict, inplace=True)
    # Set crs
    data = data.set_crs(epsg=SET_CRS)
    # Calculate area seperately
    if geometry_type == "MultiPolygon":
        # Keep only Multipolygon
        data = data[data.geom_type == geometry_type]
        # Calculate area(acre)
        data['area'] = (data['geometry'].area/10000).round(2)
    elif geometry_type == "MultiLineString":
        # Keep only MultiLineString
        data = data[data.geom_type == geometry_type]
        # Buffer for mapbox view
        data['geometry'] = data['geometry'].buffer(0.5)
        # Calculate area(acre)
        data['area'] = (data['area'].astype(float)/10000).round(2)
    # Transform crs
    data = data.to_crs(epsg=FROM_CRS)
    # Time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Reshape
    data = convert_geometry_to_wkbgeometry(data, from_crs=FROM_CRS)
    gdata = data.drop(columns=["geometry"])
    ready_data = gdata.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )
