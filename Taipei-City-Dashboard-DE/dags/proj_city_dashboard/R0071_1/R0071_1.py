from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0071_1(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_folder = kwargs.get("data_folder")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Transactions across Taipei and New Taipei are frequently, so download both.
    TPE_URL = "https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/Taipei?%24format=JSON"
    NTPE_URL = "https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/NewTaipei?%24format=JSON"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    # taipei
    raw_tpe_data = get_tdx_data(TPE_URL, output_format='dataframe')
    raw_tpe_data["county"] = "Taipei"
    # new taipei
    raw_ntpe_data = get_tdx_data(NTPE_URL, output_format='dataframe')
    raw_ntpe_data["county"] = "New Taipei"
    # merge
    raw_data = pd.concat([raw_tpe_data, raw_ntpe_data])

    # Transform
    data = raw_data.copy()
    # rename
    col_map = {
        "StationUID": "station_uid",  # 唯一識別代碼，規則為 {業管機關代碼} + {StationID}
        "StationID": "station_id",
        "AuthorityID": "authority_id",
        "StationName": "name",
        "StationPosition": "pos",
        "StationAddress": "addr",
        "BikesCapacity": "bike_capacity",  # 可容納之自行車總數
        "ServiceType": "service_type",  # [1:'YouBike1.0',2:'YouBike2.0',3:'T-Bike',4:'P-Bike',5:'K-Bike']
        "SrcUpdateTime": "data_time",  # 來源端平台資料更新時間
        "UpdateTime": "tdx_update_time",  # TDX資料更新日期時間
        "county": "county",  # 縣市
    }
    data = data.rename(columns=col_map)
    # extract nested json
    data["name"] = data["name"].apply(lambda x: x["Zh_tw"])
    data["name"] = data["name"].str.replace("YouBike2.0_", "")
    data["addr"] = data["addr"].apply(lambda x: x["Zh_tw"])
    data["lng"] = data["pos"].apply(lambda x: x["PositionLon"])
    data["lat"] = data["pos"].apply(lambda x: x["PositionLat"])
    data = data.drop(columns=["pos"])
    # define column type
    data["station_id"] = data["station_id"].astype(str)
    data["bike_capacity"] = pd.to_numeric(data["bike_capacity"], errors="coerce")
    # numbers can't be converted to int will be set to -1
    data["bike_capacity"] = data["bike_capacity"].fillna(-1).astype(int)
    # mapping category code to category name
    data["service_type"] = data["service_type"].astype(str)
    type_map = {
        "1": "UBike1.0",
        "2": "UBike2.0",
        "3": "TBike",
        "4": "PBike",
        "5": "KBike",
    }
    data["service_type"] = data["service_type"].map(type_map)
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["tdx_update_time"] = convert_str_to_time_format(data["tdx_update_time"])
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS, is_add_xy_columns=False
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "county",
            "station_uid",
            "station_id",
            "authority_id",
            "name",
            "service_type",
            "bike_capacity",
            "addr",
            "lng",
            "lat",
            "wkb_geometry",
            "tdx_update_time",
        ]
    ]

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
    # Update lasttime_in_data
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0071_1")
dag.create_dag(etl_func=_R0071_1)
