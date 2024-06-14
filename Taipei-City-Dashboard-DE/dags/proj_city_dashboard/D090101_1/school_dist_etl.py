from airflow import DAG


def school_dist_etl(rid, col_map, **kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    raw_data = get_data_taipei_api(rid, output_format="dataframe")

    # Transform
    data = raw_data.copy()
    # colname
    data.columns = data.columns.str.lower()

    data = data.rename(columns=col_map)
    # define column type
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # select column
    ready_data = data[
        [
            "data_time",
            "name",
            "addr",
            "dist",
            "dist_of_school_dist",
            "school_district",
            "phone",
        ]
    ]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)
