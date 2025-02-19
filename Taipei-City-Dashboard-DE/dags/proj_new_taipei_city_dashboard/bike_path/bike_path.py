from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
    The basic information of electric buses comes from TDX.
    
    data example
    {
        "RouteName": "中正國中體育場",
        "AuthorityName": "NULL",
        "CityCode": "NWT",
        "City": "新北市",
        "Town": "土城區",
        "RoadSectionStart": "廣福街68巷",
        "RoadSectionEnd": "金城路二段",
        "Direction": "雙向",
        "CyclingType": "NULL",
        "CyclingLength": 1100,
        "FinishedTime": "960409",
        "UpdateTime": "2025-02-18T00:00:49+08:00",
        "Geometry": "MULTILINESTRING ((121.459078004121 24.9904630035153,121.45913999526))"
    }
    '''
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_geodataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    import geopandas as gpd


    
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiLineString"
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
    NEW_TAIPEI_URL= "https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/NewTaipei?%24&%24format=JSON"

    raw_data = get_tdx_data(NEW_TAIPEI_URL, output_format='dataframe')
    # Extract
    print(f"raw data =========== {raw_data.head()}")


    # Transform
    # Rename
    data = raw_data

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
    print(f"ready_data =========== {ready_data.head()}")

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

dag = CommonDag(proj_folder='proj_new_taipei_city_dashboard', dag_folder='bike_path')
dag.create_dag(etl_func=_transfer)
