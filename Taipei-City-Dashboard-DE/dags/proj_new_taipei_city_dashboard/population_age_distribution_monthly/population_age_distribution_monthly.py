from airflow import DAG
from operators.common_pipeline import CommonDag


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
    RID= "8308ab58-62d1-424e-8314-24b65b7ab492"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    
    raw_data = pd.DataFrame(res)

    print(f"raw data =========== {raw_data.head()}")

    data = raw_data.copy()

    data = data[data["field1"].str.contains("新北市- 計")].copy()

    # ** 提取年份數字 (民國/西元 皆適用)**
    data["year"] = data["field1"].str.extract(r"(\d{4})").astype(int)
    data = data.rename(columns={
        'percent24': 'young_population',
        'percent25': 'young_population_percentage',
        'percent26': 'working_age_population',
        'percent27': 'working_age_population_percentage',
        'percent28': 'elderly_population',
        'percent29': 'elderly_population_percentage',
        'percent32': 'total_dependency_ratio',
        'percent33': 'aging_index'
    })
# 選取需要的欄位
    data = data[[
        'year', 'young_population', 'young_population_percentage',
        'working_age_population', 'working_age_population_percentage',
        'elderly_population', 'elderly_population_percentage',
        'total_dependency_ratio', 'aging_index'
    ]]

    # 重新排列欄位順序
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    print(f"ready_data =========== {data.head()}")

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

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="population_age_distribution_monthly")
dag.create_dag(etl_func=_transfer)
