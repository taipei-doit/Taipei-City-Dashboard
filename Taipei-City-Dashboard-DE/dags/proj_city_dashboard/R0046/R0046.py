from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0046(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_json_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tcgmetro.blob.core.windows.net/stationnames/stations.json"
    file_name = f"{dag_id}.json"

    # Extract
    raw_data = get_json_file(file_name, URL, is_proxy=True, output_format="dataframe")

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "Station": "station",
            "Destination": "destination",
            "UpdateTime": "updatetime",
        }
    )
    # define column type
    data["updatetime"] = convert_str_to_time_format(
        data["updatetime"], from_format="%Y%m%d%H%M%S"
    )
    # select columns
    ready_data = data[["station", "destination", "updatetime"]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    lasttime_in_data = data["updatetime"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0046")
dag.create_dag(etl_func=_R0046)
