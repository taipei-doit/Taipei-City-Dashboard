from airflow import DAG
from operators.common_pipeline import CommonDag
from sqlalchemy import create_engine
import pandas as pd

def _extract_db_info(default_table, engine):
    # read existing data
    existing_data = pd.read_sql(f"SELECT * FROM {default_table}", engine)

    # Filter columns
    keep_col = ['name', 'addr', 'lat', 'lng']
    existing_data = existing_data[keep_col]
    return existing_data

def _concat_hospital_clinic_info(clinic_table, hospital_table, **kwargs):
    # Config
    raw_data_db_uri = kwargs.get('raw_data_db_uri')

    # Get existing hospital and clinic data
    engine = create_engine(raw_data_db_uri)
    clinic_data = _extract_db_info('heal_clinic', engine)
    hospital_data = _extract_db_info('heal_hospital', engine)

    # Concat
    existing_data = pd.concat([clinic_data, hospital_data], axis=0)
    return existing_data


def D100104_1(**kwargs):
    '''
    Information and locations of maternity hospitals service from data.taipei.

    Explanation:
    -------------
    pre_marriage_check: There are 3 columns in the raw data, which are `婚後孕前健康檢查生理男性`, 
        `婚後孕前健康檢查生理女性`, `婚後孕前健康檢查生理女性加選項目抗穆勒氏管`. Since the female column 
        has covered the most information, we will only keep the column as representative. 

    unmatched_list: There are 10 hospitals in the raw data that cannot be found in the existing 
        hospital and clinic list, therefore the list was created to record the situation.
    '''
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_file_last_modified_time, get_data_taipei_api
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
    clinic_table = 'heal_clinic'
    hospital_table = 'heal_hospital'
    # Manually set
    page_id = '9ee72240-f9b3-42a7-bcbe-e1bb1a28a2dc'
    from_crs = 4326

    # Extract
    rid = get_current_rid_from_page_id(page_id)
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)

    # Transform
    # Filter columns
    data = raw_data.copy()
    # 資料集欄位改版:「婚後孕前健康檢查生理女性」已改為「孕前健康檢查生理女性門診」
    if '婚後孕前健康檢查生理女性' not in data.columns and '孕前健康檢查生理女性門診' in data.columns:
        data = data.rename(columns={'孕前健康檢查生理女性門診': '婚後孕前健康檢查生理女性'})
    keep_col = ['行政區', '醫療機構', '婚後孕前健康檢查生理女性',
                '初期孕婦唐氏症篩檢', '中期孕婦唐氏症篩檢']
    data = data[keep_col]
    data = data.iloc[:-1, :]
    # Rename
    col_map = {
        '行政區': 'district',
        '醫療機構': 'hospital',
        '婚後孕前健康檢查生理女性': 'pre_marriage_check',
        '初期孕婦唐氏症篩檢': 'early_pregnant_screening',
        '中期孕婦唐氏症篩檢': 'mid_pregnant_screening'
    }
    data = data.rename(columns=col_map)
    # 行政區代碼兼容 8 碼舊格式(63000040) 與 7 碼新格式(6300400)
    district_map = {
        # 舊 8 碼
        63000010: '松山區', 63000020: '信義區', 63000030: '大安區',
        63000040: '中山區', 63000050: '中正區', 63000060: '大同區',
        63000070: '萬華區', 63000080: '文山區', 63000090: '南港區',
        63000100: '內湖區', 63000110: '士林區', 63000120: '北投區',
        # 新 7 碼
        6300100: '松山區', 6300200: '信義區', 6300300: '大安區',
        6300400: '中山區', 6300500: '中正區', 6300600: '大同區',
        6300700: '萬華區', 6300800: '文山區', 6300900: '南港區',
        6301000: '內湖區', 6301100: '士林區', 6301200: '北投區',
    }
    data['district'] = data['district'].astype(int)
    data['district'] = data['district'].map(district_map)
    # 值格式也從 'V' 改為 '1';兼容兩者
    _truthy = {'V', '1', 'Y', True, 1}
    data['pre_marriage_check'] = data['pre_marriage_check'].apply(lambda x: x in _truthy)
    data['early_pregnant_screening'] = data['early_pregnant_screening'].apply(lambda x: x in _truthy)
    data['mid_pregnant_screening'] = data['mid_pregnant_screening'].apply(lambda x: x in _truthy)
    # Time
    data['data_time'] = get_data_taipei_file_last_modified_time(page_id)
    data['data_time'] = convert_str_to_time_format(data['data_time'])
    # Geometry from existing data
    replace_dict = {'\n': '', ' ': '', '-': '─', '－': '─', '台':'臺'}
    data['hospital'] = data['hospital'].replace(replace_dict, regex=True)
    existing_data = _concat_hospital_clinic_info(clinic_table, hospital_table, **kwargs)
    existing_data['name'] = existing_data['name'].replace(replace_dict, regex=True)
    data = data.merge(existing_data, how='left', left_on='hospital', right_on='name')
    data = data.rename(columns={'addr': 'address'})
    data = data.drop(columns=['name'])
    unmatch_list = data[data['lng'].isnull()]['hospital'].values.tolist()
    print(f'Unmatched {len(unmatch_list)} hospitals: {unmatch_list}')
    # TUIC use wkb_geometry format to store geometry data, and use `wkb_geometry` as the column name.
    # Ready data always in crs 4326 (WGS84) coordinate system.
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

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='D100104_1')
dag.create_dag(etl_func=D100104_1)
