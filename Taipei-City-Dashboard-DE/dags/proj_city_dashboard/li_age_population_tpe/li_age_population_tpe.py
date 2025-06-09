from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
from utils.transform_time import convert_roc_date
from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from sqlalchemy import create_engine
import pandas as pd


def _transfer(**kwargs):
    '''
    Monthly population by age in each li of Taipei City (only gender = total, age 0–99).
    '''

    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')

    # Manual Config
    rid = 'c8f5b53d-ef3d-4321-ae8e-58cd2a5ee73c'
    page_id = 'a6394e3f-3514-4542-87bd-de4310a40db3'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Filter only gender = '計' (total)
    raw_data = raw_data[raw_data['性別'] == '計'].copy()

    # Rename columns
    col_map = {
        '年份': 'year',
        '月份': 'month',
        '區域代碼': 'district_code',
        '區域別': 'district',
        '總計': 'total_population'
    }
    for i in range(100):  # only age 0~99
        col_map[f'{i}歲數量'] = f'age_{i}'

    data = raw_data.rename(columns=col_map)

    # Create period
    data['year'] = data['year'].astype(int) + 1911
    data['month'] = data['month'].astype(int).astype(str).str.zfill(2)
    data['period'] = data['year'].astype(str) + '-' + data['month']
    data['data_time'] = get_tpe_now_time_str()

    # 只保留需要的欄位（關鍵修正）
    data = data[['district_code', 'district', 'total_population', 'period', 'data_time']]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=data, load_behavior=load_behavior,
        default_table=default_table
    )

    # Update last update time
    lasttime_in_data = data['data_time'].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


# Create DAG
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='li_age_population_tpe')
dag.create_dag(etl_func=_transfer)
