from airflow import DAG
from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    """
    Implement the ETL function and add it to the DAG.
    There are some step or process is not necessary for common ETL, but necessary for City Dashboard,
        such as `wkb_geometry`, `dataset_info` and `lasttime_in_data` parts.
    A recommended ETL function should **at last** include the following steps:
    1. **Extract raw data from source**
        Should only extracts source data, and keeps it as raw as possible.
        _Some useful functions can be found in `utils/extract_stage.py`._
    2. **Transform raw data to ready data**
        All the data cleansing, data transformation, feature engineering should be done in this function.
        _Some useful functions can be found in `utils/transform_.*.py`._
    3. **Load ready data to PostgreSQL**
        _Some useful functions can be found in `utils/load_stage.py`._
    4. **Update lasttime_in_data to dataset_info table**
        Persist the lasttime_in_data for City Dashboard to use.
        _Some useful functions can be found in `utils/load_stage.py`._
    """
    from utils.extract_stage import get_data_taipei_api
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from sqlalchemy import create_engine

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
    RID = "04a3d195-ee97-467a-b066-e471ff99d15d"
    PAGE_ID = "ffdd5753-30db-4c38-b65f-b77892773d60"
    FROM_CRS = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    # Highly recommend to add `data_time` column to the dataframe for future long term data 
    # tracking and identifying the time of the data content.
    # If there is no time information in the raw data, you can use the last modified time of the data source.
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    # Rename
    data = raw_data
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "機構名稱": "name",
            "地址": "addr",
            "經度": "lng",
            "緯度": "lat",
            "data_time": "data_time",
        }
    )
    # Time
    # Ready data with time information should always add time zone.
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Geometry
    # TUIC use wkb_geometry format to store geometry data, and use `wkb_geometry` as the column name.
    # Ready data always in crs 4326 (WGS84) coordinate system.
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    gdata = gdata.drop(columns=["geometry", "_id"])
    ready_data = gdata[["data_time", "name", "addr", "lng", "lat", "wkb_geometry"]]

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


dag = CommonDag(proj_folder="tutorial", dag_folder="simple_template")
dag.create_dag(etl_func=etl_function)
