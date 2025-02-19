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
    from utils.transform_geometry import convert_geometry_to_wkbgeometry,convert_linestring_to_multilinestring
    import geopandas as gpd
    from shapely import wkt    
    import pandas as pd
    from geoalchemy2 import WKTElement

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
    TAIPEI_URL= "https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24&%24format=JSON"
    GEOMETRY_TYPE = "MultiLineString"   
    FROM_CRS = 4326
    raw_data = get_tdx_data(TAIPEI_URL, output_format='dataframe')
    # Extract
    def safe_load_wkt(x):
        try:
            return wkt.loads(x)
        except Exception as e:
            print(f"Error parsing WKT: {x}, error: {e}")
            return None

    data["geometry"] = data["Geometry"].apply(lambda x: safe_load_wkt(x) if pd.notnull(x) else None)
    data = data[data["geometry"].notnull()]
    data['geometry'] = data['geometry'].apply(lambda geom: geom.wkt if geom is not None else None)
    # 如果需要建立 GeoDataFrame，要先轉換回 geometry 物件
    data['geometry'] = gpd.GeoSeries.from_wkt(data['geometry'])
    # data["geometry"] = data["Geometry"].apply(wkt.loads)
    gdata = gpd.GeoDataFrame(data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")
    gdata["wkb_geometry"] = gdata["geometry"].apply(
        lambda x: WKTElement(x.wkt, srid=FROM_CRS) if x is not None else None
    )
    # gdata["geometry"] = gdata["geometry"].apply(convert_linestring_to_multilinestring)
    print(f"gdata =========== {gdata.columns}")
    gdata['data_time'] = gdata['UpdateTime']
    # Reshape
    gdata = gdata.rename(columns={
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
        })
    
    gdata = gdata.drop(columns=["Geometry"])
    ready_data = gdata.copy()
    print(f"ready_data =========== {ready_data.columns}")
    # Load

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
