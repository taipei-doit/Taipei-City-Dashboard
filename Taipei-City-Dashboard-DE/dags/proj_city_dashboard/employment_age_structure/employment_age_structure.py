from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_api,
    )
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
    RID= "71185df2-d7a2-48f2-9bb5-192b59737610"
    # Load
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data.copy()
    data = data.drop(columns=["_id", "_importdate"])

    data = data.rename(
        columns={
                    "年平均別": "year",
                    "性別": "gender",
                    "年齡結構": "age_structure",
                    # "實數[千人]": "actual_number_thousand",
                    "百分比[％]": "percentage",
        }
    )
    data['percentage'] = data['percentage'].replace('-', None).astype(float)      
 
    data['year'] = data['year'].replace('年', '', regex=True)
    data['year'] = data['year'].astype(int) + 1911
    data = data[["year","gender","age_structure","percentage","data_time"]]
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="employment_age_structure")
dag.create_dag(etl_func=_transfer)
