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

    # 只保留必要欄位
    data = data.drop(columns=[
        '_id', '_importdate', '性別', 'year', 'month',
        '0歲數量', '1歲數量', '2歲數量', '3歲數量', '4歲數量',
        '5歲數量', '6歲數量', '7歲數量', '8歲數量', '9歲數量',
        '10歲數量', '11歲數量', '12歲數量', '13歲數量', '14歲數量',
        '15歲數量', '16歲數量', '17歲數量', '18歲數量', '19歲數量',
        '20歲數量', '21歲數量', '22歲數量', '23歲數量', '24歲數量',
        '25歲數量', '26歲數量', '27歲數量', '28歲數量', '29歲數量',
        '30歲數量', '31歲數量', '32歲數量', '33歲數量', '34歲數量',
        '35歲數量', '36歲數量', '37歲數量', '38歲數量', '39歲數量',
        '40歲數量', '41歲數量', '42歲數量', '43歲數量', '44歲數量',
        '45歲數量', '46歲數量', '47歲數量', '48歲數量', '49歲數量',
        '50歲數量', '51歲數量', '52歲數量', '53歲數量', '54歲數量',
        '55歲數量', '56歲數量', '57歲數量', '58歲數量', '59歲數量',
        '60歲數量', '61歲數量', '62歲數量', '63歲數量', '64歲數量',
        '65歲數量', '66歲數量', '67歲數量', '68歲數量', '69歲數量',
        '70歲數量', '71歲數量', '72歲數量', '73歲數量', '74歲數量',
        '75歲數量', '76歲數量', '77歲數量', '78歲數量', '79歲數量',
        '80歲數量', '81歲數量', '82歲數量', '83歲數量', '84歲數量',
        '85歲數量', '86歲數量', '87歲數量', '88歲數量', '89歲數量',
        '90歲數量', '91歲數量', '92歲數量', '93歲數量', '94歲數量',
        '95歲數量', '96歲數量', '97歲數量', '98歲數量', '99歲數量',
        '100歲以上'
    ], errors='ignore')


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
