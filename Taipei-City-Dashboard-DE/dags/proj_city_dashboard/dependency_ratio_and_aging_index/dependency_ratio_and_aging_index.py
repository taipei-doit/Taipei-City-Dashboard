from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_api,
        get_data_taipei_file_last_modified_time,
    )
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID= "6701c78f-c781-426c-98b7-182827d93384"
    # Load
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data.copy()
    data = data.drop(columns=["_id", "_importdate"])
    
    data = data.rename(
        columns={
            "年底別": "end_of_year",
            "幼年人口數[人]": "young_population",
            "幼年人口占全市人口比率[％]": "young_population_percentage",
            "青壯年人口數[人]": "working_age_population",
            "青壯年人口占全市人口比率[％]": "working_age_population_percentage",
            "老年人口數[人]": "elderly_population",
            "老年人口占全市人口比率[％]": "elderly_population_percentage",
            "扶老比[％]": "elderly_dependency_ratio",
            "扶幼比[％]": "youth_dependency_ratio",
            "扶養比[％]": "total_dependency_ratio",
            "老化指數[％]": "aging_index",
        }
    )
    data['end_of_year'] = data['end_of_year'].replace('年', '', regex=True)
    data['end_of_year'] = data['end_of_year'].astype(int) + 1911
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

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="dependency_ratio_and_aging_index")
dag.create_dag(etl_func=_transfer)
