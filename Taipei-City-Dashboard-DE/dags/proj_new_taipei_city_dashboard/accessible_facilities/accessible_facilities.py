from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd
import re

def parse_charged(val, prefix):
    if pd.isna(val):
        return 0
    match = re.search(rf'{prefix}(\d+)', val)
    return int(match.group(1)) if match else 0



# pending 資料來源不全
def _transfer(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID= "1e548c60-0b04-4507-bf60-f3be651db642"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data.copy()
    data = data.rename(
        columns={
            "areacode": "district",
            "quantity": "name",
        }
    )
    data['type'] = 'parking'
    data['disabled_parking_car_count'] = data['charged'].apply(lambda x: parse_charged(x, '身汽'))
    data['disabled_parking_motorcycle_count'] = data['charged'].apply(lambda x: parse_charged(x, '身機'))
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
    data = data[[
        "name", "district", "type", "address", "disabled_parking_car_count", "disabled_parking_motorcycle_count", 'data_time']]

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="accessible_facilities")
dag.create_dag(etl_func=_transfer)
