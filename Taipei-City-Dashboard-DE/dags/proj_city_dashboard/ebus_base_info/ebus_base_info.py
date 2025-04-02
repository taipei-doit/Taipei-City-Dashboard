from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
    The basic information of electric buses comes from TDX.
    
    data example
    {
        "PlateNumb": "001-U3",
        "OperatorID": "800",
        "OperatorCode": "MetropolitanBus",
        "OperatorNo": "0303",
        "VehicleClass": 1,
        "VehicleType": 1,
        "CardReaderLayout": 2,
        "IsElectric": 0,
        "IsHybrid": 0,
        "IsLowFloor": 1,
        "HasLiftOrRamp": 1,
        "HasWifi": 0,
        "InBoxID": "104017906",
        "UpdateTime": "2025-02-18T22:11:04+08:00"
        }
    '''
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_dataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine

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
    TAIPEI_URL= "https://tdx.transportdata.tw/api/basic/v2/Bus/Vehicle/City/Taipei?%24&%24format=JSON"

    raw_data = get_tdx_data(TAIPEI_URL, output_format='dataframe')
    # Extract
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data

    data['data_time'] = data['UpdateTime']
    # Reshape
    data = data.rename(columns={
        "PlateNumb": "plate_numb",
        "OperatorID": "operator_id",
        "OperatorCode": "operator_code",
        "OperatorNo": "operator_no",
        "VehicleClass": "vehicle_class",
        "VehicleType": "vehicle_type",
        "CardReaderLayout": "card_reader_layout",
        "IsElectric": "is_electric",
        "IsHybrid": "is_hybrid",
        "IsLowFloor": "is_low_floor",
        "HasLiftOrRamp": "has_lift_or_ramp",
        "HasWifi": "has_wifi",
        "InBoxID": "inbox_id"	
        })
    data = data.drop(columns=["UpdateTime"])

    ready_data = data.copy()

    # Load
    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='ebus_base_info')
dag.create_dag(etl_func=_transfer)
