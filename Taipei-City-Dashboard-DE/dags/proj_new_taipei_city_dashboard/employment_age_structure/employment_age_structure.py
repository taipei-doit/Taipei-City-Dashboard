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
    RID= "c285509a-7fb2-434f-8542-0b4986c337a8"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data.copy()
    data = data.rename(
        columns={
            "field1": "year",
            "percent2": "15-24_male",
            "percent3": "15-24_female",
            "percent4": "25-29_male",
            "percent5": "25-29_female",
            "percent6": "30-34_male",
            "percent7": "30-34_female",
            "percent8": "35-39_male",
            "percent9": "35-39_female",
            "percent10": "40-44_male",
            "percent11": "40-44_female",
            "percent12": "45-49_male",
            "percent13": "45-49_female",
            "percent14": "50-54_male",
            "percent15": "50-54_female",
            "percent16": "55-59_male",
            "percent17": "55-59_female",
            "percent18": "60-64_male",
            "percent19": "60-64_female",
            "percent20": "65_above_male",
            "percent21": "65_above_female",
        }
    )

    # 將百分比欄位轉換為浮點數
    percent_cols = [c for c in data.columns if c != "year"]
    data[percent_cols] = data[percent_cols].apply(pd.to_numeric, errors="coerce")

    # 定義年齡組對應 (male_col, female_col, age_label)
    age_groups = [
        ("15-24_male", "15-24_female", "就業人口按年齡別/15-24歲"),
        ("25-29_male", "25-29_female", "就業人口按年齡別/25-29歲"),
        ("30-34_male", "30-34_female", "就業人口按年齡別/30-34歲"),
        ("35-39_male", "35-39_female", "就業人口按年齡別/35-39歲"),
        ("40-44_male", "40-44_female", "就業人口按年齡別/40-44歲"),
        ("45-49_male", "45-49_female", "就業人口按年齡別/45-49歲"),
        ("50-54_male", "50-54_female", "就業人口按年齡別/50-54歲"),
        ("55-59_male", "55-59_female", "就業人口按年齡別/55-59歲"),
        ("60-64_male", "60-64_female", "就業人口按年齡別/60-64歲"),
        ("65_above_male", "65_above_female", "就業人口按年齡別/65歲以上"),
    ]

    # 建構男、女、總計的資料列
    rows = []
    for _, row in data.iterrows():
        year = row["year"]
        for male_col, female_col, age_label in age_groups:
            male_val = row[male_col]
            female_val = row[female_col]
            total_val = round(male_val + female_val, 2)
            rows.append({"year": year, "gender": "男", "age_structure": age_label, "percentage": male_val})
            rows.append({"year": year, "gender": "女", "age_structure": age_label, "percentage": female_val})
            rows.append({"year": year, "gender": "總計", "age_structure": age_label, "percentage": total_val})

    melted_data = pd.DataFrame(rows)
    melted_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    print(f"ready_data =========== {melted_data.head(10)}")

    
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=melted_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, melted_data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="employment_age_structure")
dag.create_dag(etl_func=_transfer)
