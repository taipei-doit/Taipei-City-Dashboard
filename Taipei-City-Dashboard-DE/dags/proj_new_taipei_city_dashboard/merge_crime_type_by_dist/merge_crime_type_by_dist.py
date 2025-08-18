from airflow import DAG
from operators.common_pipeline import CommonDag


def rocdate_to_ad(date_str):
    # 取前三位是民國年，後面是MMDD
    year = int(date_str[:3]) + 1911
    month = int(date_str[3:5])
    day = int(date_str[5:7])
    return f"{year:04d}-{month:02d}-{day:02d}"


# 定義 Airflow DAG 要執行的 ETL 任務函式
def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID= "8a32c6b5-46fc-4fac-b3a4-317b9998bfd7"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    raw_data["date"] = raw_data["date"].astype(str).apply(rocdate_to_ad)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    raw_data['dist'] = raw_data['location'].str.extract(r'(.{2,3}區)')
    raw_data = raw_data[["type","date","dist","location","data_time"]]
    # 建立資料庫連線
    engine = create_engine(ready_data_db_uri)

    save_dataframe_to_postgresql(
        engine,
        data=raw_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    lasttime_in_data = raw_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

# 建立 DAG 物件，指定專案與 DAG 所在目錄
dag = CommonDag(
    proj_folder='proj_new_taipei_city_dashboard',
    dag_folder='merge_crime_type_by_dist'
)

# 將 _transfer 函式掛載為 DAG 的主要 ETL 任務
dag.create_dag(etl_func=_transfer)
