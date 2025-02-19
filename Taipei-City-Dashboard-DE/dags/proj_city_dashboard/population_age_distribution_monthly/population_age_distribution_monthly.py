from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    import requests
    from io import StringIO
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=8907&kind=21&type=0&funid=a04000401&cycle=1&outmode=12&compmode=0&outkind=3&deflst=2&nzo=1"

    response = requests.get(URL, verify=False)
    # 讀取 CSV
    raw_data = pd.read_csv(StringIO(response.text))
    print(f"raw data =========== {raw_data.head()}")
    # Transform
    data = raw_data.copy()
    # ** 只篩選 "12月底"**
    data = data[data["統計期"].str.contains("12月底")].copy()
    # ** 轉換 "89年" → "2000"（民國轉西元）**
    data["year"] = data["統計期"].str.extract(r"(\d+)").astype(int) + 1911
    # ** 移除原始 `統計期` 欄位**
    data = data.drop(columns=["統計期"])
    # ** 重新排列欄位**
    data = data[["year"] + [col for col in data.columns if col != "year"]]

    # rename
    data = data.rename(
        columns={
            "幼年人口數[0~14歲][人]": "young_population",  # 0-14歲人口數
            "幼年人口占全市人口比率[%]": "young_population_percentage",  # 0-14歲占全市人口比率
            "青壯年人口數[15~64歲][人]": "working_age_population",  # 15-64歲人口數
            "青壯年人口占全市人口比率[%]": "working_age_population_percentage",  # 15-64歲占全市人口比率
            "老年人口數[65歲以上][人]": "elderly_population",  # 65歲以上人口數
            "老年人口占全市人口比率[%]": "elderly_population_percentage",  # 65歲以上占全市人口比率
            "扶養比[%]": "total_dependency_ratio",  # 扶養比（％）
            "老化指數[%]": "aging_index",  # 老化指數（％）
        }
    )
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Load
    
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="population_age_distribution_monthly")
dag.create_dag(etl_func=_transfer)
