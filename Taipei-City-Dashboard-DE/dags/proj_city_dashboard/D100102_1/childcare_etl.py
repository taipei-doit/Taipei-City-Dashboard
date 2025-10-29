from airflow import DAG
from operators.common_pipeline import CommonDag

def childcare_etl(rid, page_id, **kwargs):
    from utils.extract_stage import get_data_taipei_api, get_data_taipei_file_last_modified_time
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_address import clean_data, main_process, save_data, get_addr_xy_parallel
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    import pandas as pd

    # ===== Config =====
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    dag_infos = kwargs.get('dag_infos', {})
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    from_crs = 4326

    # ===== Extract =====
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data['data_time'] = get_data_taipei_file_last_modified_time(page_id)

    # ===== Transform =====
    # 只取需要的欄位
    name_dict = {
        '機構類型': 'type',
        '機構名稱': 'name',
        '地址': 'address',
        '電話': 'phone',
    }

    # rename 並只保留有對應的欄位
    data = raw_data.rename(columns=name_dict)
    data = data[list(name_dict.values()) + ['data_time']]
    data = data.dropna(subset=['address'])  # 移除無地址資料

    # 地址清理與標準化
    addr = data['address']
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    _, output = save_data(addr, addr_cleaned, standard_addr_list)
    data['address'] = output

    # 行政區萃取（臺北市開頭固定前三字）
    data['town'] = data['address'].str[3:6]

    # 時間轉換
    data['data_time'] = convert_str_to_time_format(data['data_time'])

    # 經緯度 + 幾何
    data['lng'], data['lat'] = get_addr_xy_parallel(data['address'], sleep_time=0.5)
    gdata = add_point_wkbgeometry_column_to_df(data, x=data['lng'], y=data['lat'], from_crs=from_crs)

    # 最終只保留指定欄位
    ready_data = gdata[['type', 'name', 'address', 'phone', 'data_time', 'town', 'wkb_geometry']]

    # ===== Load =====
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type='Point'
    )

    # 更新 dataset_info 的 lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data)

