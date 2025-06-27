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
    Extract AED location data from Taipei Open Data platform and load into PostgreSQL.
    '''

    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')

    # Resource ID (AED 自動體外心臟去顫器設置地點)
    rid = '438c61ad-24f6-4e54-a1cc-e2cfe0e7051e'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Clean coordinates
    raw_data['lat'] = pd.to_numeric(raw_data['緯度'], errors='coerce')
    raw_data['lng'] = pd.to_numeric(raw_data['經度'], errors='coerce')

    # Derive city & district from address
    raw_data['city'] = raw_data['設置地點地址'].str[:3]
    raw_data['district'] = raw_data['設置地點地址'].str[3:6]

    # Create WKB geometry
    raw_data['wkb_geometry'] = raw_data.apply(
        lambda row: wkb.dumps(Point(row['lng'], row['lat'])) if pd.notnull(row['lng']) and pd.notnull(row['lat']) else None,
        axis=1
    )

    # Final dataframe
    df = pd.DataFrame({
        'place_id': pd.to_numeric(raw_data['場所代碼'], errors='coerce'),
        'place_name': raw_data['場所名稱'],
        'city': raw_data['city'],
        'district': raw_data['district'],
        'address': raw_data['設置地點地址'],
        'category': raw_data['場所類別'],
        'type': raw_data['場所型態'],
        'description': raw_data['場所描述'],
        'aed_id': pd.to_numeric(raw_data['AED編號'], errors='coerce'),
        'aed_location': raw_data['AED放置地點'],
        'aed_description': raw_data['AED描述'],
        'lat': raw_data['lat'],
        'lng': raw_data['lng'],
        'wkb_geometry': raw_data['wkb_geometry'],
        'weekday_open': pd.to_datetime(raw_data['平日啟用開始時間'], errors='coerce').dt.time,
        'weekday_close': pd.to_datetime(raw_data['平日啟用結束時間'], errors='coerce').dt.time,
        'saturday_open': pd.to_datetime(raw_data['星期六啟用開始時間'], errors='coerce').dt.time,
        'saturday_close': pd.to_datetime(raw_data['星期六啟用結束時間'], errors='coerce').dt.time,
        'sunday_open': pd.to_datetime(raw_data['星期日啟用開始時間'], errors='coerce').dt.time,
        'sunday_close': pd.to_datetime(raw_data['星期日啟用結束時間'], errors='coerce').dt.time,
        'open_note': raw_data['啟用備註'],
        'emergency_phone': raw_data['緊急聯絡電話'],
        'data_time': raw_data['data_time']
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
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='aed_locations')
dag.create_dag(etl_func=_transfer)
