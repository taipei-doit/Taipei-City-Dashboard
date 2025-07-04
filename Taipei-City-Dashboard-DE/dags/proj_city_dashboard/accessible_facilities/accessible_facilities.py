from airflow import DAG
from operators.common_pipeline import CommonDag
import re
import pandas as pd

################################################
# 將無障礙設施內容內容解析為多個欄位
################################################
def parse_content(text):
    value_map = {
    '無障礙停車位': 'disabled_parking_car_count',
    '無障礙機車停車位': 'disabled_parking_motorcycle_count'
    }
    flag_map = {
        '無障礙電梯': 'accessible_elevator_flag',
        '無障礙廁所': 'accessible_restroom_flag',
        '無障礙樓梯扶手': 'accessible_stair_handrail_flag'
    }
    out = {
        'disabled_parking_car_count': 0,
        'disabled_parking_motorcycle_count': 0,
        'accessible_elevator_flag': False,
        'accessible_restroom_flag': False,
        'accessible_stair_handrail_flag': False
    }
    # 處理數值型
    for k, v in value_map.items():
        match = re.search(rf'{k}X(\d+)', text)
        if match:
            out[v] = int(match.group(1))
    # 處理flag型
    for k, v in flag_map.items():
        if k in text:
            out[v] = True
    return pd.Series(out)


def _transfer(**kwargs):
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.extract_stage import get_data_taipei_api
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    
    # 市場無障礙設施
    RID = "b9281f44-8eda-4cc2-bf97-745667ed03cd"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            '場地名稱': "name",
            '地址': "address",
            '無障礙設施內容': "description",
            'gtag_longitude': "lng",
            'gtag_latitude': "lat",
        }
    )
    
    data = pd.concat([data, data['description'].apply(parse_content)], axis=1)
    # 資料格式為"108臺北市萬華區昆明街142號7-8樓", 只取區
    area_candidates = data['address'].str.slice(3, 6)
    data['district'] = area_candidates.apply(lambda x: x if x.endswith('區') else None)
    # define columns type
    float_cols = ['lng', 'lat']
    for col in float_cols:
        data[col] = data[col].astype(float)
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(data, data["lng"], data["lat"], from_crs=FROM_CRS)
        # select columns
    market_ready_data = gdata[
        [
            'data_time',
            'name',
            'address',
            'description',
            'district',
            'lng',
            'lat', 
            'disabled_parking_car_count',
            'disabled_parking_motorcycle_count',
            'accessible_elevator_flag',
            'accessible_restroom_flag',
            'accessible_stair_handrail_flag',
            'wkb_geometry'
        ]
    ]

    # 停車場無障礙設施
    RID = "936e3be6-e029-4bdf-9199-a8b8fb482df6"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Point"
    # Extract
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            '停車場名稱': "name",
            '地址': "address",
            '無障礙設施內容': "description",
            '行政區': "district",
            'tmpx': "lng",
            'tmpy': "lat",
            '身心障礙汽車格位統計數值':'disabled_parking_car_count',
            '身心障礙機車格位統計數值':'disabled_parking_motorcycle_count',
            '無障礙電梯':'accessible_elevator_flag',
            '無障礙廁所':'accessible_restroom_flag',
            '無障礙樓梯扶手':'accessible_stair_handrail_flag',
            
        }
    )
    data['accessible_elevator_flag'] = data['accessible_elevator_flag'].map(lambda x: True if x == 'v' else False)
    data['accessible_restroom_flag'] = data['accessible_restroom_flag'].map(lambda x: True if x == 'v' else False)
    data['accessible_stair_handrail_flag'] = data['accessible_stair_handrail_flag'].map(lambda x: True if x == 'v' else False)

    # define columns type
    float_cols = ['lng', 'lat']
    for col in float_cols:
        data[col] = data[col].astype(float)
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(data, data["lng"], data["lat"], from_crs=FROM_CRS)
        # select columns
    park_ready_data = gdata[
        [
            'data_time',
            'name',
            'address',
            'description',
            'district',
            'lng',
            'lat', 
            'disabled_parking_car_count',
            'disabled_parking_motorcycle_count',
            'accessible_elevator_flag',
            'accessible_restroom_flag',
            'accessible_stair_handrail_flag',
            'wkb_geometry'
        ]
    ]

    ready_data = pd.concat([market_ready_data, park_ready_data], ignore_index=True)

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)



dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="accessible_facilities")
dag.create_dag(etl_func=_transfer)
