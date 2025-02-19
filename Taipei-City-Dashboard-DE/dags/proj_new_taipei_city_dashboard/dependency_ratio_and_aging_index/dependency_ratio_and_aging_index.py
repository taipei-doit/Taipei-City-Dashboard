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
    from utils.transform_time import convert_str_to_time_format
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
    # ** 只保留 "新北市- 計" 的資料**
    data = data[data["field1"].str.contains("新北市- 計")].copy()

    # ** 提取年份數字 (民國/西元 皆適用)**
    data["end_of_year"] = data["field1"].str.extract(r"(\d{4})").astype(int)
    data = data.rename(
        columns={
            "percent24": "young_population",  # 0-14歲人口數
            "percent25": "young_population_percentage",  # 0-14歲占全市人口比率
            "percent26": "working_age_population",  # 15-64歲人口數
            "percent27": "working_age_population_percentage",  # 15-64歲占全市人口比率
            "percent28": "elderly_population",  # 65歲以上人口數
            "percent29": "elderly_population_percentage",  # 65歲以上占全市人口比率
            "percent30": "elderly_dependency_ratio",  # 扶老比（％）
            "percent31": "youth_dependency_ratio",  # 扶幼比（％）
            "percent32": "total_dependency_ratio",  # 扶養比（％）
            "percent33": "aging_index",  # 老化指數（％）
        }
    )
    data = data.drop(columns=["field1"])
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # ** 重新排列欄位順序**
    data = data[
        [
            "end_of_year", "young_population", "young_population_percentage",
            "working_age_population", "working_age_population_percentage",
            "elderly_population", "elderly_population_percentage",
            "elderly_dependency_ratio", "youth_dependency_ratio",
            "total_dependency_ratio", "aging_index", "data_time"
        ]
    ]
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

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="dependency_ratio_and_aging_index")
dag.create_dag(etl_func=_transfer)
