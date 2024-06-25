from airflow import DAG
from operators.common_pipeline import CommonDag

def childcare_etl(rid, page_id,**kwargs):
    from utils.extract_stage import get_data_taipei_api
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_address import clean_data, main_process, save_data, get_addr_xy_parallel
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get('raw_data_db_uri')
    data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    # Manually set
    # Highly recommend to add `data_time` column to the dataframe for future long term data tracking.
    # If data has no time information and the data source is data.taipei, 
    # you can use the `更新時間` besides `下載` link as data time information.
    # `更新時間` is a dynamic API, can be found in browse Devtools -> Network -> Fetch/XHR -> Name: dataset.view?...
    from_crs = 4326

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data['data_time'] = get_data_taipei_file_last_modified_time(page_id)

    # Transform
    # Rename
    data = raw_data
    data = data.drop(columns=['_id', '_importdate'])
    name_dict = {
    '機構類型': 'type', 
    '機構名稱': 'name', 
    '地址': 'address',
    '電話': 'phone',
    }
    data = data.rename(columns=name_dict)
    # clean addr
    addr = data['address']
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data['address'] = output
    # Extract town from address
    data['town'] = data['address'].str[3:6]
    # Time
    data['data_time'] = convert_str_to_time_format(data['data_time'])
    # Geometry
    data['lng'], data['lat'] = get_addr_xy_parallel(data['address'], sleep_time=0.5)
    gdata = add_point_wkbgeometry_column_to_df(data, x=data['lng'], y=data['lat'], from_crs=from_crs)
    # Reshape
    ready_data = gdata.drop(columns=['lng', 'lat', 'geometry'])

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine, gdata=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
        geometry_type='Point'
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )
