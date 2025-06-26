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

    # Construct WKB Point geometry
    raw_data['wkb_geometry'] = raw_data.apply(
        lambda row: wkb.dumps(Point(row['lon'], row['lat'])) if pd.notnull(row['lon']) and pd.notnull(row['lat']) else None,
        axis=1
    )

    # Build final DataFrame
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
        'wkb_geometry': raw_data['wkb_geometry'],  # ← geometry 點位欄位

        'f_lang': (raw_data['英文友善（count）'] + raw_data['日文友善（count）'] + raw_data['韓文友善（count）']) > 0,
        'f_moblie': raw_data['行動裝置充電（count）'] > 0,
        'f_acc': raw_data['無障礙友善（count）'] > 0,
        'f_sex': raw_data['性別友善（count）'] > 0,
        'f_pay': raw_data['便利支付（count）'] > 0,
        'f_veg': raw_data['素食友善（count）'] > 0,
        'f_toilet': raw_data['友善廁所（count）'] > 0,
        'f_wifi': raw_data['free wifi（count）'] > 0,
        'f_bike': raw_data['自行車友善（count）'] > 0,
        'f_lactation': raw_data['親子友善（count）'] > 0,
        'f_muslim': raw_data['穆斯林友善（count）'] > 0,
        'f_mc': raw_data['月經友善（count）'] > 0,
        'f_sum': pd.to_numeric(raw_data['友善項目總計'], errors='coerce').fillna(0).astype(int)
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