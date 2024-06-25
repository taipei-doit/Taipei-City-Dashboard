from airflow import DAG
from operators.common_pipeline import CommonDag


def _D060102_1(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "438c61ad-24f6-4e54-a1cc-e2cfe0e7051e"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = get_data_taipei_api(RID, output_format="dataframe")

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "場所名稱": "name",
            "場所地址": "addr",
            "區域代碼": "vil_code",
            "場所分類": "main_type",
            "場所類型": "sub_type",
            "aed放置地點": "aed_place",
            "經度": "lng",
            "緯度": "lat",
            "data_time": "data_time",
        }
    )
    # define column type
    data["vil_code"] = data["vil_code"].astype(float).astype(int).astype(str)
    
    # add column
    data["city"] = "台北市"
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "city",
            "vil_code",
            "name",
            "addr",
            "main_type",
            "sub_type",
            "aed_place",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

    # Load
    # Load data to DB
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
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D060102_1")
dag.create_dag(etl_func=_D060102_1)
