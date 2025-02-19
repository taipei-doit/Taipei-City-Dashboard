from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
    The basic information of electric buses comes from TDX.
    
    data example
    {
        "RouteName": "三元街(東北側2)",
        "AuthorityName": "NULL",
        "CityCode": "TPE",
        "City": "台北市",
        "Town": "",
        "RoadSectionStart": "和平西路二段104巷",
        "RoadSectionEnd": "和平西路二段98巷",
        "Direction": "雙向",
        "CyclingType": "NULL",
        "CyclingLength": 267,
        "FinishedTime": "1021231",
        "UpdateTime": "2025-02-18T00:01:52+08:00",
        "Geometry": "MULTILINESTRING ((121.507845000865 25.0305410051544,121.50819900141 25.0303169993081,121.508853000944 25.0297239978913,121.509352001504 25.0292229977471,121.509862004641 25.0287910052392))"
    }
    '''
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_geodataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format
    import geopandas as gpd
    from shapely.wkt import loads
    import pandas as pd
    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    # raw_data_db_uri = kwargs.get('raw_data_db_uri')
    # data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    history_table = dag_infos.get('ready_data_history_table')
    NEW_TAIPEI_URL= "https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24&%24format=JSON"
    GEOMETRY_TYPE = "MultiLineString"   
    FROM_CRS = 4326
    raw_data = get_tdx_data(NEW_TAIPEI_URL, output_format='dataframe')
    # Extract
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data
    data["Geometry"] = data["Geometry"].apply(lambda x: loads(x) if pd.notnull(x) else None)

    gdata = gpd.GeoDataFrame(data, geometry="Geometry", crs=f"EPSG:{FROM_CRS}")
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)

    
    gdata['data_time'] = gdata['UpdateTime']
    # Reshape
    gdata.rename(columns={
        "RouteName": "route_name",
        "AuthorityName": "authority_name",
        "CityCode": "city_code",
        "City": "city",
        "Town": "town",
        "RoadSectionStart": "road_section_start",
        "RoadSectionEnd": "road_section_end",
        "Direction": "direction",
        "CyclingType": "cycling_type",
        "CyclingLength": "cycling_length",
        "FinishedTime": "finished_time",
        "UpdateTime": "update_time",
        }, inplace=True)
    ready_data = gdata.copy()

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        GEOMETRY_TYPE=GEOMETRY_TYPE,
    )
    
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='bike_path')
dag.create_dag(etl_func=_transfer)
