from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from sqlalchemy import create_engine
import pandas as pd


def _transfer(**kwargs):
    '''
    Monthly population by 10-year age group in each li of Taipei City (all genders, includes 100+, with district_area).
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

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Rename columns
    col_map = {
        '年份': 'year',
        '月份': 'month',
        '區域代碼': 'district_code',
        '區域別': 'district',
        '性別': 'gender',
        '總計': 'total_population',
        '100歲以上': 'age_100_plus'
    }
    for i in range(100):
        col_map[f'{i}歲數量'] = f'age_{i}'
    raw_data = raw_data.rename(columns=col_map)

    # Create data_period for original year-month
    raw_data['year'] = raw_data['year'].astype(int) + 1911
    raw_data['month'] = raw_data['month'].astype(int).astype(str).str.zfill(2)
    raw_data['data_period'] = raw_data['year'].astype(str) + '-' + raw_data['month']
    raw_data['data_time'] = get_tpe_now_time_str()

    # 建立區碼對應行政區名稱（只取 district_code 長度為8者）
    area_map = raw_data[raw_data['district_code'].str.len() == 8][['district_code', 'district']]
    area_map = area_map.drop_duplicates().set_index('district_code')['district'].to_dict()

    # 新增行政區欄位（用前8碼對應）
    raw_data['district_area'] = raw_data['district_code'].str[:8].map(area_map)

    # 合併年齡級距
    age_group_labels = []
    for i in range(0, 100, 10):
        group_label = f'age_{i}_{i+9}'
        age_group_labels.append(group_label)
        cols = [f'age_{j}' for j in range(i, i + 10)]
        raw_data[cols] = raw_data[cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        raw_data[group_label] = raw_data[cols].sum(axis=1)

    raw_data['age_100_plus'] = pd.to_numeric(raw_data['age_100_plus'], errors='coerce').fillna(0)
    age_group_labels.append('age_100_plus')

    # 轉為長格式
    melt_df = raw_data.melt(
        id_vars=[
            'district_code', 'district_area', 'district', 'gender',
            'total_population', 'data_period', 'data_time'
        ],
        value_vars=age_group_labels,
        var_name='period',
        value_name='population'
    )

    melt_df = melt_df[[  # 調整欄位順序
        'district_code', 'district_area', 'district', 'gender',
        'total_population', 'data_period', 'period', 'data_time', 'population'
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=melt_df, load_behavior=load_behavior,
        default_table=default_table
    )

    # Update last update time
    lasttime_in_data = melt_df['data_time'].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )



# Create DAG
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='li_age_population_tpe')
dag.create_dag(etl_func=_transfer)
