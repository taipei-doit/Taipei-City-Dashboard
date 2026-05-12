import pandas as pd
from airflow import DAG
from sqlalchemy import create_engine
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from utils.transform_geometry import add_point_wkbgeometry_column_to_df


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    GEOMETRY_TYPE = 'Point'
    FROM_CRS = 4326

    page_id = "8b2fcdeb-d14b-46c4-92d8-66ad07b96a91"
    rid = get_current_rid_from_page_id(page_id)
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)

    raw_data = raw_data.rename(columns={
        '行政區': 'district',
        '地點': 'place_name',
        '地址': 'address',
        '樣態': 'category',
        '開放時間': 'open_time',
        '緯度': 'latitude',
        '經度': 'longitude',
        '相對位置': 'relative_location',
        '照片連結': 'image_url',
        '管理單位': 'management_unit',
        '管理單位電話': 'management_phone',
        '備註': 'remark',
    })

    raw_data['latitude'] = pd.to_numeric(raw_data['latitude'], errors='coerce')
    raw_data['longitude'] = pd.to_numeric(raw_data['longitude'], errors='coerce')

    gdata = add_point_wkbgeometry_column_to_df(
        raw_data,
        raw_data['longitude'],
        raw_data['latitude'],
        from_crs=FROM_CRS,
    )

    # 對齊 DB schema 長度限制,避免 StringDataRightTruncation
    str_limits = {
        'district': 50,
        'place_name': 50,
        'address': 50,
        'category': 50,
        'open_time': 64,
        'relative_location': 50,
        'image_url': 128,
        'management_unit': 50,
        'management_phone': 50,
        'remark': 50,
    }
    for col, limit in str_limits.items():
        gdata[col] = gdata[col].astype(str).str.slice(0, limit)

    ready_data = gdata[[
        'district', 'place_name', 'address', 'category', 'open_time',
        'latitude', 'longitude', 'relative_location', 'image_url',
        'management_unit', 'management_phone', 'remark', 'wkb_geometry',
    ]]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(),
    )


dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='smoking_area')
dag.create_dag(etl_func=_transfer)
