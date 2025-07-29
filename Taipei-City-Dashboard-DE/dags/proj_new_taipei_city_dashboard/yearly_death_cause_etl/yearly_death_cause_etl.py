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
    # 死亡率
    RATE_RID= "5e6a672a-09e6-4119-8de6-0ca9856f3a01"
    client = NewTaipeiAPIClient(RATE_RID, input_format="json")
    res = client.get_all_data(size=1000)
    rate_df = pd.DataFrame(res)
    # 死亡人數
    DEATH_RID= "e490f906-93f0-4fc3-b5b3-fe34fb31d1db"
    client = NewTaipeiAPIClient(DEATH_RID, input_format="json")
    res = client.get_all_data(size=1000)
    death_df = pd.DataFrame(res)

    cause_map = {
        "癌症":        ("itemvalue4", "itemvalue5", "item value4", "item value5"),
        "心臟疾病":    ("itemvalue6", "itemvalue7", "item value6", "item value7"),
        "腦血管疾病":  ("itemvalue8", "itemvalue9", "item value8", "item value9"),
        "糖尿病":      ("itemvalue10", "itemvalue11", "item value10", "item value11"),
        "肺炎":        ("itemvalue12", "itemvalue13", "item value12", "item value13"),
        "腎炎_腎徵候群及腎性病變": ("itemvalue14", "itemvalue15", "item value14", "item value15"),
        "自殺":        ("itemvalue16", "itemvalue17", "item value16", "item value17"),
        "事故傷害":    ("itemvalue18", "itemvalue19", "item value18", "item value19"),
    }

    rows = []
    for idx, row in death_df.iterrows():
        year = row["field1"]
        rate_row = rate_df[rate_df["field1"] == year].iloc[0]
        for cause, (death_male_col, death_female_col, rate_male_col, rate_female_col) in cause_map.items():
            death_count = row[death_male_col] + row[death_female_col]
            mortality_rate = float(rate_row[rate_male_col]) + float(rate_row[rate_female_col])
            rows.append({
                "year": int(year),
                "death_cause": cause,
                "death_count": int(death_count),
                "mortality_rate": round(mortality_rate, 2)
            })

    result_df = pd.DataFrame(rows)
    result_df['data_time'] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=result_df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, result_df["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="yearly_death_cause_etl")
dag.create_dag(etl_func=_transfer)
