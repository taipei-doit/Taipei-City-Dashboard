from airflow import DAG
from operators.common_pipeline import CommonDag


def D100103(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_file_last_modified_time,
        get_data_taipei_api,
    )
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    RID = "f5e1b147-3927-40ba-9fbc-64c36022c1e7"
    PAGE_ID = "48eb75e3-8694-433d-87cd-01b08668bcc7"

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)

    # Transform
    # Rename
    data = raw_data
    data = data.drop(columns=["_id", "_importdate"])
    data["年別"] = data["年別"].apply(lambda x: x.replace("年", ""))
    data["年別"] = data["年別"].apply(lambda x: int(x) + 1911)
    data["年別"] = pd.to_datetime(data["年別"], format="%Y").dt.year
    name_dict = {
        "年別": "year",
        "性別": "category",
        "就業保險育嬰留職停薪津貼初次核付人數[人]": "parental_leave_count",
    }
    data = data.rename(columns=name_dict)
    data["year"] = data["year"].astype(int)
    data["parental_leave_count"] = data["parental_leave_count"].astype(int)
    # Time
    data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Reshape
    ready_data = data.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=None,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100103")
dag.create_dag(etl_func=D100103)
