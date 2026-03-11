import re
from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
        The basic information of disaster report alerts comes from the Disaster Management System.

        data example
        {
            "DPID": "70819f56-6c23-4153-ac41-a206481c47ed",
            "DPName": "1141102_毒氣瓦斯外洩",
            "IssueTime": "2025-12-03T15:18:00",
            "ReportSeq": 131,
            "WaterOutage": 0,
            "PowerOutage": 0,
            "TelSuspended": 0,
            "Gas": 0,
            "District": "士林區",
            "UnWaterOutage": 0,
            "UnPowerOutage": 0,
            "UnTelSuspended": 0,
            "UnGas": 0
        }
    '''
    from utils.load_stage import save_dataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    import pandas as pd
    import requests
    from utils.get_time import get_tpe_now_time_str
    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    # raw_data_db_uri = kwargs.get('raw_data_db_uri')
    # data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    # proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    URL = '''https://tfd.blob.core.windows.net/blobfs/data/TEST-T-SAGEDamageCaseData.json'''

    raw_data = requests.get(URL)
    raw_data_json = raw_data.json()
    # 處理 API 回傳空資料或無資料狀態
    if not raw_data_json:
        print("!!!data is empty!!!")
        return "!!!data is empty!!!"
    # API 回傳 {"open":"現在無資料"} 表示目前沒有災情資料
    if isinstance(raw_data_json, dict) and "open" in raw_data_json:
        print(f"!!!API 回傳: {raw_data_json}!!!")
        return "!!!data is empty!!!"
    if isinstance(raw_data_json, dict):
        raw_data_json = [raw_data_json]
    df = pd.DataFrame(raw_data_json)
    if df.empty:
        return "!!!data is empty!!!"
    data = df.copy()
    # Extract


    data = data.rename(columns={
        "DPID": "disaster_id",
        "IssueTime": "dp_issue_date_time",
        "DPName": "dp_name",
        "ReportSeq": "report_seq",
        "WaterOutage": "suspended_water_supply_count",
        "PowerOutage": "suspended_electricity_supply_count",
        "TelSuspended": "suspended_tel_supply_count",
        "Gas": "suspended_gas_supply_count",
        "District": "district",
        "UnWaterOutage": "un_without_water",
        "UnPowerOutage": "un_power_outage",
        "UnTelSuspended": "un_tel_temp_discon",
        "UnGas": "un_gas"
    })
    
    # 新 API 沒有 ReportSendTime 欄位，給定預設值空字串或 None
    if "report_send_time" not in data.columns:
        data["report_send_time"] = None

    data['data_time'] = get_tpe_now_time_str()
    data = data[data["disaster_id"] != "f804b5b3-3526-4692-87d1-6e6dc785966f"]
    ready_data = data.copy()
    print(f"ready_data =========== {ready_data.columns}")
    # Load

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='eoc_damage_case')
dag.create_dag(etl_func=_transfer)
