from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    '''
    data example
    {
        "DPID": "d9ea6131-9f91-4100-8607-717095df89e7",
        "DPName": "尼伯特颱風",
        "CaseID": "02373bed-8ca2-4e63-bcf8-886a6f9edaca",
        "CaseTime": "2016-07-07T16:44:52",
        "PName": "民生、基礎設施災情",
        "CaseLocationDistrict": "松山區",
        "CaseLocationDescription": "南京東路五段250 巷 18 弄1 號",
        "CaseDescription": "路燈上之纜線垂落，請清除以免掉落造成危險。",
        "CaseComplete": true,
        "Wgs84X": 121.566231,
        "Wgs84Y": 25.0503178,
        "CaseSerious":false
    }
    '''
    from utils.load_stage import save_geodataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
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
    URL = '''https://www.eocmap.gov.taipei/DisasterOperationSystemWebAPIUnite/api/DisasterServiceApi/GetDisasterSummary'''
    GEOMETRY_TYPE = "Point"   
    FROM_CRS = 4326
    raw_data = requests.get(URL, proxies=proxies)
    raw_data_json = raw_data.json()
    df = pd.DataFrame(raw_data_json)
    if df.empty:
        return "!!!data is empty!!!"
    data = df.copy()
    # Extract

    data = data.rename(columns={
        "DPID": "dpid",
        "DPName": "dpname",
        "CaseID": "caseid",
        "CaseTime": "case_time",
        "PName": "pname",
        "CaseLocationDistrict": "case_location_district",
        "CaseLocationDescription": "case_location_description",
        "CaseDescription": "case_description",
        "CaseComplete": "case_complete",
        "Wgs84X": "lng",
        "Wgs84Y": "lat",
        "CaseSerious":"case_serious"
        })
    # 將 case_complete 欄位的 True/False 轉換為中文
    data["case_complete"] = data["case_complete"].map({True: "處理完成", False: "未處理完成"})
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # sele
    gdata['data_time'] = get_tpe_now_time_str()
    # Reshape
    ready_data = gdata.drop(columns=["geometry"])
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
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='eoc_disaster_summary')
dag.create_dag(etl_func=_transfer)
