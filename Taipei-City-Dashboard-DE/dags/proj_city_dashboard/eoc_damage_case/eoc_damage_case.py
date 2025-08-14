import re
from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
        The basic information of disaster report alerts comes from the Disaster Management System.

        data example
        {
            "Disasterid": "d9ea6131-9f91-4100-8607-717095df89e7",
            "DPName": "尼伯特颱風",
            "DPIssueDateTime": "2016-07-06T21:00:00",
            "ReportSeq": 14,
            "ReportSendTime": "2016-07-08T20:58:19",
            "SuspendedWaterSupplyCount": 0,
            "SuspendedElectricitySupplyCount": 403,
            "SuspendedTelSupplyCount": 0,
            "SuspendedGasSupplyCount": 0,
            "District": "士林區",
            "UnWithoutWater": 0,
            "UnPowerOutage": 0,
            "UnTelTempDiscon": 0,
            "UnGas": 22
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
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    history_table = dag_infos.get('ready_data_history_table')
    URL = '''https://www.eocmap.gov.taipei/DisasterOperationSystemWebAPIUnite/api/DoItTaipeiApi/GetDamageCaseData'''
    raw_data = requests.get(URL, proxies=proxies)
    raw_data_json = raw_data.json()
    df = pd.DataFrame(raw_data_json)
    if df.empty:
        return "!!!data is empty!!!"
    data = df.copy()
    # Extract


    data = data.rename(columns={
        "Disasterid": "disaster_id",
        "DPIssueDateTime": "dp_issue_date_time",
        "DPName": "dp_name",
        "ReportSeq": "report_seq",
        "ReportSendTime": "report_send_time",
        "SuspendedWaterSupplyCount": "suspended_water_supply_count",
        "SuspendedElectricitySupplyCount": "suspended_electricity_supply_count",
        "SuspendedTelSupplyCount": "suspended_tel_supply_count",
        "SuspendedGasSupplyCount": "suspended_gas_supply_count",
        "District": "district",
        "UnWithoutWater": "un_without_water",
        "UnPowerOutage": "un_power_outage",
        "UnTelTempDiscon": "un_tel_temp_discon",
        "UnGas": "un_gas"
    })
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
