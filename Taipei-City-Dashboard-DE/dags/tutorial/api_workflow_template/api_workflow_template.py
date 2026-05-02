from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    """
    Template ETL function for a public API workflow.

    Replace the source URL and the field mapping with the real dataset rules.
    """
    import pandas as pd
    import requests
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    source_url = "https://example.gov.tw/api/v1/public-data"
    response = requests.get(source_url, timeout=60, proxies=proxies)
    response.raise_for_status()
    payload = response.json()

    records = payload.get("result", payload)
    if isinstance(records, dict):
        records = records.get("results", records.get("data", []))

    raw_data = pd.DataFrame(records)
    if raw_data.empty:
        raise ValueError("Source API returned no records.")

    data = raw_data.copy()
    rename_map = {
        "source_time": "data_time",
        "source_name": "name",
    }
    data = data.rename(columns=rename_map)

    if "data_time" in data.columns:
        data["data_time"] = convert_str_to_time_format(data["data_time"])
    elif isinstance(payload, dict) and payload.get("updated_at"):
        data["data_time"] = convert_str_to_time_format(payload["updated_at"])

    ready_data = data
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

    lasttime_in_data = None
    if "data_time" in ready_data.columns and ready_data["data_time"].notna().any():
        lasttime_in_data = ready_data["data_time"].max()

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=lasttime_in_data,
    )


dag = CommonDag(proj_folder="tutorial", dag_folder="api_workflow_template")
dag.create_dag(etl_func=etl_function)