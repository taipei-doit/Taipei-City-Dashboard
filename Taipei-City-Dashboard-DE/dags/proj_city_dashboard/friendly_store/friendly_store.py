from shapely.geometry import Point
from shapely import wkb
from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from sqlalchemy import create_engine
import pandas as pd


def _transfer(**kwargs):
    '''
    Extract friendly store data, convert to WKB geometry point, and load into PostgreSQL.
    '''

    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')

    # Resource ID
    rid = '5a5b36e0-f870-4b7f-8378-c91ac5f57941'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Filter: Taipei and New Taipei only
    raw_data = raw_data[raw_data['地址'].str.startswith(('臺北市', '新北市'))].copy()

    # Derive city and zone
    raw_data['city'] = raw_data['地址'].str[:3]
    raw_data['zone'] = raw_data['地址'].str[3:6]

    # Clean and convert coordinates
    raw_data['lon'] = pd.to_numeric(raw_data['經度'], errors='coerce')
    raw_data['lat'] = pd.to_numeric(raw_data['緯度'], errors='coerce')

    # Convert all count columns to numeric
    def safe_int(col):
        return pd.to_numeric(raw_data[col], errors='coerce').fillna(0)

    # Build WKB geometry
    raw_data['wkb_geometry'] = raw_data.apply(
        lambda row: wkb.dumps(Point(row['lon'], row['lat'])) if pd.notnull(row['lon']) and pd.notnull(row['lat']) else None,
        axis=1
    )

    # Final DataFrame
    df = pd.DataFrame({
        'store_name': raw_data['友善店家名稱'],
        'address': raw_data['地址'],
        'city': raw_data['city'],
        'zone': raw_data['zone'],
        'd_address': raw_data['友善店家網站個別店家介紹網址'],
        'lon': raw_data['lon'],
        'lat': raw_data['lat'],
        'call_num': raw_data['電話'],
        'store_summary': raw_data['簡介'],
        'wkb_geometry': raw_data['wkb_geometry'],

        'f_lang': (safe_int('英文友善（count）') + safe_int('日文友善（count）') + safe_int('韓文友善（count）')) > 0,
        'f_moblie': safe_int('行動裝置充電（count）') > 0,
        'f_acc': safe_int('無障礙友善（count）') > 0,
        'f_sex': safe_int('性別友善（count）') > 0,
        'f_pay': safe_int('便利支付（count）') > 0,
        'f_veg': safe_int('素食友善（count）') > 0,
        'f_toilet': safe_int('友善廁所（count）') > 0,
        'f_wifi': safe_int('free wifi（count）') > 0,
        'f_bike': safe_int('自行車友善（count）') > 0,
        'f_lactation': safe_int('親子友善（count）') > 0,
        'f_muslim': safe_int('穆斯林友善（count）') > 0,
        'f_mc': safe_int('月經友善（count）') > 0,
        'f_sum': safe_int('友善項目總計').astype(int)
    })

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=df, load_behavior=load_behavior,
        default_table=default_table
    )

    # Update last update time
    lasttime_in_data = raw_data['data_time'].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


# Create DAG
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='friendly_store')
dag.create_dag(etl_func=_transfer)
