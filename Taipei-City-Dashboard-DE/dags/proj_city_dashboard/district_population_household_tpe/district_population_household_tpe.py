from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
import pandas as pd
from utils.transform_time import convert_roc_date
from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from sqlalchemy import create_engine
from utils.get_time import get_tpe_now_time_str


def _transfer(**kwargs):
    '''
    Monthly population and household count by district in Taipei City.

    Explanation:
    -------------
    `年份` + `月份` => period
    `行政區` as district
    `戶數` as household_count
    `人口數_合計數量` as total_population
    `人口數_男數量` as male_population
    `人口數_女數量` as female_population
    '''

    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')

    # Manual
    rid = '6a1dbb4e-e99c-4e67-ab09-f6d83852dc99'
    page_id = '6a1dbb4e-e99c-4e67-ab09-f6d83852dc99'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Transform
    col_map = {
        '年份': 'year',
        '月份': 'month',
        '行政區': 'district',
        '戶數': 'household_count',
        '人口數_合計數量': 'total_population',
        '人口數_男數量': 'male_population',
        '人口數_女數量': 'female_population'
    }
    data = raw_data.rename(columns=col_map)

    # 合併年與月為 period，轉西元年
    data['year'] = data['year'].astype(int) + 1911
    data['month'] = data['month'].astype(int).astype(str).str.zfill(2)
    data['period'] = data['year'].astype(str) + '-' + data['month']

    # 清除欄位
    data = data.drop(columns=['_id', '_importdate', 'year', 'month'], errors='ignore')

    ready_data = data.copy()

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table
    )

    lasttime_in_data = ready_data['data_time'].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='district_population_household_tpe')
dag.create_dag(etl_func=_transfer)
