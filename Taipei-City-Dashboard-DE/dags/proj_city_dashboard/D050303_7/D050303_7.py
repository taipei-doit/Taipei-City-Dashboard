from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import MultiPolygon
from shapely import wkb

def safe_load_wkb(wkb_str):
    '''
    Note: In order to avoid missing value from original wkb geometry, we need to write a simple
    function to load wkb geometry with missing value.
    '''
    try:
        if pd.notnull(wkb_str) and len(wkb_str) > 0:
            return wkb.loads(wkb_str)
        else:
            return None
    except Exception as e:
        print(f"Error loading WKB: {e}")
        return None

def _extract_db_info(default_table, engine):
    # read existing data
    existing_data = pd.read_sql(f"SELECT 編號, wkb_geometry FROM {default_table}", engine)
    # Use function to transform 'wkb_geometry'
    existing_data['wkb_geometry'] = existing_data['wkb_geometry'].apply(safe_load_wkb)
    existing_data = gpd.GeoDataFrame(existing_data, geometry='wkb_geometry', crs='epsg:4326')
    return existing_data

def _replace_geometry(data, **kwargs):
    '''
    Note: This function aims to replace broken geometry from original geojson. Some boundries of 
    parks like Da-An and Ching-Nian seems weird so we replaced them.
    '''
    engine = create_engine(kwargs.get('raw_data_db_uri'))
    landuse = _extract_db_info('building_landuse', engine)
    # Filter the park need to replace
    replace_list = ['大安森林公園', '青年公園']
    replace_data = data[data['name'].isin(replace_list)]

    # Compare to urban plan
    landuse = landuse.set_crs(epsg=4326)
    landuse = landuse.to_crs(epsg=3826)
    temp = gpd.sjoin(replace_data, landuse, how='inner', op='intersects')
    index = temp['編號'].values.tolist()

    # Replace each geometry
    for idx in index:
        # Find target geometry
        target_poly = landuse[landuse['編號']==idx]['wkb_geometry'].values[0]
        # 將MultiPolygon賦值給新的GeoDataFrame中的geometry欄位
        temp.loc[temp['編號'] == idx, 'geometry'] = target_poly
    # Drop columns
    drop_col = ['index_right', '編號']
    temp.drop(columns=drop_col, inplace=True)

    # Replace original geometry
    for idx, row in temp.iterrows():
        if row['name'] in replace_list:
            data.loc[data['name'] == row['name'], 'geometry'] = row['geometry']
        else:
            print('No need to replace')
    return data

def D050303_7(**kwargs):
    from utils.extract_stage import download_file
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

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
    # Config
    file_name = "D050303_7.geojson"
    web_url = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=97d2bea0-eedf-47ec-b286-5229cf99f558"
    page_id = "5b277432-f534-4d09-a24c-d3f6b514e042"
    rank_index = 27
    geometry_type = "MultiPolygon"
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
    # Replace Da-An and  Chin_Nian park
    data = _replace_geometry(data, **kwargs)
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
        data['geometry'] = data['geometry'].buffer(3)
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

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_7")
dag.create_dag(etl_func=D050303_7)
