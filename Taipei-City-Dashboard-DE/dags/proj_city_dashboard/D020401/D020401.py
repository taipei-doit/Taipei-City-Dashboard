from airflow import DAG
from operators.common_pipeline import CommonDag


def _D020401(**kwargs):
    import pandas as pd
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
    RID = "a87b93bd-ff23-4483-a792-feeff423e831"
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
            '專案名稱': "project_name",
            '災情發生時間': "occurred_time",
            '主災情類型名稱': "main_type",
            '災情細項': "sub_type",
            '災情行政區': "dist",
            '災情通報單位': "report_unit",
            '經度': "lng",
            '緯度': "lat",
            "data_time": "data_time",
        }
    )
    # define columns type
    float_cols = ['lng', 'lat']
    for col in float_cols:
        data[col] = data[col].astype(float)
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["occurred_time"] = convert_str_to_time_format(data["occurred_time"])
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(data, data["lng"], data["lat"], from_crs=FROM_CRS)
        # select columns
    ready_data = gdata[
        [
            'data_time',
            'occurred_time',
            'project_name',
            'main_type',
            'sub_type',
            'report_unit',
            'dist',
            'lng',
            'lat', 
            'wkb_geometry'
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
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D020401")
dag.create_dag(etl_func=_D020401)
