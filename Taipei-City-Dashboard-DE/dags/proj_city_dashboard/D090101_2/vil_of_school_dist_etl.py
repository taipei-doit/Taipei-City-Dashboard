from airflow import DAG


def vil_of_school_dist_etl(rid, school_dist_col, **kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
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

    # Extract
    raw_data = get_data_taipei_api(rid, output_format="dataframe")

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "行政區": "dist",
            "里": "vill",
            "鄰": "neighborhood",
            school_dist_col: "school_district",
        }
    )
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # repair data error
    # 洲美里 did not have dist
    is_target_vil = data["vill"] == "洲美"
    data.loc[is_target_vil, "dist"] = "北投區"
    # dist in New Taipei City add city name in front of dist
    is_ntpe = data["dist"].str.contains("(汐止)|(淡水)")
    data.loc[is_ntpe, "dist"] = "新北市" + data.loc[is_ntpe, "dist"].str.slice(-3)
    # Add village
    is_need_vil = ~(data["vill"].str.endswith("里"))
    data.loc[is_need_vil & ~is_ntpe, "vill"] = (
        data.loc[is_need_vil & ~is_ntpe, "vill"] + "里"
    )
    # select column
    ready_data = data[["data_time", "dist", "vill", "neighborhood", "school_district"]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)
