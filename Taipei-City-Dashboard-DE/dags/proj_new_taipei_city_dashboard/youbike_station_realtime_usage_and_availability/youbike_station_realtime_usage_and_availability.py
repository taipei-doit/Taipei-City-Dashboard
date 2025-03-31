from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_tdx_data
    import pandas as pd
    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    proxies = kwargs.get("proxies")
    url = '''https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/NewTaipei?%24&%24format=JSON'''
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326
    raw_data = get_tdx_data(url, output_format='dataframe')

    print(f"raw data =========== {raw_data.columns}")

    # Transform
    data = raw_data.copy()
    data = pd.concat([data.drop(['StationName', 'StationPosition'], axis=1), 
                    data['StationName'].apply(pd.Series), 
                    data['StationPosition'].apply(pd.Series)], axis=1)

    # Rename the columns for clarity (不要同時使用 inplace 與賦值)
    data.rename(columns={"StationID": "sno", "Zh_tw": "sna", "SrcUpdateTime": "data_time",
                        "PositionLon": "longitude", "PositionLat": "latitude"}, inplace=True)

# 如果你想重新設定 DataFrame 的欄位順序，可以使用以下方式，而不是覆蓋整個 data：
    data = data[["sno", "sna", "data_time", "longitude", "latitude"]]
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )

    ready_data = gdata[["sno", "sna", "data_time", "wkb_geometry"]]
    print(f"ready_data =========== {ready_data.head()}")

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
    engine = create_engine(ready_data_db_uri)
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="youbike_station_realtime_usage_and_availability")
dag.create_dag(etl_func=_transfer)
