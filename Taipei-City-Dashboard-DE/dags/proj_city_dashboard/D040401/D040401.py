from airflow import DAG
from operators.common_pipeline import CommonDag


def D040401(**kwargs):
    """
    Routes and locations of garbage trucks from data.taipei.

    Explanation:
    -------------
    unmatched_list: There are 10 hospitals in the raw data that cannot be found in the existing
        hospital and clinic list, therefore the list was created to record the situation.
        Therefore, we manually add the address for these hospitals.
    """
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_api,
        get_data_taipei_file_last_modified_time,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_path = kwargs.get("data_path")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Manually set
    RID = "a6e90031-7ec4-4089-afb5-361a4efe7202"
    PAGE_ID = "6bb3304b-4f46-4bb0-8cd1-60c66dcd1cae"
    FROM_CRS = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    # Rename
    data = raw_data.copy()
    name_dict = {
        "行政區": "district",
        "里別": "village",
        "分隊": "division",
        "局編": "office_code",
        "車號": "car_number",
        "路線": "route",
        "車次": "car_times",
        "抵達時間": "arrival_time",
        "離開時間": "departure_time",
        "地點": "location",
        "經度": "lng",
        "緯度": "lat",
    }
    data = data.rename(columns=name_dict)
    # Time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    gdata = gdata.drop(columns=["geometry", "_id", "_importdate"])
    ready_data = gdata.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D040401")
dag.create_dag(etl_func=D040401)
