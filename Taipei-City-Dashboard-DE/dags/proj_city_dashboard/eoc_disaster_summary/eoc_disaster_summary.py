from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    '''
    data example
    {
        "DPID": "290e30bb-d2b1-448d-8a51-0099a738734a",
        "DPName": "1140414_陽明山小油坑森林火災",
        "CaseID": "171a1cdf-8c54-414b-8bd3-7e4f499b1795",
        "CaseTime": "2025-12-24T10:23:00",
        "DisasterName": "其他(前述以外火災)",
        "Address": "忠孝東路三段3號",
        "CaseDesc": "test 1224測試",
        "ProcStatus": false,
        "WGS84X": 121.533379,
        "WGS84Y": 25.042028,
        "IsSerious": false
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
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    URL = '''https://tfd.blob.core.windows.net/blobfs/data/TEST-T-TSAGEDisasterSummary.json'''
    GEOMETRY_TYPE = "Point"   
    FROM_CRS = 4326
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
    if df.empty or "CaseID" not in df.columns:
        return "!!!data is empty!!!"
    data = df.copy()
    # Extract

    data = data.rename(columns={
        "DPID": "dpid",
        "DPName": "dpname",
        "CaseID": "caseid",
        "CaseTime": "case_time",
        "DisasterName": "pname",
        "District": "case_location_district",
        "Address": "case_location_description",
        "CaseDesc": "case_description",
        "ProcStatus": "case_complete",
        "WGS84X": "lng",
        "WGS84Y": "lat",
        "IsSerious":"case_serious"
        })
    # 將 case_complete 欄位的 True/False 轉換為中文
    data["case_complete"] = data["case_complete"].map({True: "處理完成", False: "處理中"})
    # 新資料欄位可能沒有行政區 (District) 資訊，給定空字串避免後續操作失敗
    if "case_location_district" not in data.columns:
        data["case_location_district"] = ""
    else:
        # 若有此欄位，將缺失值填為空字串
        data["case_location_district"] = data["case_location_district"].fillna("")
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
