from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
    The basic information of electric buses comes from TDX.
    
    data example
    {
        "PlateNumb": "EAA-135",
        "OperatorID": "16176",
        "OperatorCode": "TaipeiBus",
        "OperatorNo": "1407",
        "VehicleClass": 1,
        "VehicleType": 1,
        "CardReaderLayout": 2,
        "IsElectric": 1,
        "IsHybrid": 0,
        "IsLowFloor": 1,
        "HasLiftOrRamp": 1,
        "HasWifi": 1,
        "InBoxID": "104034180",
        "UpdateTime": "2025-02-17T13:13:47+08:00"
    }
    '''
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    from utils.transform_time import convert_str_to_time_format

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
    NEW_TAIPEI_URL= '''https://tdx.transportdata.tw/api/basic/v2/Bus/Vehicle/City/NewTaipei?%24&%24format=JSON'''

    raw_data = get_tdx_data(NEW_TAIPEI_URL, output_format='dataframe')
    print(f"raw data =========== {raw_data.head()}")

    # Extract
    

    # Transform
    # Rename
    data = raw_data

    data["data_time"] = convert_str_to_time_format(data["UpdateTime"])


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
    # Reshape
    ready_data = data.copy()
    print(f"ready_data =========== {ready_data.head()}")

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

dag = CommonDag(proj_folder='proj_new_taipei_city_dashboard', dag_folder='ebus_base_info')
dag.create_dag(etl_func=_transfer)
