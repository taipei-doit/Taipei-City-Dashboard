from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import requests
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    GEOMETRY_TYPE = 'Point'
    FROM_CRS = 4326

    URL = 'https://od.cdc.gov.tw/eic/Dengue_Daily.json'

    res = requests.get(URL, proxies=proxies, timeout=300)
    res.encoding = 'utf-8-sig'
    raw_data = res.json()
    df = pd.DataFrame(raw_data)

    df = df.rename(columns={
        '發病日': 'onset_date',
        '個案研判日': 'diagnosis_date',
        '通報日': 'report_date',
        '性別': 'gender',
        '年齡層': 'age_group',
        '居住縣市': 'residence_city',
        '居住鄉鎮': 'residence_district',
        '居住村里': 'residence_village',
        '最小統計區中心點X': 'lng',
        '最小統計區中心點Y': 'lat',
        '是否境外移入': 'is_imported',
        '感染國家': 'infection_country',
        '確定病例數': 'confirmed_cases',
        '血清型': 'serotype',
    })

    df = df[df['residence_city'].str.contains('台北|臺北', na=False)]

    df = df[
        (df['lng'].notna()) & (df['lng'] != '') &
        (df['lat'].notna()) & (df['lat'] != '')
    ]

    if df.empty:
        engine = create_engine(ready_data_db_uri)
        update_lasttime_in_data_to_dataset_info(
            engine, airflow_dag_id=dag_id, lasttime_in_data=get_tpe_now_time_str()
        )
        return

    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['confirmed_cases'] = pd.to_numeric(df['confirmed_cases'], errors='coerce').fillna(1).astype(int)

    df = df.dropna(subset=['lng', 'lat'])

    gdf = add_point_wkbgeometry_column_to_df(df, df['lng'], df['lat'], from_crs=FROM_CRS)

    gdf['data_time'] = get_tpe_now_time_str()

    final_df = gdf[[
        'onset_date',
        'diagnosis_date',
        'report_date',
        'gender',
        'age_group',
        'residence_city',
        'residence_district',
        'residence_village',
        'is_imported',
        'infection_country',
        'confirmed_cases',
        'serotype',
        'lng',
        'lat',
        'wkb_geometry',
        'data_time',
    ]]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=final_df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    lasttime_in_data = final_df['data_time'].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='dengue_confirmed_cases')
dag.create_dag(etl_func=_transfer)
